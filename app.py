from flask import Flask, render_template, request, redirect, url_for, session, send_file
import qrcode
import os
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Folder for storing QR codes
QR_FOLDER = "static/qr_codes"
if not os.path.exists(QR_FOLDER):
    os.makedirs(QR_FOLDER)

# Path to the attendance Excel file
ATTENDANCE_FILE = 'attendance.xlsx'

# Dummy users for login
users = {
    'admin': {'password': 'adminpass', 'is_admin': True},
    'student': {'password': 'studentpass', 'is_admin': False},
}

# Initialize attendance file
def initialize_attendance_file():
    if not os.path.exists(ATTENDANCE_FILE):
        df = pd.DataFrame(columns=["Roll Number", "PRN", "Name", "Attendance", "Date", "Time"])
        df.to_excel(ATTENDANCE_FILE, index=False)

initialize_attendance_file()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)
        if user and user['password'] == password:
            session['user_id'] = username
            session['is_admin'] = user['is_admin']
            return redirect(url_for('dashboard'))
        return "Invalid credentials!", 400
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if username in users:
            return "User already exists!", 400
        if password != confirm_password:
            return "Passwords do not match!", 400
        users[username] = {'password': password, 'is_admin': False}
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    username = session['user_id']
    is_admin = session['is_admin']
    if is_admin:
        return render_template('dashboard.html', username=username)
    return render_template('dashboard.html', username=username)

@app.route('/generate_qr', methods=['GET', 'POST'])
def generate_qr():
    if request.method == 'POST':
        roll_number = request.form['roll_number']
        prn = request.form['prn']
        name = request.form['name']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        qr_data = f"{roll_number},{prn},{name},{timestamp}"
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        filename = f"{roll_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        filepath = os.path.join(QR_FOLDER, filename)
        img.save(filepath)
        return render_template('generate_qr.html', qr_filename=filename)
    return render_template('generate_qr.html')

@app.route('/scan_qr', methods=['GET', 'POST'])
def scan_qr():
    if request.method == 'POST':
        qr_data = request.form['qr_data']
        try:
            roll_number, prn, name, timestamp = qr_data.split(',')
            timestamp = datetime.now()
            df = pd.DataFrame([{
                "Roll Number": roll_number,
                "PRN": prn,
                "Name": name,
                "Attendance": "Present",
                "Date": timestamp.date(),
                "Time": timestamp.strftime('%H:%M:%S')
            }])
            with pd.ExcelWriter(ATTENDANCE_FILE, mode="a", engine="openpyxl", if_sheet_exists="overlay") as writer:
                df.to_excel(writer, index=False, header=False)
            return "Attendance marked successfully!"
        except Exception as e:
            return f"Error: {e}", 400
    return render_template('scan_qr.html')

@app.route('/attendance')
def attendance():
    if 'user_id' not in session or not session['is_admin']:
        return redirect(url_for('login'))
    df = pd.read_excel(ATTENDANCE_FILE)
    records = df.to_dict(orient='records')
    return render_template('attendance.html', attendance_data=records)

@app.route('/download_attendance')
def download_attendance():
    return send_file(ATTENDANCE_FILE, as_attachment=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
