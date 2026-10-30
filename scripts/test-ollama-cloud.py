"""Send one real request through the app's server-side Ollama Cloud client."""
import argparse
from pathlib import Path
import sys
from dotenv import load_dotenv

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--env-file", type=Path, help="Existing private env file; never prints its contents")
args = parser.parse_args()
if args.env_file:
    if not args.env_file.is_file():
        parser.error("The selected env file does not exist.")
    load_dotenv(args.env_file, override=False, interpolate=False)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.ollama_cloud import OllamaCloudError, chat

try:
    reply = chat([{"role": "user", "content": "Responda em português, em uma frase curta, confirmando que recebeu esta mensagem de teste."}])
except OllamaCloudError as error:
    print(f"Not tested yet — HTTP {error.status_code}: {error}", file=sys.stderr)
    raise SystemExit(1)
print(reply)
