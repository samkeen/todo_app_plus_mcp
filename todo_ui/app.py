"""
Flask UI application for the Todo API.
"""

import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# API base URL - defaults to localhost if not set
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


# Custom filter for datetime formatting
@app.template_filter("datetime")
def format_datetime(value):
    """Format a datetime string to a more readable format."""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return value


def handle_api_error(response):
    """Handle API errors and provide flash messages."""
    try:
        error_data = response.json()
        flash(f"Error: {error_data.get('detail', 'Unknown error')}", "error")
    except:
        flash(f"Error: {response.status_code} - {response.reason}", "error")


@app.route("/")
def index():
    """Home page - list all todos."""
    try:
        response = requests.get(f"{API_BASE_URL}/todos")
        if response.status_code == 200:
            todos = response.json()
            return render_template("index.html", todos=todos)
        else:
            handle_api_error(response)
            return render_template("index.html", todos=[])
    except requests.RequestException as e:
        flash(f"API Connection Error: {str(e)}", "error")
        return render_template("index.html", todos=[])


@app.route("/todo/new", methods=["GET", "POST"])
def new_todo():
    """Create a new todo."""
    if request.method == "POST":
        todo_data = {
            "title": request.form.get("title"),
            "description": request.form.get("description", ""),
            "completed": request.form.get("completed") == "on",
        }

        try:
            response = requests.post(f"{API_BASE_URL}/todos", json=todo_data)
            if response.status_code == 201:
                flash("Todo created successfully!", "success")
                return redirect(url_for("index"))
            else:
                handle_api_error(response)
        except requests.RequestException as e:
            flash(f"API Connection Error: {str(e)}", "error")

    return render_template("new.html")


@app.route("/todo/<string:todo_id>")
def view_todo(todo_id):
    """View a specific todo."""
    try:
        response = requests.get(f"{API_BASE_URL}/todos/{todo_id}")
        if response.status_code == 200:
            todo = response.json()
            return render_template("view.html", todo=todo)
        else:
            handle_api_error(response)
            return redirect(url_for("index"))
    except requests.RequestException as e:
        flash(f"API Connection Error: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/todo/<string:todo_id>/edit", methods=["GET", "POST"])
def edit_todo(todo_id):
    """Edit an existing todo."""
    if request.method == "POST":
        todo_data = {
            "title": request.form.get("title"),
            "description": request.form.get("description", ""),
            "completed": request.form.get("completed") == "on",
        }

        # Remove None values
        todo_data = {k: v for k, v in todo_data.items() if v is not None}

        try:
            response = requests.put(f"{API_BASE_URL}/todos/{todo_id}", json=todo_data)
            if response.status_code == 200:
                flash("Todo updated successfully!", "success")
                return redirect(url_for("index"))
            else:
                handle_api_error(response)
        except requests.RequestException as e:
            flash(f"API Connection Error: {str(e)}", "error")

    # Get current todo data for the form
    try:
        response = requests.get(f"{API_BASE_URL}/todos/{todo_id}")
        if response.status_code == 200:
            todo = response.json()
            return render_template("edit.html", todo=todo)
        else:
            handle_api_error(response)
            return redirect(url_for("index"))
    except requests.RequestException as e:
        flash(f"API Connection Error: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/todo/<string:todo_id>/delete", methods=["POST"])
def delete_todo(todo_id):
    """Delete a todo."""
    try:
        response = requests.delete(f"{API_BASE_URL}/todos/{todo_id}")
        if response.status_code == 204:
            flash("Todo deleted successfully!", "success")
        else:
            handle_api_error(response)
    except requests.RequestException as e:
        flash(f"API Connection Error: {str(e)}", "error")

    return redirect(url_for("index"))


@app.route("/todo/<string:todo_id>/toggle", methods=["POST"])
def toggle_todo(todo_id):
    """Toggle the completed status of a todo."""
    try:
        # First get the current todo
        get_response = requests.get(f"{API_BASE_URL}/todos/{todo_id}")
        if get_response.status_code == 200:
            todo = get_response.json()
            # Toggle the completed status
            update_data = {"completed": not todo["completed"]}

            # Update the todo
            update_response = requests.put(f"{API_BASE_URL}/todos/{todo_id}", json=update_data)
            if update_response.status_code == 200:
                new_status = "completed" if update_data["completed"] else "active"
                flash(f"Todo marked as {new_status}!", "success")
            else:
                handle_api_error(update_response)
        else:
            handle_api_error(get_response)
    except requests.RequestException as e:
        flash(f"API Connection Error: {str(e)}", "error")

    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 8001))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    app.run(debug=debug, port=port)
