from flask import Flask, render_template, request, redirect, url_for, session ,flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
 

# In-memory databases
users = []  # Doctors and Patients
appointments = []  # Appointment records


# ----------------------------------------
# Home
# ----------------------------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

# ----------------------------------------
# Login
# ----------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        email = request.form['email']
        password = request.form['password']

        user = next((u for u in users if u['email'] == email and u['role'] == role), None)
        if user and check_password_hash(user['password'], password):
            session['user'] = user['email']
            session['role'] = user['role']
            session['name'] = user['name']

            if role == 'patient':
                return redirect(url_for('patient_dashboard'))
            else:
                return redirect(url_for('doctor_dashboard'))
        else:
            return "Invalid credentials", 401

    return render_template('login.html')

# ----------------------------------------
# Signup
# ----------------------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        role = request.form['role']
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        user = {'role': role, 'name': name, 'email': email, 'password': password}

        if role == 'patient':
            user['age'] = request.form.get('age')
            user['gender'] = request.form.get('gender')
        else:
            user['specialization'] = request.form.get('specialization')

        users.append(user)
        return redirect(url_for('login'))

    return render_template('signup.html')

# ----------------------------------------
# Patient Dashboard
# ----------------------------------------
@app.route('/dashboard')
def patient_dashboard():
    if 'user' not in session or session['role'] != 'patient':
        return redirect(url_for('login'))

    specialization_query = request.args.get('specialization', '').lower()
    if specialization_query:
        doctor_list = [u for u in users if u['role'] == 'doctor' and specialization_query in u.get('specialization', '').lower()]
    else:
        doctor_list = [u for u in users if u['role'] == 'doctor']

    return render_template('patient_dashboard.html', doctors=doctor_list, search_query=specialization_query)


# ----------------------------------------
# Book Appointment
# ----------------------------------------
from datetime import datetime

@app.route('/book/<doctor_email>', methods=['GET', 'POST'])
def book(doctor_email):
    if 'user' not in session or session['role'] != 'patient':
        return redirect(url_for('login'))

    doctor = next((u for u in users if u['email'] == doctor_email and u['role'] == 'doctor'), None)

    if request.method == 'POST':
        appointment = {
            'id': str(uuid.uuid4()),
            'patient_email': session['user'],
            'patient_name': session['name'],
            'doctor_email': doctor['email'],
            'doctor_name': doctor['name'],
            'symptoms': request.form['symptoms'],
            'description': request.form['description'],
            'status': 'Pending',
            'prescription': '',
            'booking_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'responded_time': ''
        }
        appointments.append(appointment)
        return redirect(url_for('my_appointments'))

    return render_template('book_appointment.html', doctor=doctor)


# ----------------------------------------
# Doctor Dashboard
# ----------------------------------------
@app.route('/doctor_dashboard')
def doctor_dashboard():
    if 'user' not in session or session['role'] != 'doctor':
        return redirect(url_for('login'))

    my_appointments = [a for a in appointments if a['doctor_email'] == session['user']]
    return render_template('doctor_dashboard.html', appointments=my_appointments)

# ----------------------------------------
# Doctor Responds
# ----------------------------------------
@app.route('/respond/<appointment_id>', methods=['POST'])
def respond(appointment_id):
    if 'user' not in session or session['role'] != 'doctor':
        return redirect(url_for('login'))

    prescription = request.form['prescription']
    for a in appointments:
        if a['id'] == appointment_id:
            a['prescription'] = prescription
            a['status'] = 'Replied'
            a['responded_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break

    return redirect(url_for('doctor_dashboard'))


# ----------------------------------------
# Patient Views Appointments
# ----------------------------------------
@app.route('/my_appointments')
def my_appointments():
    if 'user' not in session or session['role'] != 'patient':
        return redirect(url_for('login'))

    my_appointments = [a for a in appointments if a['patient_email'] == session['user']]
    return render_template('my_appointments.html', appointments=my_appointments)

# ----------------------------------------
# Logout
# ----------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ----------------------------------------
# Run
# ----------------------------------------
# REMOVE app.run() at bottom

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple('0.0.0.0',5000,app)

