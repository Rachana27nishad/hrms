
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
import re
import os

app = Flask(__name__)
CORS(app)

# ---------- DATABASE CONNECTION ----------

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME")
    )

@app.route("/")
def home():
    return render_template("index.html")

# ---------- EMPLOYEE APIs ----------

@app.route("/employees", methods=["POST"])
def add_employee():
    data = request.json

    emp_id = data.get("emp_id")
    name = data.get("name")
    email = data.get("email")
    department = data.get("department")

    if not all([emp_id, name, email, department]):
        return jsonify({"error": "All fields required"}), 400

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"error": "Invalid email"}), 400

    try:
        db = get_db()
        cur = db.cursor()

        cur.execute(
            "INSERT INTO employees (emp_id, name, email, department) VALUES (%s,%s,%s,%s)",
            (emp_id, name, email, department)
        )
        db.commit()

        return jsonify({"message": "Employee added successfully"}), 201

    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/employees", methods=["GET"])
def get_employees():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM employees")
    return jsonify(cur.fetchall())


@app.route("/employees/<emp_id>", methods=["DELETE"])
def delete_employee(emp_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM employees WHERE emp_id=%s", (emp_id,))
    db.commit()

    if cur.rowcount == 0:
        return jsonify({"error": "Employee not found"}), 404

    return jsonify({"message": "Employee deleted"})


@app.route("/employees/<emp_id>", methods=["PUT"])
def update_employee(emp_id):
    data = request.json
    name = data.get("name")
    email = data.get("email")
    department = data.get("department")

    if not all([name, email, department]):
        return jsonify({"error": "All fields required"}), 400

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "UPDATE employees SET name=%s, email=%s, department=%s WHERE emp_id=%s",
        (name, email, department, emp_id)
    )
    db.commit()

    return jsonify({"message": "Employee updated"})


# ---------- ATTENDANCE APIs ----------

@app.route("/attendance", methods=["POST"])
def mark_attendance():
    data = request.json

    emp_id = data.get("emp_id")
    date = data.get("date")
    status = data.get("status")

    if not all([emp_id, date, status]):
        return jsonify({"error": "All fields required"}), 400

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO attendance (emp_id, date, status) VALUES (%s,%s,%s)",
        (emp_id, date, status)
    )
    db.commit()

    return jsonify({"message": "Attendance marked"}), 201

@app.route("/dashboard", methods=["GET"])
def dashboard_data():
    from datetime import date
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) FROM employees")
    total_employees = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM attendance")
    total_attendance = cur.fetchone()[0]

    today = date.today()
    cur.execute("SELECT COUNT(*) FROM attendance WHERE date=%s AND status='Present'", (today,))
    present_today = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM attendance WHERE date=%s AND status='Absent'", (today,))
    absent_today = cur.fetchone()[0]

    return jsonify({
        "total_employees": total_employees,
        "total_attendance": total_attendance,
        "present_today": present_today,
        "absent_today": absent_today
    })

@app.route("/attendance/<emp_id>", methods=["GET"])
def get_attendance(emp_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute(
        "SELECT date, status FROM attendance WHERE emp_id=%s",
        (emp_id,)
    )
    return jsonify(cur.fetchall())


if __name__ == "__main__":
    app.run(debug=True)
