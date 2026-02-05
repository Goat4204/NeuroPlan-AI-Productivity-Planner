
from flask import Flask, render_template, request, redirect
import sqlite3
import os
import google.generativeai as genai

app = Flask(__name__)


# Ai intrigration (Google gemini)

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

# DATABASE CONNECTION

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# DATABASE INIT

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            priority TEXT NOT NULL,
            estimated_time INTEGER NOT NULL,
            energy_mode TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

init_db()

# AI function (Prompting Ai to take task from database and run the follwoing prompt on it)

def generate_ai_plan(tasks):

    task_text = ""

    for task in tasks:
        task_text += f"""
Task: {task['task_name']}
Priority: {task['priority']}
Estimated Time: {task['estimated_time']} minutes
Energy Level: {task['energy_mode']}
"""

    prompt = f"""
You are an AI productivity planner inside a web application.

Return output EXACTLY in the format below.
Use NEW LINE after every item.
Do NOT combine lines.
Do NOT write paragraphs.
Do NOT act like chatbot.

FORMAT:

DAILY SCHEDULE:
[Time] - [Task Name] - [Priority]
[Time] - [Task Name] - [Priority]

BREAK SUGGESTIONS:
[Break time]
[Break time]

BURNOUT STATUS:
SAFE or OVERLOADED
[Short reason]

PRODUCTIVITY TIPS:
- Tip 1
- Tip 2

Tasks:
{task_text}
"""

    try:
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"AI Planner temporarily unavailable: {str(e)}"



# HOME ROUTE

@app.route("/")
def home():

    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()

    return render_template("index.html", tasks=tasks)


# ADD TASK

@app.route("/add_task", methods=["POST"])
def add_task():

    task_name = request.form["task_name"]
    priority = request.form["priority"]
    estimated_time = request.form["estimated_time"]
    energy_mode = request.form["energy_mode"]

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO tasks (task_name, priority, estimated_time, energy_mode)
        VALUES (?, ?, ?, ?)
    """, (task_name, priority, estimated_time, energy_mode))

    conn.commit()
    conn.close()

    return redirect("/")


# =====================================================
# DELETE TASK
# =====================================================
@app.route("/delete_task/<int:task_id>")
def delete_task(task_id):

    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    return redirect("/")

# GENERATE AI PLAN

@app.route("/generate_plan", methods=["POST"])
def generate_plan():

    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()

    ai_plan = generate_ai_plan(tasks)

    return render_template("index.html", tasks=tasks, ai_plan=ai_plan)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

