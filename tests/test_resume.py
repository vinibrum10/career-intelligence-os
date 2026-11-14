import json
import unittest
from copy import deepcopy
from unittest.mock import patch
from uuid import uuid4

from pydantic import ValidationError

from app.ollama_cloud import OllamaCloudError
from app.profiles.resume import router, validate_content
from tests import test_profiles as profile_tests


FACTS = {'experience': 'Deu suporte a 2 aplicações fictícias.', 'skills': 'Aplicou Python em um projeto fictício.'}


def content():
    return {
        'summary': {'text': 'Profissional com atuação no suporte a 2 aplicações fictícias.', 'sources': ['experience']},
        'sections': [{'topic': key, 'text': value, 'sources': [key]} for key, value in FACTS.items()],
    }


class ResumeValidationTest(unittest.TestCase):
    def test_valid_content_and_single_json_fence(self):
        raw = json.dumps(content())
        self.assertEqual(validate_content(raw, FACTS).sections[0].sources, ['experience'])
        self.assertEqual(validate_content('```json\n' + raw + '\n```', FACTS).summary.text, content()['summary']['text'])

    def test_unknown_sources_omissions_duplicates_and_unsupported_numbers_fail(self):
        invalid = []
        item = content(); item['summary']['sources'] = ['projects']; invalid.append(item)
        item = content(); item['sections'].pop(); invalid.append(item)
        item = content(); item['sections'][1] = deepcopy(item['sections'][0]); invalid.append(item)
        item = content(); item['sections'][1]['sources'] = ['experience']; invalid.append(item)
        item = content(); item['summary']['text'] = 'Tem 10 anos de experiência.'; invalid.append(item)
        item = content(); item['sections'][1]['text'] = 'Utilizou Python por 2 anos.'; invalid.append(item)
        item = content(); item['summary']['sources'] = ['experience', 'experience']; invalid.append(item)
        item = content(); item['name'] = 'Invented name'; invalid.append(item)
        item = content(); item['summary']['text'] = ' '; invalid.append(item)
        for item in invalid:
            with self.subTest(item=item), self.assertRaises((ValueError, ValidationError)):
                validate_content(json.dumps(item), FACTS)
        for raw in ['not JSON', '[]', 'null', 'x' * 60001]:
            with self.subTest(raw=raw[:30]), self.assertRaises((ValueError, ValidationError)):
                validate_content(raw, FACTS)


class ResumeEndpointTest(unittest.TestCase):
    owner = profile_tests.ProfilesTest.owner

    @classmethod
    def setUpClass(cls):
        profile_tests.ProfilesTest.setUpClass.__func__(cls)
        cls.app.include_router(router)

    @classmethod
    def tearDownClass(cls):
        profile_tests.ProfilesTest.tearDownClass.__func__(cls)

    def interview(self):
        owner = self.owner()
        interview = str(uuid4())
        payload = {'answers': {
            'experience': 'RAW RESPONSE NOT TO BE SENT. Deu suporte a 2 aplicações fictícias.',
            'projects': 'EXCLUDED RESPONSE NOT TO BE SENT.',
            'skills': FACTS['skills'],
        }, 'facts': FACTS}
        path = f'/career/owners/{owner}/interviews/{interview}'
        response = self.client.put(path, json=payload)
        self.assertEqual(response.status_code, 201)
        return owner, interview, path, response.json()

    @patch('app.profiles.resume.chat')
    def test_only_confirmed_facts_are_sent_and_profile_is_unchanged(self, cloud):
        owner, interview, path, before = self.interview()
        cloud.return_value = json.dumps(content())
        response = self.client.post(path + '/resume-draft', json={'consent': True})
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result['interview_id'], interview)
        self.assertEqual(result['facts'], FACTS)
        self.assertEqual(result['missing_topics'], ['projects', 'results'])
        messages = cloud.call_args.args[0]
        self.assertEqual(json.loads(messages[1]['content']), {'facts': FACTS})
        self.assertNotIn('RAW RESPONSE', str(messages))
        self.assertNotIn('EXCLUDED RESPONSE', str(messages))
        self.assertNotIn(owner, str(messages))
        self.assertNotIn(interview, str(messages))
        self.assertEqual(self.client.get(path).json(), before)
        self.assertEqual(len(self.client.get(path.rsplit('/', 1)[0]).json()), 1)

    @patch('app.profiles.resume.chat')
    def test_consent_must_be_explicit_and_no_unknown_payload_is_accepted(self, cloud):
        _, _, path, _ = self.interview()
        for payload in [{}, {'consent': False}, {'consent': 1}, {'consent': 'true'}, {'consent': True, 'facts': FACTS}]:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post(path + '/resume-draft', json=payload).status_code, 422)
        cloud.assert_not_called()

    @patch('app.profiles.resume.chat')
    def test_missing_or_cross_owner_profile_never_calls_provider(self, cloud):
        _, interview, _, _ = self.interview()
        other = self.owner()
        for record in [interview, str(uuid4())]:
            response = self.client.post(f'/career/owners/{other}/interviews/{record}/resume-draft', json={'consent': True})
            self.assertEqual(response.status_code, 404)
        cloud.assert_not_called()

    @patch('app.profiles.resume.chat')
    def test_bad_responses_and_provider_failure_do_not_write_or_leak_content(self, cloud):
        _, _, path, before = self.interview()
        cloud.return_value = 'PRIVATE_INVALID_MODEL_RESPONSE'
        response = self.client.post(path + '/resume-draft', json={'consent': True})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn('PRIVATE_INVALID_MODEL_RESPONSE', response.text)
        cloud.side_effect = OllamaCloudError(429, 'Limite atingido. Aguarde antes de tentar novamente.')
        response = self.client.post(path + '/resume-draft', json={'consent': True})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(self.client.get(path).json(), before)
