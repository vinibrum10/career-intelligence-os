"""Server-only Ollama Cloud transport. Never falls back to another provider's key."""
import os

import httpx
from ollama import Client, ResponseError

HOST = "https://ollama.com"
MODEL = "gemma4:31b"
TIMEOUT_SECONDS = 300


class OllamaCloudError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        super().__init__(message)


def chat(messages, *, response_format=None):
    key = os.environ.get("OLLAMA_API_KEY", "").strip()
    if not key:
        raise OllamaCloudError(503, "Configure OLLAMA_API_KEY no servidor antes de gerar rascunhos.")
    try:
        with Client(host=HOST, headers={"Authorization": "Bearer " + key},
                    timeout=TIMEOUT_SECONDS, follow_redirects=False) as client:
            reply = client.chat(model=MODEL, messages=messages, stream=False, think=False,
                                format=response_format, options={"temperature": 0})
    except ResponseError as error:
        # Provider bodies may contain sensitive information; return only controlled messages.
        messages_by_status = {
            401: "A chave do Ollama Cloud está ausente ou inválida.",
            402: "Adicione créditos de uso à sua conta Ollama antes de tentar novamente.",
            404: "O modelo gemma4:31b não foi encontrado no Ollama Cloud.",
            429: "O limite de uso do Ollama Cloud foi atingido. Aguarde antes de tentar novamente.",
        }
        status = error.status_code if error.status_code in messages_by_status else 502
        raise OllamaCloudError(status, messages_by_status.get(status, "O Ollama Cloud não conseguiu concluir a solicitação.")) from None
    except (httpx.RequestError, ConnectionError, OSError):
        raise OllamaCloudError(502, "Não foi possível conectar ao Ollama Cloud.") from None
    except ValueError:
        raise OllamaCloudError(502, "O Ollama Cloud retornou uma resposta em formato inválido.") from None
    content = reply.message.content
    if not isinstance(content, str) or not content.strip():
        raise OllamaCloudError(502, "O Ollama Cloud retornou uma resposta vazia.")
    return content
