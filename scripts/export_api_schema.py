"""Export both mode contracts without loading data or starting a server.

This is a type-generation union, not a claim that either mode serves all routes.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.api import create_app
from backend.operator_api import create_operator_app
from backend.contracts import CustomerPathFrame

schema = create_app().openapi()
synthetic = create_operator_app().openapi()
for section, additions in ((schema["paths"], synthetic["paths"]),
                           (schema["components"]["schemas"], synthetic["components"]["schemas"])):
    for key, value in additions.items():
        if key in section and section[key] != value:
            raise ValueError("Conflicting public contract definitions")
        section[key] = value
# Static prepared-frame contracts share generated types but add no HTTP endpoint.
frame = CustomerPathFrame.model_json_schema(ref_template='#/components/schemas/{model}')
schema['components']['schemas'].update(frame.pop('$defs', {}))
schema['components']['schemas']['CustomerPathFrame'] = frame
print(json.dumps(schema, sort_keys=True))
