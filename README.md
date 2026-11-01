# Personal Finance Budget

A full-stack personal finance and expense management application built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, **Alembic**, **Streamlit**, and the **Gemini API**. It helps users record income and expenses, set monthly category budgets, review spending patterns, and ask an AI finance assistant questions about category spending.

> Currency: INR (₹). The application uses authenticated user accounts and scopes financial records to the signed-in user.

## Features

### Authentication
- User registration with email and password.
- Login using JWT bearer tokens.
- Authenticated endpoints for retrieving the current user.
- Passwords are stored as hashes, not as plain text.

### Transaction management
- Create income and expense transactions.
- View transaction history with pagination support.
- Filter transactions by type and date range.
- Retrieve, update, and delete transactions.
- Store amount, category, optional description, type, and transaction date.
- Transaction queries are restricted to the authenticated user.

### Monthly budgets
- Create a monthly spending limit for a category.
- View budgets by month and year.
- Update and delete budgets.
- Calculate category-level spending from expense transactions.
- View total budget, total spent, remaining amount, percentage used, and budget status.
- Highlight budgets that are nearing or exceeding their limits.

### Dashboard and visualizations
- Current-month income, expenses, and remaining balance.
- Income-versus-expenses chart.
- Expense category breakdown.
- Recent transaction list.
- Monthly budget progress and alerts.

### AI Finance Assistant
- Uses the Gemini API with function/tool calling.
- The model can request the `get_category_spending` Python tool for a category, month, and year.
- The backend executes the database query using the authenticated user's ID.
- The tool result is passed back to Gemini to produce a natural-language explanation.
- The response includes the tool name and calculated result as well as the explanation.

The AI assistant currently implements category-spending questions through the `get_category_spending` tool; it is not a general-purpose financial planner or a bank-connected service.

## Technology stack

| Layer | Technologies |
|---|---|
| Frontend | Python, Streamlit, Pandas, Plotly, Requests |
| Backend API | Python, FastAPI, Pydantic |
| Database | PostgreSQL |
| ORM and migrations | SQLAlchemy, Alembic |
| Authentication | JWT, password hashing |
| AI | Google Gemini API, `google-genai` SDK, function calling |
| Testing | Pytest |

## Project structure

```text
Personal_Finance_Budget/
├── backend/
│   ├── alembic/
│   │   ├── versions/          # Database migration revisions
│   │   └── env.py
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── transactions.py
│   │   │   ├── budgets.py
│   │   │   └── ai.py
│   │   ├── core/              # Settings, security and token helpers
│   │   ├── db/                # SQLAlchemy database setup
│   │   ├── models/            # User, Transaction and Budget models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/
│   │   │   └── gemini_service.py
│   │   ├── tools/
│   │   │   └── finance_tools.py
│   │   └── main.py
│   ├── tests/
│   ├── .env                   # Create locally; do not commit
│   ├── alembic.ini
│   └── requirements.txt
└── frontend/
    ├── app.py
    ├── api_client.py
    └── requirements.txt
```

## Prerequisites

- Python 3.10 or later.
- PostgreSQL.
- A Google Gemini API key.
- Git.

## Setup

The commands below use Windows PowerShell. Run them from the repository root unless a different directory is shown.

### 1. Clone the repository

```powershell
git clone https://github.com/Sanika-Gajarishi/Personal_Finance_Budget.git
cd Personal_Finance_Budget
```

### 2. Create the PostgreSQL database

Open PostgreSQL (for example, with pgAdmin or psql) and create a database:

```sql
CREATE DATABASE personal_finance_agent;
```

Use your own PostgreSQL username, password, host, and port in the connection string in the next step.

### 3. Configure backend environment variables

Create a file named `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/personal_finance_agent
JWT_SECRET_KEY=replace_this_with_a_long_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GEMINI_API_KEY=your_gemini_api_key
```

Replace the example values with your local credentials and API key. URL-encode special characters in the database password when required by the connection URL format.

**Security:** Never commit `.env`, database credentials, JWT secrets, or API keys. Keep the local environment file out of version control.

### 4. Set up and start the backend

```powershell
cd backend

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Apply the database migrations:

```powershell
alembic upgrade head
```

Start the FastAPI development server:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URLs:

- API root: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs

Keep the backend terminal running while using the frontend.

### 5. Set up and start the Streamlit frontend

Open a **second** PowerShell terminal at the repository root:

```powershell
cd frontend

