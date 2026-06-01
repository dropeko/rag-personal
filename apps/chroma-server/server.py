import os
import subprocess
import sys

from dotenv import load_dotenv

# Load variables from .env in this directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH")
PORT = os.getenv("CHROMA_PORT", "8000")


def run_server():
    print(f"Starting ChromaDB server (v1.x) pointing to: {CHROMA_DB_PATH}")
    print(f"Listening on http://0.0.0.0:{PORT}")

    # ChromaDB v1.x removed the `chroma run` CLI command.
    # The server is now a FastAPI app served via uvicorn.
    # We pass the persistence settings via environment variables.
    env = os.environ.copy()
    env["IS_PERSISTENT"] = "1"
    env["PERSIST_DIRECTORY"] = CHROMA_DB_PATH
    env["ANONYMIZED_TELEMETRY"] = "false"

    cmd = [
        sys.executable, "-m", "uvicorn",
        "chromadb.app:app",
        "--host", "0.0.0.0",
        "--port", PORT,
    ]

    try:
        subprocess.run(cmd, check=True, env=env)
    except KeyboardInterrupt:
        print("\nStopping ChromaDB server...")
    except subprocess.CalledProcessError as e:
        print(f"ChromaDB server exited with error code: {e.returncode}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running ChromaDB server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if not CHROMA_DB_PATH:
        print("Error: CHROMA_DB_PATH environment variable is not set.")
        print("Please set it in apps/chroma-server/.env")
        sys.exit(1)

    if not os.path.exists(CHROMA_DB_PATH):
        print(f"ChromaDB path not found, creating: {CHROMA_DB_PATH}")
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)

    run_server()
