"""Export both mode contracts without loading data or starting a server.

This is a type-generation union, not a claim that either mode serves all routes.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.api import create_app
from backend.synthetic_api import create_synthetic_app

schema = create_app().openapi()
synthetic = create_synthetic_app().openapi()
for section, additions in ((schema["paths"], synthetic["paths"]),
                           (schema["components"]["schemas"], synthetic["components"]["schemas"])):
    for key, value in additions.items():
        if key in section and section[key] != value:
            raise ValueError("Conflicting public contract definitions")
        section[key] = value
print(json.dumps(schema, sort_keys=True))