# Activate the backend virtual environment created in the previous step.
..\backend\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit will print the local URL in the terminal (normally http://localhost:8501). Open that URL in your browser.

The frontend API client uses `http://127.0.0.1:8000` by default. To use another backend URL, set `FINANCE_API_URL` in the frontend process environment before starting Streamlit.

## Using the application

1. Open the Streamlit app and create an account.
2. Log in with the registered email and password.
3. Add income and expense transactions from the Transactions page.
4. Open Budgets to create monthly category spending limits.
5. Review balances, charts, recent activity, budget progress, and alerts on the Dashboard.
6. Ask supported category-spending questions in the AI Finance Assistant, for example: `How much did I spend on Food in October 2026?`

The AI assistant's tool uses the transaction records belonging to the currently authenticated user. It calculates expenses only (not income) for the requested category and calendar month.

## API overview

All routes below are mounted by the FastAPI application. Except for registration and login, the user-facing finance endpoints require a valid bearer access token.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Register a user |
| POST | `/auth/login` | Obtain a JWT access token |
| GET | `/auth/me` | Get the authenticated user |
| POST | `/transactions/` | Create a transaction |
| GET | `/transactions/` | List transactions; supports type, date and pagination filters |
| GET | `/transactions/{transaction_id}` | Retrieve one transaction |
| PATCH | `/transactions/{transaction_id}` | Update a transaction |
| DELETE | `/transactions/{transaction_id}` | Delete a transaction |
| POST | `/budgets/` | Create a monthly category budget |
| GET | `/budgets/` | List budgets; supports month and year filters |
| PATCH | `/budgets/{budget_id}` | Update a budget limit |
| DELETE | `/budgets/{budget_id}` | Delete a budget |
| GET | `/budgets/summary?month=10&year=2026` | Get the selected month's budget summary |
| POST | `/ai/ask` | Ask the AI finance assistant |
| GET | `/health` | Check API health |

### Example: ask the AI assistant

Request:

```http
POST /ai/ask
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

```json
{
  "question": "How much did I spend on Food in October 2026?"
}
```

The AI endpoint uses the authenticated account from the token. A user ID is not accepted from the question or from Gemini's tool arguments.

## Database migrations

Alembic manages schema migrations. After pulling changes that add a migration, apply them from the `backend` directory:

```powershell
alembic upgrade head
```

To check the current migration revision:

```powershell
alembic current
```

## Running tests

From the `backend` directory with the virtual environment activated:

```powershell
pytest
```

Tests may require a configured test database and environment variables, depending on the test configuration.

## Configuration reference

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy PostgreSQL connection URL |
| `JWT_SECRET_KEY` | Secret used to sign access tokens |
| `JWT_ALGORITHM` | JWT signing algorithm (defaults to `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes (defaults to `30`) |
| `GEMINI_API_KEY` | Credential for Gemini API requests |
| `FINANCE_API_URL` | Optional frontend override for the FastAPI base URL |

## Troubleshooting

### Frontend cannot connect to FastAPI

- Confirm the backend server is running.
- Open http://127.0.0.1:8000/health and check for a healthy response.
- Confirm `FINANCE_API_URL` points to the backend address used by your environment.

### Database connection or missing-table errors

- Confirm PostgreSQL is running.
- Verify `DATABASE_URL` and that the database exists.
- Run `alembic upgrade head` from the `backend` directory.

### AI assistant errors or timeouts

- Confirm `GEMINI_API_KEY` is set correctly in `backend/.env`.
- Check the FastAPI terminal for the backend exception details.
- Verify that the machine can reach the Gemini API.
- Remember that the AI question flow makes a model request to select tool arguments and a further model request to explain the tool result.

## Security notes

- Keep secrets in local environment variables or an untracked `.env` file.
- Use a strong, unique `JWT_SECRET_KEY` outside local development.
- Do not expose database credentials or Gemini API keys in frontend code.
- The backend derives the user identity from the validated JWT and filters financial records by that user.

## Current scope and limitations

- The application stores transactions entered by the user; no bank account synchronization is documented in the implementation.
- The Gemini tool currently supports category spending totals for a specified month and year.
- The frontend and backend are configured for local development in the setup instructions above; production deployment requires appropriate hosted database, API, secrets, HTTPS, and CORS configuration.

## License

No license file is currently present in this repository. Unless a license is added, do not assume the code is open for reuse, redistribution, or modification by others.
