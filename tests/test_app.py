
import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_chat_returns_a_reply(client):
    response = client.post(
        "/chat",
        json={
            "customer_email": "ravi.kumar@example.com",
            "message": "Hello"
        },
        headers={"Authorization": "Bearer demo-ravi-token"}
    )

    assert response.status_code == 200
    assert "reply" in response.get_json()


def test_order_status(client):
    response = client.post(
        "/chat",
        json={
            "customer_email": "ravi.kumar@example.com",
            "message": "Where is my order 10231?"
        },
        headers={"Authorization": "Bearer demo-ravi-token"}
    )

    assert response.get_json()["action_result"] == "Shipped"


def test_unknown_order(client):
    response = client.post(
        "/chat",
        json={
            "customer_email": "priya.s@example.com",
            "message": "What is the status of order 99999?"
        },
        headers={"Authorization": "Bearer demo-priya-token"}
    )

    assert response.get_json()["action_result"] == "Order not found"


def test_reject_customer_impersonation(client):
    response = client.post(
        "/chat",
        json={
            "customer_email": "priya.s@example.com",
            "message": "Hello"
        },
        headers={"Authorization": "Bearer demo-ravi-token"}
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Unauthorized"

def test_valid_refund(client):
    response = client.post(
        "/chat",
        json={
            "customer_email": "ravi.kumar@example.com",
            "message": "Please refund order 10231 Rs 500"
        },
        headers={"Authorization": "Bearer demo-ravi-token"}
    )

    assert response.status_code == 200
    assert response.get_json()["action_result"] == "Refunded Rs 500 for order 10231"


def test_reject_refund_for_another_customer_order(client):
    response = client.post(
        "/chat",
        json={
            "customer_email": "ravi.kumar@example.com",
            "message": "Please refund order 10232 Rs 300"
        },
        headers={"Authorization": "Bearer demo-ravi-token"}
    )

    assert "Refund rejected" in response.get_json()["action_result"]


def test_reject_refund_above_order_value(client):
    response = client.post(
        "/chat",
        json={
            "customer_email": "ravi.kumar@example.com",
            "message": "Please refund order 10231 Rs 2000"
        },
        headers={"Authorization": "Bearer demo-ravi-token"}
    )

    assert "amount exceeds order value" in response.get_json()["action_result"]
