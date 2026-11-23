
"""Customer Support Bot (Day 7 Challenge: risk review)."""

import json
import logging

from flask import Flask, jsonify, request

from llm import call_llm

app = Flask(__name__)

API_KEY = "sk-demo-4f9a2c71-FAKE-KEY-for-training-only"

logging.basicConfig(filename="logs/app.log", level=logging.INFO)

ORDERS = {
    "10231": {
        "status": "Shipped",
        "amount": 1299,
        "customer_email": "ravi.kumar@example.com"
    },
    "10232": {
        "status": "Delivered",
        "amount": 499,
        "customer_email": "priya.s@example.com"
    },
    "10233": {
        "status": "Processing",
        "amount": 2499,
        "customer_email": "ravi.kumar@example.com"
    },
}


CUSTOMERS = {
    "ravi.kumar@example.com": {
        "name": "Ravi Kumar",
        "phone": "+91 98480 12345",
        "active": True
    },
    "priya.s@example.com": {
        "name": "Priya Sharma",
        "phone": "+91 99890 67890",
        "active": True
    },
}

CUSTOMER_TOKENS = {
    "demo-ravi-token": "ravi.kumar@example.com",
    "demo-priya-token": "priya.s@example.com",
}

REFUNDS = []


# ---------- Tools the LLM can use ----------

def get_order_status(order_id):
    order = ORDERS.get(order_id)
    return order["status"] if order else "Order not found"



def issue_refund(order_id, amount, customer_email):
    order = ORDERS.get(order_id)

    if not order:
        return "Refund rejected: order not found"

    if order["customer_email"] != customer_email:
        return "Refund rejected: order does not belong to this customer"

    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
        return "Refund rejected: invalid amount"

    if amount > order["amount"]:
        return "Refund rejected: amount exceeds order value"

    REFUNDS.append({
        "order_id": order_id,
        "amount": amount
    })

    return f"Refunded Rs {amount} for order {order_id}"


def delete_customer_account(customer_email):
    CUSTOMERS.pop(customer_email, None)
    return f"Deleted account {customer_email}"


TOOLS = {
    "get_order_status": get_order_status,
    "issue_refund": issue_refund,
    "delete_customer_account": delete_customer_account,
}


# ---------- Chat endpoint ----------

@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}

    # Verify customer token
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Unauthorized"}), 401

    token = auth_header[len("Bearer "):]
    authenticated_email = CUSTOMER_TOKENS.get(token)

    email = data.get("customer_email", "")
    message = data.get("message", "")

    if not authenticated_email or email != authenticated_email:
        return jsonify({"error": "Unauthorized"}), 401

    customer = CUSTOMERS.get(email, {})

    prompt = (
        "You are a helpful support agent. Reply in JSON with reply, action and args.\n"
        f"Customer name: {customer.get('name')}\n"
        f"Customer email: {email}\n"
        f"Customer phone: {customer.get('phone')}\n"
        f"Customer message: {message}"
    )

    logging.info("PROMPT: %s", prompt)

    text, usage = call_llm(prompt, API_KEY)
    result = json.loads(text)

   
    action = result.get("action")
    action_result = None

    if action:
        args = result.get("args", {})

        if action == "issue_refund":
            args["customer_email"] = email

        elif args.get("customer_email") == "from_request":
            args["customer_email"] = email

        action_result = TOOLS[action](**args)


    logging.info("REPLY to %s: %s", email, result["reply"])

    return jsonify({
        "reply": result["reply"],
        "action_result": action_result
    })


if __name__ == "__main__":
    app.run(debug=False)
