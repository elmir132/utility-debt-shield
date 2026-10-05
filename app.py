import os
import uuid

from flask import Flask, jsonify, request

from udshield.engine import evaluate
from udshield.providers import MockProvider


def create_app(provider=None):
    app = Flask(__name__)
    provider = provider or MockProvider()
    checks = {}  # in-memory; a real service would need retention rules for this data

    @app.post("/v1/checks")
    def create_check():
        body = request.get_json(silent=True) or {}
        address = body.get("address")
        if not isinstance(address, str) or not address.strip():
            return jsonify(error="'address' is required"), 400
        if body.get("consent") is not True:
            # Utility account data may only be read with the account holder's consent.
            return jsonify(error="account-holder consent is required (consent: true)"), 403
        result = evaluate(address.strip(), provider.fetch(address), provider.name)
        check_id = uuid.uuid4().hex[:12]
        checks[check_id] = result.to_dict()
        return jsonify(id=check_id, **checks[check_id]), 201

    @app.get("/v1/checks/<check_id>")
    def get_check(check_id):
        if check_id not in checks:
            return jsonify(error="not found"), 404
        return jsonify(id=check_id, **checks[check_id])

    @app.get("/healthz")
    def healthz():
        return jsonify(ok=True)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", "5000")), debug=False)
