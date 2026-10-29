from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from app.tools.finance_tools import get_category_spending
from app.core.config import settings


client = genai.Client(
    api_key=settings.GEMINI_API_KEY,
)


get_category_spending_declaration = types.FunctionDeclaration(
    name="get_category_spending",
    description=(
        "Calculate the total expenses for a specified category "
        "for a particular month and year. Use this tool when "
        "the user asks how much they spent in a category."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "category": types.Schema(
                type=types.Type.STRING,
                description=(
                    "The expense category, such as Food, "
                    "Shopping, Travel, or Entertainment."
                ),
            ),
            "month": types.Schema(
                type=types.Type.INTEGER,
                description="Month number from 1 to 12.",
            ),
            "year": types.Schema(
                type=types.Type.INTEGER,
                description="Four-digit year, such as 2026.",
            ),
        },
        required=["category", "month", "year"],
    ),
)


finance_tools = [
    types.Tool(
        function_declarations=[
            get_category_spending_declaration
        ]
    )
]

def request_category_spending_tool(question: str):
    """
    Ask Gemini to identify the category-spending tool
    and provide its arguments.
    """

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=question,
        config=types.GenerateContentConfig(
            tools=finance_tools,
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="ANY",
                    allowed_function_names=[
                        "get_category_spending"
                    ],
                )
            ),
        ),
    )

    return response

def answer_category_spending_question(
    question: str,
    db: Session,
    user_id: int,
) -> dict:
    """
    Ask Gemini to interpret a spending question, execute
    the requested finance tool, and generate a final answer.

    The user_id must come from the authenticated backend,
    never from Gemini's function-call arguments.
    """

    # 1. Ask Gemini to select the finance tool.
    response = request_category_spending_tool(question)

    function_calls = response.function_calls or []

    if not function_calls:
        raise RuntimeError(
            "Gemini did not return a finance tool call."
        )

    if len(function_calls) != 1:
        raise RuntimeError(
            "Expected exactly one finance tool call."
        )

    function_call = function_calls[0]

    # 2. Allow only the tool implemented by this service.
    if function_call.name != "get_category_spending":
        raise ValueError("Unsupported finance tool.")

    arguments = function_call.args or {}

    # 3. Validate arguments before executing the function.
    category = arguments.get("category")
    month = arguments.get("month")
    year = arguments.get("year")

    if not isinstance(category, str) or not category.strip():
        raise ValueError("Invalid category returned by Gemini.")

    # bool is a subclass of int in Python, so explicitly reject it.
    if isinstance(month, bool) or not isinstance(month, int):
        raise ValueError("Invalid month returned by Gemini.")

    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError("Invalid year returned by Gemini.")

    # 4. Execute the Python tool using the authenticated user's ID.
    tool_result = get_category_spending(
        db=db,
        user_id=user_id,
        category=category,
        month=month,
        year=year,
    )

    # 5. Send Gemini's original function call and the tool result.
    function_response = types.Content(
        role="user",
        parts=[
            types.Part.from_function_response(
                name=function_call.name,
                response=tool_result,
            )
        ],
    )

    final_response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=[
            question,
            response.candidates[0].content,
            function_response,
        ],
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are a personal finance assistant. "
                "Explain the supplied tool result clearly. "
                "Use the returned total as the source of truth. "
                "Do not invent financial figures. "
                "If spending is zero, say no matching expenses "
                "were found for the selected category and period."
            ),
        ),
    )

    # 6. Return both the calculated result and the explanation.
    return {
        "question": question,
        "tool_name": function_call.name,
        "tool_result": tool_result,
        "answer": final_response.text,
    }