import json
import os
import unittest
from unittest.mock import patch

import httpx
from ollama import Client as SDKClient
from app import ollama_cloud


class CloudClientTest(unittest.TestCase):
    def transport_client(self, handler):
        return patch.object(ollama_cloud, "Client", side_effect=lambda **kwargs: SDKClient(**kwargs, transport=httpx.MockTransport(handler)))

    def test_exact_cloud_host_model_and_bearer_header(self):
        calls = []
        def handler(request):
            calls.append(request)
            self.assertEqual(str(request.url), "https://ollama.com/api/chat")
            self.assertEqual(request.headers['authorization'], 'Bearer synthetic-ollama-key')
            self.assertNotIn('x-api-key', request.headers)
            body = json.loads(request.content)
            self.assertEqual(body['model'], 'gemma4:31b')
            self.assertFalse(body['stream'])
            self.assertEqual(body['format'], 'json')
            self.assertEqual(body['messages'], [{'role':'user','content':'Synthetic message'}])
            return httpx.Response(200, json={'model':'gemma4:31b','message':{'role':'assistant','content':'Synthetic reply'},'done':True})
        with patch.dict(os.environ, {'OLLAMA_API_KEY':'synthetic-ollama-key','OPENAI_API_KEY':'never-send-openai','ANTHROPIC_API_KEY':'never-send-anthropic','OLLAMA_HOST':'http://untrusted.invalid'}), self.transport_client(handler):
            self.assertEqual(ollama_cloud.chat([{'role':'user','content':'Synthetic message'}], response_format='json'), 'Synthetic reply')
        self.assertEqual(len(calls), 1)

    def test_empty_key_fails_before_creating_client_without_provider_fallback(self):
        for key in ('', '   '):
            with patch.dict(os.environ, {'OLLAMA_API_KEY':key,'OPENAI_API_KEY':'never-send','ANTHROPIC_API_KEY':'never-send'}), patch.object(ollama_cloud, 'Client') as client:
                with self.assertRaises(ollama_cloud.OllamaCloudError) as error:
                    ollama_cloud.chat([])
                self.assertEqual(error.exception.status_code, 503)
                client.assert_not_called()

    def test_provider_errors_are_safe_and_not_retried(self):
        for status in (401, 402, 404, 429, 500):
            calls=[]
            def handler(request):
                calls.append(request)
                return httpx.Response(status, json={'error':'sensitive-provider-text'})
            with self.subTest(status=status), patch.dict(os.environ, {'OLLAMA_API_KEY':'synthetic-key'}), self.transport_client(handler):
                with self.assertRaises(ollama_cloud.OllamaCloudError) as error:
                    ollama_cloud.chat([])
                self.assertEqual(error.exception.status_code, status if status != 500 else 502)
                self.assertNotIn('sensitive-provider-text', str(error.exception))
            self.assertEqual(len(calls), 1)

    def test_connection_errors_and_empty_answers_are_controlled(self):
        def unreachable(request):
            raise httpx.ConnectError('sensitive-connection-text', request=request)
        def empty(request):
            return httpx.Response(200, json={'message':{'role':'assistant','content':''}})
        for handler in (unreachable, empty):
            with patch.dict(os.environ, {'OLLAMA_API_KEY':'synthetic-key'}), self.transport_client(handler):
                with self.assertRaises(ollama_cloud.OllamaCloudError) as error:
                    ollama_cloud.chat([])
                self.assertEqual(error.exception.status_code, 502)
                self.assertNotIn('sensitive-connection-text', str(error.exception))

    def test_cross_host_redirect_is_not_followed(self):
        calls=[]
        def redirect(request):
            calls.append(str(request.url))
            return httpx.Response(307, headers={'location':'https://untrusted.invalid/api/chat'})
        with patch.dict(os.environ, {'OLLAMA_API_KEY':'synthetic-key'}), self.transport_client(redirect):
            with self.assertRaises(ollama_cloud.OllamaCloudError):
                ollama_cloud.chat([])
        self.assertEqual(calls, ['https://ollama.com/api/chat'])

    def test_malformed_json_does_not_expose_response_text(self):
        def malformed(request):
            return httpx.Response(200, text='sensitive-non-json-response')
        with patch.dict(os.environ, {'OLLAMA_API_KEY':'synthetic-key'}), self.transport_client(malformed):
            with self.assertRaises(ollama_cloud.OllamaCloudError) as error:
                ollama_cloud.chat([])
            self.assertEqual(error.exception.status_code, 502)
            self.assertNotIn('sensitive-non-json-response', str(error.exception))
