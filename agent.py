# agent.py
import os
import re
import json
import sqlite3
from openai import OpenAI
from dotenv import load_dotenv
from database import run_query

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

DESTRUCTIVE_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|ATTACH)\b",
    re.IGNORECASE,
)

SYSTEM_PROMPT = f"""You are a SQL expert assistant for a SQLite database.
Your job is to convert natural language questions into SQL queries and explain the results.

DATABASE SCHEMA:
{{SCHEMA}}

TODAY'S DATE: Use DATE('now') in SQLite for any relative date calculations.

RULES:
1. Only generate SELECT statements. Never INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or CREATE.
2. Always use proper JOINs when data spans multiple tables.
3. Revenue = SUM(order_items.quantity * order_items.unit_price) for completed orders only.
4. Return your response as valid JSON in exactly this format:
{{
  "sql": "SELECT ...",
  "explanation": "A clear plain-English explanation of what the query does and what the results mean."
}}
5. If the question is a follow-up, use the conversation history to resolve references like 'them', 'those', 'that country'.
6. If the question cannot be answered from this database, set sql to null and explain why.
7. Do not wrap the JSON in markdown code blocks. Return raw JSON only.
8. If a table or column name is a SQL reserved word or contains spaces (e.g. "Order", "Order Details"), wrap it in double quotes in the generated SQL.
9. Before finalizing the query, double-check that every table referenced in SELECT, WHERE, or ORDER BY clauses is also present in a FROM or JOIN clause. Add any missing JOINs.
"""


def is_destructive(sql: str) -> bool:
    return bool(DESTRUCTIVE_PATTERN.search(sql))


def ask(question, history, db_path, schema) -> dict:

    history_text = ""
    for turn in history:
        history_text += f"User: {turn['question']}\nAssistant: {turn['answer']}\n\n"

    prompt = SYSTEM_PROMPT.replace("{{SCHEMA}}", schema)

    full_prompt = prompt
    if history_text:
        full_prompt += f"\n\nConversation so far:\n{history_text}"
    full_prompt += f"\n\nUser question: {question}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "sql": None,
            "explanation": "The model returned an unexpected response. Please try rephrasing.",
            "results": [],
            "error": raw,
        }

    sql = parsed.get("sql")
    explanation = parsed.get("explanation", "")

    if sql is None:
        return {"sql": None, "explanation": explanation, "results": []}

    if is_destructive(sql):
        return {
            "sql": sql,
            "explanation": "Blocked: destructive query cannot be executed.",
            "results": [],
            "error": "destructive_query",
        }

    try:
        results = run_query(sql, db_path)
        return {"sql": sql, "explanation": explanation, "results": results}
    except sqlite3.Error as e:
        return {"sql": sql, "explanation": explanation, "results": [], "error": str(e)}