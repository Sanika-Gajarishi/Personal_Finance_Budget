def register_and_login(client, email="tester@example.com"):
    # Register a user
    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert register_response.status_code == 201

    # Log in using OAuth2 form data
    login_response = client.post(
        "/auth/login",
        data={
            "username": email,
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def test_register_and_login(client):
    headers = register_and_login(client)

    response = client.get(
        "/auth/me",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["email"] == "tester@example.com"


def test_create_and_list_transactions(client):
    headers = register_and_login(client)

    create_response = client.post(
        "/transactions/",
        headers=headers,
        json={
            "amount": "450.00",
            "category": "Food",
            "description": "Lunch",
            "transaction_type": "expense",
            "transaction_date": "2026-10-28",
        },
    )

    assert create_response.status_code == 201

    transaction = create_response.json()

    assert transaction["amount"] == "450.00"
    assert transaction["category"] == "Food"
    assert transaction["transaction_type"] == "expense"

    list_response = client.get(
        "/transactions/",
        headers=headers,
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_filter_transactions_by_type(client):
    headers = register_and_login(client)

    client.post(
        "/transactions/",
        headers=headers,
        json={
            "amount": "450.00",
            "category": "Food",
            "transaction_type": "expense",
            "transaction_date": "2026-10-28",
        },
    )

    client.post(
        "/transactions/",
        headers=headers,
        json={
            "amount": "25000.00",
            "category": "Salary",
            "transaction_type": "income",
            "transaction_date": "2026-10-28",
        },
    )

    response = client.get(
        "/transactions/?transaction_type=expense",
        headers=headers,
    )

    assert response.status_code == 200

    transactions = response.json()

    assert len(transactions) == 1
    assert transactions[0]["category"] == "Food"


def test_users_cannot_access_each_others_transactions(client):
    user_a_headers = register_and_login(
        client,
        "usera@example.com",
    )

    create_response = client.post(
        "/transactions/",
        headers=user_a_headers,
        json={
            "amount": "500.00",
            "category": "Food",
            "transaction_type": "expense",
            "transaction_date": "2026-10-28",
        },
    )

    assert create_response.status_code == 201

    transaction_id = create_response.json()["id"]

    user_b_headers = register_and_login(
        client,
        "userb@example.com",
    )

    response = client.get(
        f"/transactions/{transaction_id}",
        headers=user_b_headers,
    )

    assert response.status_code == 404


def test_create_budget_and_calculate_summary(client):
    headers = register_and_login(client)

    # Create a food expense
    transaction_response = client.post(
        "/transactions/",
        headers=headers,
        json={
            "amount": "1500.00",
            "category": "Food",
            "transaction_type": "expense",
            "transaction_date": "2026-10-15",
        },
    )

    assert transaction_response.status_code == 201

    # Create the October food budget
    budget_response = client.post(
        "/budgets/",
        headers=headers,
        json={
            "category": "Food",
            "monthly_limit": "5000.00",
            "month": 10,
            "year": 2026,
        },
    )

    assert budget_response.status_code == 201

    # Retrieve the monthly summary
    summary_response = client.get(
        "/budgets/summary?month=10&year=2026",
        headers=headers,
    )

    assert summary_response.status_code == 200

    summary = summary_response.json()

    assert summary["total_budget"] == "5000.00"
    assert summary["total_spent"] == "1500.00"
    assert summary["total_remaining"] == "3500.00"

    food_budget = summary["budgets"][0]

    assert food_budget["category"] == "Food"
    assert food_budget["percentage_used"] == 30.0
    assert food_budget["status"] == "within_budget"


def test_duplicate_budget_is_rejected(client):
    headers = register_and_login(client)

    budget_data = {
        "category": "Food",
        "monthly_limit": "5000.00",
        "month": 10,
        "year": 2026,
    }

    first_response = client.post(
        "/budgets/",
        headers=headers,
        json=budget_data,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/budgets/",
        headers=headers,
        json=budget_data,
    )

    assert second_response.status_code == 409


def test_transaction_requires_authentication(client):
    response = client.get("/transactions/")

    assert response.status_code == 401