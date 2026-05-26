from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "mysecretkey123"

def init_db():
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT,
        name TEXT,
        email TEXT,
        password TEXT,
        role TEXT,
        department TEXT,
        address TEXT,
        image TEXT,
        salary TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT,
        prediction TEXT,
        stay_prob REAL,
        leave_prob REAL,
        risk_status TEXT
    )
    """)

    cursor.execute("SELECT * FROM users WHERE role=?", ("admin",))
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO users(employee_id, name, email, password, role, department, address, image, salary)
        VALUES(?,?,?,?,?,?,?,?,?)
        """, ("ADMIN001", "Enterprise Admin", "admin@gmail.com", "admin123", "admin", "Management", "Bangladesh", "default.png", "0"))
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    selected_role = request.form.get('role', 'employee')

    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return render_template("login.html", error="User account not found.")
    if user[4] != password:
        return render_template("login.html", error="Invalid password credentials.")
    if user[5] != selected_role:
        return render_template("login.html", error=f"Access denied for role '{selected_role}'.")

    session['user_id'] = user[0]
    session['name'] = user[2]
    session['role'] = user[5]

    if user[5] == "admin":
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('employee_dashboard'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != "admin":
        return redirect(url_for('login_page'))
    
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE role='admin'")
    admins = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='employee'")
    total_employees = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM predictions WHERE risk_status='High'")
    high_risk = cursor.fetchone()[0]
    
    conn.close()
    return render_template("admin_dashboard.html", employees=admins, total_count=total_employees, high_risk=high_risk, low_risk=(total_employees - high_risk))

@app.route('/admin_employees')
def admin_employees():
    if session.get('role') != "admin":
        return redirect(url_for('login_page'))
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE role='employee'")
    employees = cursor.fetchall()
    conn.close()
    return render_template("admin_employees.html", employees=employees)

@app.route('/add_employee')
def add_employee():
    if session.get('role') != "admin":
        return redirect(url_for('login_page'))
    return render_template("add_employee.html")

@app.route('/add_admin')
def add_admin():
    if session.get('role') != "admin":
        return redirect(url_for('login_page'))
    return render_template("add_admin.html")

@app.route('/save_employee', methods=['POST'])
def save_employee():
    if session.get('role') != "admin":
        return redirect(url_for('login_page'))
    employee_id = request.form['employee_id']
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    role = request.form.get('role', 'employee')
    department = request.form['department']
    address = request.form['address']
    salary = request.form.get('salary', '0')
    
    image = request.files.get('image')
    filename = "default.png"
    if image and image.filename != "":
        os.makedirs("static/uploads", exist_ok=True)
        filename = image.filename
        image.save(os.path.join("static/uploads", filename))
        
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO users(employee_id,name,email,password,role,department,address,image,salary) 
    VALUES(?,?,?,?,?,?,?,?,?)
    """, (employee_id, name, email, password, role, department, address, filename, salary))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard') if role == 'admin' else url_for('admin_employees'))

@app.route('/delete_employee/<int:user_id>')
def delete_employee(user_id):
    if session.get('role') != "admin":
        return redirect(url_for('login_page'))
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE id=?", (user_id,))
    res = cursor.fetchone()
    role_str = res[0] if res else 'employee'
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard') if role_str == 'admin' else url_for('admin_employees'))

@app.route('/employee_dashboard')
def employee_dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login_page'))
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (session['user_id'],))
    employee = cursor.fetchone()
    conn.close()
    return render_template("employee_dashboard.html", employee=employee)

@app.route('/edit_profile/<int:user_id>', methods=['GET', 'POST'])
def edit_profile(user_id):
    if not session.get('user_id'):
        return redirect(url_for('login_page'))
    if session.get('role') != 'admin' and session.get('user_id') != user_id:
        return redirect(url_for('login_page'))
        
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        address = request.form['address']
        salary = request.form.get('salary', '0')
        image = request.files.get('image')
        
        cursor.execute("SELECT role FROM users WHERE id=?", (user_id,))
        tgt_role = cursor.fetchone()[0]
        
        if image and image.filename != "":
            os.makedirs("static/uploads", exist_ok=True)
            filename = image.filename
            image.save(os.path.join("static/uploads", filename))
            cursor.execute("UPDATE users SET name=?, email=?, address=?, image=?, salary=? WHERE id=?", (name, email, address, filename, salary, user_id))
        else:
            cursor.execute("UPDATE users SET name=?, email=?, address=?, salary=? WHERE id=?", (name, email, address, salary, user_id))
        conn.commit()
        conn.close()
        
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard') if tgt_role == 'admin' else url_for('admin_employees'))
        return redirect(url_for('employee_dashboard'))
        
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return render_template("edit_profile.html", user=user)

@app.route('/predict_form')
def predict_form():
    if not session.get('user_id'):
        return redirect(url_for('login_page'))
    
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()
    cursor.execute("SELECT employee_id, name FROM users WHERE role='employee'")
    active_workers = cursor.fetchall()
    conn.close()
    
    return render_template("index.html", active_workers=active_workers)

@app.route('/predict', methods=['POST'])
def predict():
    if not session.get('user_id'):
        return redirect(url_for('login_page'))
        
    target_emp_id = request.form.get('selected_employee_id', 'UNKNOWN')
        
    age = float(request.form.get('Age', 30))
    overtime = float(request.form.get('OverTime', 0))
    job_satisfaction = float(request.form.get('JobSatisfaction', 3))
    
    base_leave = (overtime * 40.0) + (max(0, 50 - age) * 0.8) + ((4 - job_satisfaction) * 10.0)
    leave_prob = round(min(95.0, max(5.0, base_leave)), 2)
    stay_prob = round(100.0 - leave_prob, 2)
    
    if leave_prob > 70.0:
        prediction_text = "Leave"
        risk_status = "High"
    elif leave_prob > 35.0:
        prediction_text = "Leave"
        risk_status = "Medium"
    else:
        prediction_text = "Stay"
        risk_status = "Low"
        
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO predictions(employee_id, prediction, stay_prob, leave_prob, risk_status) 
        VALUES(?,?,?,?,?)
    """, (target_emp_id, prediction_text, stay_prob, leave_prob, risk_status))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login_page'))
    
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, prediction, stay_prob, leave_prob, risk_status, employee_id FROM predictions ORDER BY id ASC")
    data = cursor.fetchall()
    
    if data:
        cursor.execute("SELECT prediction, stay_prob, leave_prob, risk_status, employee_id FROM predictions ORDER BY id DESC LIMIT 1")
        lr = cursor.fetchone()
        last = {"prediction": lr[0], "stay_prob": lr[1], "leave_prob": lr[2], "risk_status": lr[3], "employee_id": lr[4]}
        
        cursor.execute("SELECT AVG(stay_prob), AVG(leave_prob) FROM predictions")
        avg = cursor.fetchone()
        avg_stay = round(avg[0] or 0, 1)
        avg_leave = round(avg[1] or 0, 1)
    else:
        last = None
        avg_stay, avg_leave = 100.0, 0.0
        
    conn.close()
    return render_template("dashboard.html", data=data, last=last, avg_stay=avg_stay, avg_leave=avg_leave)

@app.route('/delete/<int:pred_id>')
def delete_prediction(pred_id):
    if not session.get('user_id'):
        return redirect(url_for('login_page'))
    conn = sqlite3.connect("employees.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM predictions WHERE id=?", (pred_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/company_info')
def company_info():
    if not session.get('user_id'):
        return redirect(url_for('login_page'))
    return render_template("company.html")

if __name__ == "__main__":
    app.run(debug=True)