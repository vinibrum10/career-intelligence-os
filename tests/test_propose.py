import io
import json
import unittest
from unittest.mock import patch
from urllib.error import URLError
from uuid import uuid4
from tests import test_profiles as fixtures
from tests.test_extractions import TEXT, at
from app.jobs import propose
from app.jobs.extractions import router as extractions_router
from app.jobs.router import router as jobs_router

def item(field_key, excerpt, value, requirement="required"):
    return {"field_key": field_key, "knowledge": "explicit", "requirement": requirement, "value": value, "excerpt": excerpt}

class Reply(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        self.close()

def reply(content):
    return Reply(json.dumps({"message": {"content": content}}).encode())

class BuildTest(unittest.TestCase):
    def test_every_bad_candidate_is_discarded_with_a_reason(self):
        built = propose.build(TEXT, [
            item("work_arrangement", "home office", "remote"),          # invented excerpt
            item("contract", "R$", "employee"),                         # appears twice
            item("contract", "CLT", "freelancer"),                      # value outside the vocabulary
            item("benefits", "CLT", "x"),                               # unknown field
            {"field_key": "contract", "knowledge": "inferred", "value": "employee", "excerpt": "CLT"},
            {"field_key": "contract", "knowledge": "explicit", "value": "employee"},  # no excerpt
            "not an object",
        ])
        self.assertEqual(built["claims"], [])
        reasons = [d["reason"] for d in built["discarded"]]
        self.assertEqual(len(reasons), 7)
        self.assertIn("Excerpt not found in the saved text", reasons)
        self.assertIn("Excerpt appears more than once", reasons)
        self.assertIn("Missing excerpt", reasons)
        self.assertIn("Item is not an object", reasons)

    def test_offsets_come_from_the_code_not_from_the_model(self):
        built = propose.build(TEXT, [dict(item("working_time", "Salary up to USD 90k.", "full_time"), start_char=0, end_char=3)])
        evidence = built["claims"][0].evidence[0]
        self.assertEqual((evidence.start_char, evidence.end_char), (at("Salary up to USD 90k.")["start_char"], at("Salary up to USD 90k.")["end_char"]))
        self.assertEqual(TEXT[evidence.start_char:evidence.end_char], evidence.excerpt)

    def test_not_provided_is_kept_once_and_never_beside_an_explicit_claim(self):
        missing = {"field_key": "sponsorship", "knowledge": "not_provided"}
        built = propose.build(TEXT, [missing, missing, {"field_key": "contract", "knowledge": "not_provided"},
                                     item("contract", "CLT", "employee")])
        self.assertEqual([(c.field_key, c.knowledge) for c in built["claims"]], [("sponsorship", "not_provided"), ("contract", "explicit")])

class AskModelTest(unittest.TestCase):
    def test_sends_only_the_vacancy_to_the_configured_model(self):
        sent = {}
        def fake(request, timeout):
            sent.update(url=request.full_url, body=json.loads(request.data), timeout=timeout)
            return reply('{"claims": [{"field_key": "contract", "knowledge": "not_provided"}]}')
        with patch("urllib.request.urlopen", fake):
            claims = propose.ask_model(TEXT)
        self.assertEqual(claims, [{"field_key": "contract", "knowledge": "not_provided"}])
        self.assertEqual(sent["url"], "http://host.docker.internal:11434/api/chat")
        self.assertEqual(sent["body"]["model"], "qwen3:8b")
        self.assertFalse(sent["body"]["stream"])
        self.assertEqual(sent["body"]["options"]["temperature"], 0)
        self.assertEqual([m["role"] for m in sent["body"]["messages"]], ["system", "user"])
        self.assertIn(TEXT, sent["body"]["messages"][1]["content"])

    def test_unreachable_server_and_unusable_answers_become_502(self):
        for failure in (URLError("refused"), TimeoutError("slow")):
            with patch("urllib.request.urlopen", side_effect=failure):
                with self.assertRaises(propose.HTTPException) as caught:
                    propose.ask_model(TEXT)
                self.assertEqual(caught.exception.status_code, 502)
        for content in ("not json", '{"other": 1}', '{"claims": "x"}'):
            with patch("urllib.request.urlopen", return_value=reply(content)):
                with self.assertRaises(propose.HTTPException) as caught:
                    propose.ask_model(TEXT)
                self.assertEqual(caught.exception.status_code, 502)

class DraftEndpointTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.ProfilesTest.setUpClass.__func__(cls)
        cls.app.include_router(jobs_router)
        cls.app.include_router(extractions_router)
        cls.app.include_router(propose.router)
    @classmethod
    def tearDownClass(cls):
        fixtures.ProfilesTest.tearDownClass.__func__(cls)
    def setUp(self):
        self.owner = self.client.post("/career/owners", json={"label": "Synthetic draft owner"}).json()["id"]
        self.job = self.client.post(f"/career/owners/{self.owner}/jobs", json={"label": "Synthetic vacancy", "original_text": TEXT}).json()["id"]
        self.path = f"/career/owners/{self.owner}/jobs/{self.job}/snapshots/1/extractions"

    def test_draft_saves_nothing_and_the_reviewed_draft_can_be_saved(self):
        items = [item("work_arrangement", "remoto", "remote"), item("contract", "CLT", "employee", "informational"),
                 {"field_key": "sponsorship", "knowledge": "not_provided"}, item("contract", "freelance", "contractor")]
        with patch.object(propose, "ask_model", return_value=items):
            r = self.client.post(self.path + "/draft")
        self.assertEqual(r.status_code, 200, r.text)
        draft = r.json()
        self.assertEqual(draft["extractor"], "ollama-qwen3:8b+reviewed")
        self.assertEqual([c["field_key"] for c in draft["claims"]], ["work_arrangement", "contract", "sponsorship"])
        self.assertEqual(len(draft["discarded"]), 1)
        self.assertEqual(self.client.get(self.path).json(), [])  # nothing stored by the draft
        saved = self.client.post(self.path, json={"extractor": draft["extractor"], "claims": draft["claims"]})
        self.assertEqual(saved.status_code, 201, saved.text)
        self.assertEqual(saved.json()["claims"][0]["evidence"][0]["excerpt"], "remoto")
        self.assertEqual(len(self.client.get(self.path).json()), 1)

    def test_model_failure_is_502_and_stores_nothing(self):
        with patch("urllib.request.urlopen", side_effect=URLError("refused")):
            r = self.client.post(self.path + "/draft")
        self.assertEqual(r.status_code, 502)
        self.assertEqual(self.client.get(self.path).json(), [])

    def test_unknown_capture_other_owner_and_too_long_text(self):
        with patch.object(propose, "ask_model", side_effect=AssertionError("model must not be called")):
            other = self.client.post("/career/owners", json={"label": "Synthetic other owner"}).json()["id"]
            self.assertEqual(self.client.post(f"/career/owners/{other}/jobs/{self.job}/snapshots/1/extractions/draft").status_code, 404)
            self.assertEqual(self.client.post(f"/career/owners/{self.owner}/jobs/{uuid4()}/snapshots/1/extractions/draft").status_code, 404)
            self.assertEqual(self.client.post(f"/career/owners/{self.owner}/jobs/{self.job}/snapshots/2/extractions/draft").status_code, 404)
            long = self.client.post(f"/career/owners/{self.owner}/jobs", json={"label": "Long", "original_text": "x" * (propose.MAX_CHARS + 1)}).json()["id"]
            r = self.client.post(f"/career/owners/{self.owner}/jobs/{long}/snapshots/1/extractions/draft")
            self.assertEqual(r.status_code, 422)

if __name__ == "__main__":
    unittest.main()
