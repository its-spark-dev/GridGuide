"""Export public HTTP types without loading raw data or starting a server."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.api import app

print(json.dumps(app.openapi(), sort_keys=True))
