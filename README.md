## 💰 Personal Finance Budget — AI Finance Assistant

A full-stack personal finance management application that helps users track income, manage expenses, create monthly budgets, and understand their spending habits.

The application combines **FastAPI**, **PostgreSQL**, **Streamlit**, and **Google's Gemini API** to provide a financial dashboard and an AI-powered finance assistant.

Users can securely manage their financial records, monitor monthly budget utilization, and ask natural-language questions about their category-wise spending.

## Features

### User Authentication
- User registration and login.
- Password hashing for secure credential storage.
- JWT-based authentication.
- Authenticated access to financial records.
- User-specific data isolation.

### Transaction management
- Add income and expense transactions.
- View transaction history.
- Update existing transactions.
- Delete transactions.
- Categorize transactions.
- Add custom transaction categories.
- Filter transactions by type and category.
- Search transactions using category or description.
- Store transaction dates and descriptions.

### Budget Management
- Create monthly budgets for different spending categories.
- Set individual category-wise spending limits.
- Update existing budget limits.
- Delete budgets.
- View monthly budget summaries.
- Calculate total spending and remaining budget.
- Monitor budget utilization through progress indicators.

## Budget alerts:
- Warning when 80% or more of a budget is utilized.
- Notification when the budget limit is reached.
- Alert when spending exceeds the budget.

### Financial Dashboard
- The dashboard provides an overview of the user's financial activity.

Features include:
- Total income for the current month.
- Total expenses for the current month.
- Remaining balance.
- Monthly budget overview.
- Income vs. expenses visualization.
- Category-wise expense breakdown.
- Recent transaction history.
- Monthly budget progress and alerts.

### AI Finance Assistant
The application integrates Google's Gemini API to understand natural-language financial questions.

Instead of calculating financial figures directly through the language model, the assistant uses **function calling (tool calling)** to retrieve actual financial data from PostgreSQL.

Example question:

```
How much did I spend on food in October 2026?
```

The assistant identifies the required category, month, and year, calls the Python finance tool, retrieves the calculated result, and generates a natural-language response.

Example response

```
You spent ₹250.00 on food in October 2026.
```

**Current AI tool:**

**get_category_spending**

Calculates total expenses for a selected category, month, and year using the authenticated user's database records.

## Technology stack

| Layer | Technologies |
|---|---|
| Programming Language | Python |
| Backend Framework | FastAPI |
| Frontend Framework | Streamlit |
| Database | PostgreSQL |
| ORM and migrations | SQLAlchemy, Alembic |
| Data Validation | Pydantic |
| Authentication | JWT |
| Password Security | Password Hashing |
| LLM | Google Gemini API |
| AI Integration | Gemini Function Calling |
| Data Processing | Pandas |
| Data Visualization | Plotly |
| API Communication | Requests |
| Testing | Pytest |
| API Documentation | Swagger UI |

## 🏗️ System Architecture
The application follows a client-server architecture.

- Streamlit provides the user interface.
- FastAPI handles application logic and REST API requests.
- PostgreSQL stores user, transaction, and budget information.
- SQLAlchemy manages database operations.
- Gemini interprets natural-language finance questions.
- Python finance tools retrieve and calculate financial information.

## 🤖 AI Finance Assistant — Tool Calling Workflow

One of the important components of this project is the integration of Gemini function calling with Python backend tools.

The language model does not directly access the database. Instead, it identifies the appropriate tool and provides the required arguments. The backend validates the arguments and executes the Python function.

**Example Workflow**

**User question:** 
```
How much did I spend on Travel in October 2026?
```
Step 1 — User submits a question

The Streamlit frontend sends the question to:

```
POST /ai/ask
```

Step 2 — Gemini identifies the required tool

Gemini selects:

```
get_category_spending
```

And generates arguments:

```
{
    "category": "Food",
    "month": 10,
    "year": 2026
}
```

Step 3 — Backend validates the arguments

The backend validates the category, month, and year before executing the function.

The authenticated user's ID is supplied by FastAPI authentication rather than being accepted from Gemini.

Step 4 — Python executes the finance tool

```
tool_result = get_category_spending(
    db=db,
    user_id=user_id,
    category=category,
    month=month,
    year=year,
)
```

The tool queries PostgreSQL and calculates the total expenses for the requested category and period.

Step 5 — Tool result is sent back to Gemini

The backend provides the function result to Gemini so it can generate a natural-language explanation.

Step 6 — Final response

```
Example tool result:

{
    "category": "Food",
    "month": 10,
    "year": 2026,
    "total_spending": "250.00",
    "currency": "INR"
}
```

Final AI response:

```
You spent ₹250.00 on food in October 2026.
```

## 🗄️ Database Design

The application uses PostgreSQL as its primary relational database.
SQLAlchemy is used as the ORM, while Alembic manages database schema migrations.

## Main Database Models
| Model | Purpose |
|---|---|
| User | Stores user account information and authentication details. |
| Transaction | Stores income and expense records. |
| Budget | tores monthly category-wise spending limits. |

## Database migrations

Alembic manages schema migrations. After pulling changes that add a migration, apply them from the `backend` directory:

```powershell
alembic upgrade head
```

To check the current migration revision:

```powershell
alembic current
```


## 📁 Project Structure
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

## ⚙️ Installation and Setup

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


## 🧪 Testing
The backend uses Pytest for testing.

The test suite includes:
- Database connection tests.
- Finance API endpoint tests.
- Finance tool tests.
- Authentication and security tests.
- Shared test fixtures.

**Run Tests**
Navigate to the backend directory:

**cd backend**

Activate the virtual environment:

**.\.venv\Scripts\Activate.ps1**

Run all tests:

**pytest -v**

Run an individual test file:

**pytest tests/test_finance_tools.py -v**

Run database connection tests:

**pytest tests/test_db_connection.py -v**


## 🔐 Security Considerations

- Keep secrets in local environment variables or an untracked `.env` file.
- Use a strong, unique `JWT_SECRET_KEY` outside local development.
- Do not expose database credentials or Gemini API keys in frontend code.
- The backend derives the user identity from the validated JWT and filters financial records by that user.

## 👩‍💻 Author

Sanika Gajarishi

B.Tech — Artificial Intelligence and Data Science

GitHub: Sanika-Gajarishi

Project Repository: Personal Finance Budget

 ## 📄 License

No license file is currently present in this repository. Unless a license is added, do not assume the code is open for reuse, redistribution, or modification by others.
