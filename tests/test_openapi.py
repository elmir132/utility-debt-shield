"""Keep openapi.yaml honest: it must describe exactly the routes the app serves."""
import re
from pathlib import Path

import yaml

from app import create_app
from udshield.models import Flag

SPEC = yaml.safe_load((Path(__file__).parent.parent / "openapi.yaml").read_text())


def flask_routes():
    routes = set()
    for rule in create_app().url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        path = re.sub(r"<[^>]*?(\w+)>", r"{\1}", rule.rule).replace("{check_id}", "{id}")
        for method in rule.methods - {"HEAD", "OPTIONS"}:
            routes.add((method.lower(), path))
    return routes


def test_spec_routes_match_app_routes():
    spec_routes = {(m, p) for p, ops in SPEC["paths"].items() for m in ops}
    assert spec_routes == flask_routes()


def test_flag_codes_in_spec_match_engine():
    import udshield.engine as engine
    src = Path(engine.__file__).read_text()
    in_code = set(re.findall(r'Flag\("([A-Z_]+)"', src))
    in_spec = set(SPEC["components"]["schemas"]["Flag"]["properties"]["code"]["enum"])
    assert in_code == in_spec


def test_response_has_every_documented_field():
    client = create_app().test_client()
    body = client.post("/v1/checks", json={"address": "3 demo street, example city", "consent": True}).get_json()
    assert set(SPEC["components"]["schemas"]["Check"]["properties"]) <= set(body)
    assert set(SPEC["components"]["schemas"]["Flag"]["properties"]) == set(body["flags"][0])
