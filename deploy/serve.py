"""One process, explicit bounds, no access/body logging; SIGTERM handled by uvicorn."""
import os
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.public_app import create_public_app
import uvicorn

if __name__ == '__main__':
    uvicorn.run(create_public_app(), host='0.0.0.0', port=int(os.environ.get('PORT','8000')),
                access_log=False, log_level='warning', limit_concurrency=16,
                timeout_keep_alive=5, timeout_graceful_shutdown=10, proxy_headers=False)
