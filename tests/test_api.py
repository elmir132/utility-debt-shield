import pytest

from app import create_app


@pytest.fixture
def client():
    return create_app().test_client()


def post(client, **body):
    return client.post("/v1/checks", json=body)


def test_requires_address(client):
    assert post(client, consent=True).status_code == 400


def test_requires_explicit_consent(client):
    assert post(client, address="1 demo street, example city").status_code == 403
    assert post(client, address="1 demo street, example city", consent="yes").status_code == 403
    assert post(client, address="1 demo street, example city", consent=False).status_code == 403


def test_clean_demo_address(client):
    res = post(client, address="1 Demo Street, Example City", consent=True)
    body = res.get_json()
    assert res.status_code == 201
    assert body["friction"] == "none" and body["data_source"] == "mock"


def test_arrears_demo_address_flags_balance_hold_and_deposit(client):
    body = post(client, address="3 demo street, example city", consent=True).get_json()
    codes = {f["code"] for f in body["flags"]}
    assert body["friction"] == "high"
    assert {"BALANCE_ON_ACCOUNT", "METER_HOLD", "DEPOSIT_REQUIRED"} <= codes


def test_no_balance_data_is_unknown(client):
    body = post(client, address="4 demo street, example city", consent=True).get_json()
    assert body["friction"] == "unknown"


def test_unlisted_address_is_stable(client):
    a = post(client, address="99 Other Road", consent=True).get_json()
    b = post(client, address="99 other road ", consent=True).get_json()
    assert a["friction"] == b["friction"]


def test_get_check_roundtrip_and_404(client):
    created = post(client, address="2 demo street, example city", consent=True).get_json()
    fetched = client.get(f"/v1/checks/{created['id']}").get_json()
    assert fetched == created
    assert client.get("/v1/checks/nope").status_code == 404
