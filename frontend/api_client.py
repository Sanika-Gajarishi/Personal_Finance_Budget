import os

import requests


API_BASE_URL = os.getenv(
    "FINANCE_API_URL",
    "http://127.0.0.1:8000",
)

TIMEOUT = 20


def handle_response(response):
    """Convert an HTTP response into a consistent result dictionary."""
    try:
        data = response.json()
    except ValueError:
        data = None

    if response.ok:
        return {
            "success": True,
            "data": data,
            "message": "Request successful.",
        }

    if isinstance(data, dict):
        message = data.get("detail", "The request failed.")
    else:
        message = f"Request failed with status {response.status_code}."

    if isinstance(message, list):
        message = "; ".join(
            str(item.get("msg", item)) if isinstance(item, dict)
            else str(item)
            for item in message
        )

    return {
        "success": False,
        "data": data,
        "message": str(message),
    }


def request_error(error):
    """Return a friendly message for connection and timeout errors."""
    return {
        "success": False,
        "data": None,
        "message": (
            "Unable to contact the backend. "
            "Check that FastAPI is running at "
            f"{API_BASE_URL}. Details: {error}"
        ),
    }


def auth_headers(token):
    """Add the logged-in user's JWT to an API request."""
    return {
        "Authorization": f"Bearer {token}",
    }


def register_user(email, password, full_name=None):
    payload = {
        "email": email,
        "password": password,
    }

    if full_name:
        payload["full_name"] = full_name

    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json=payload,
            timeout=TIMEOUT,
        )
        return handle_response(response)

    except requests.RequestException as error:
        return request_error(error)


def login_user(email, password):
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data={
                "username": email,
                "password": password,
            },
            timeout=TIMEOUT,
        )
        return handle_response(response)

    except requests.RequestException as error:
        return request_error(error)


def get_current_user(token):
    try:
        response = requests.get(
            f"{API_BASE_URL}/auth/me",
            headers=auth_headers(token),
            timeout=TIMEOUT,
        )
        return handle_response(response)

    except requests.RequestException as error:
        return request_error(error)


def get_transactions(
    token,
    transaction_type=None,
    start_date=None,
    end_date=None,
    limit=100,
    offset=0,
):
    """Get transactions belonging to the authenticated user."""
    params = {
        "limit": limit,
        "offset": offset,
    }

    if transaction_type:
        params["transaction_type"] = transaction_type

    if start_date:
        params["start_date"] = str(start_date)

    if end_date:
        params["end_date"] = str(end_date)

    try:
        response = requests.get(
            f"{API_BASE_URL}/transactions/",
            headers=auth_headers(token),
            params=params,
            timeout=TIMEOUT,
        )
        return handle_response(response)

    except requests.RequestException as error:
        return request_error(error)


def create_transaction(
    token,
    amount,
    category,
    description,
    transaction_type,
    transaction_date,
):
    """Create an income or expense transaction in PostgreSQL."""
    payload = {
        "amount": str(amount),
        "category": category.strip(),
        "description": description.strip() or None,
        "transaction_type": transaction_type,
        "transaction_date": str(transaction_date),
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/transactions/",
            headers=auth_headers(token),
            json=payload,
            timeout=TIMEOUT,
        )
        return handle_response(response)

    except requests.RequestException as error:
        return request_error(error)


def update_transaction(token, transaction_id, updates):
    """Update an existing transaction."""
    try:
        response = requests.patch(
            f"{API_BASE_URL}/transactions/{transaction_id}",
            headers=auth_headers(token),
            json=updates,
            timeout=TIMEOUT,
        )
        return handle_response(response)

    except requests.RequestException as error:
        return request_error(error)


def delete_transaction(token, transaction_id):
    """Delete a transaction belonging to the authenticated user."""
    try:
        response = requests.delete(
            f"{API_BASE_URL}/transactions/{transaction_id}",
            headers=auth_headers(token),
            timeout=TIMEOUT,
        )
        return handle_response(response)

    except requests.RequestException as error:
        return request_error(error)

def get_budgets(token, month=None, year=None):
    """Fetch the authenticated user's budgets, optionally filtered by month and year."""
    params = {}

    if month is not None:
        params["month"] = month

    if year is not None:
        params["year"] = year

    response = requests.get(
        f"{API_BASE_URL}/budgets/",
        headers=auth_headers(token),
        params=params,
        timeout=TIMEOUT,
    )

    return handle_response(response)


def create_budget(token, category, monthly_limit, month, year):
    """Create a monthly budget for a category."""
    payload = {
        "category": category,
        "monthly_limit": str(monthly_limit),
        "month": month,
        "year": year,
    }

    response = requests.post(
        f"{API_BASE_URL}/budgets/",
        headers=auth_headers(token),
        json=payload,
        timeout=TIMEOUT,
    )

    return handle_response(response)


def update_budget(token, budget_id, monthly_limit):
    """Update a budget's monthly spending limit."""
    response = requests.patch(
        f"{API_BASE_URL}/budgets/{budget_id}",
        headers=auth_headers(token),
        json={"monthly_limit": str(monthly_limit)},
        timeout=TIMEOUT,
    )

    return handle_response(response)


def delete_budget(token, budget_id):
    """Delete a budget."""
    response = requests.delete(
        f"{API_BASE_URL}/budgets/{budget_id}",
        headers=auth_headers(token),
        timeout=TIMEOUT,
    )

    return handle_response(response)


def get_budget_summary(token, month, year):
    """Fetch spending summaries for a particular month."""
    response = requests.get(
        f"{API_BASE_URL}/budgets/summary",
        headers=auth_headers(token),
        params={
            "month": month,
            "year": year,
        },
        timeout=TIMEOUT,
    )

    return handle_response(response)



def ask_finance_assistant(token, question):
    try:
        response = requests.post(
            f"{API_BASE_URL}/ai/ask",
            headers=auth_headers(token),
            json={
                "question": question,
            },
            timeout=60,
        )
        return handle_response(response)

    except requests.RequestException as error:
        return request_error(error)