from flask import Flask, render_template
from flask import request, redirect, flash, session
from flask_bcrypt import Bcrypt
from flask_session import Session
from models import users_collection, passengers_collection
from flight_agent import get_flights
from flask import send_file
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import pyotp
import qrcode
import os
import random
from ai_agent import get_ai_response

app = Flask(__name__)

app.secret_key = "secretkey"
app.config["SESSION_TYPE"] = "filesystem"

Session(app)
bcrypt = Bcrypt(app)

@app.route('/')

def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])

def register():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user = users_collection.find_one({
            "username": username
        })

        if existing_user:
            flash('Username already exists', 'danger')
            return redirect('/register')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        secret = pyotp.random_base32()

        user_data = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "secret": secret
        }

        users_collection.insert_one(user_data)

        totp_uri = pyotp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name="Flight AI"
        )

        qr = qrcode.make(totp_uri)

        qr_folder = os.path.join('static', 'qr_codes')

        if not os.path.exists(qr_folder):
            os.makedirs(qr_folder)

        qr_path = os.path.join(qr_folder, f'{username}.png')
        qr.save(qr_path)

        image_path = f'/static/qr_codes/{username}.png'

        flash('Registration Successful', 'success')

        return render_template('register.html', qr_image=image_path)

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])

def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = users_collection.find_one({
            "username": username
        })

        if user and bcrypt.check_password_hash(user['password'], password):
            session['username'] = username
            session['email'] = user['email']
            return redirect('/verify')
        flash('Invalid Credentials', 'danger')

    return render_template('login.html')


@app.route('/verify', methods=['GET', 'POST'])

def verify():

    username = session.get('username')

    user = users_collection.find_one({
        "username": username
    })

    if not user:
        flash('User not found', 'danger')
        return redirect('/login')

    totp = pyotp.TOTP(user['secret'])

    if request.method == 'POST':

        otp = request.form['otp']

        if totp.verify(otp):

            session['logged_in'] = True
            flash('Login Successful', 'success')
            return redirect('/dashboard')

        else:
            flash('Invalid OTP', 'danger')

    return render_template('verify.html')


@app.route('/dashboard')

def dashboard():

    if not session.get('logged_in'):
        return redirect('/login')

    return render_template('dashboard.html')


@app.route('/flight')

def flight():
    return render_template('flight.html')


@app.route('/chatbot', methods=['GET', 'POST'])

def chatbot():

    response = ""

    if request.method == 'POST':
        user_message = request.form['message']
        response = get_ai_response(user_message)

    return render_template('chatbot.html', response=response)


booked_seats = ['A1', 'A2', 'C2', 'D3']


@app.route('/book', methods=['GET', 'POST'])
def book():

    global booked_seats

    if request.method == 'POST':

        passenger_name = request.form['passenger_name']
        passenger_age = request.form['passenger_age']
        gender = request.form['gender']
        passenger_type = request.form['passenger_type']
        travel_class = request.form['travel_class']
        payment_method = request.form['payment_method']

        # ✅ FIX: multiple seats
        selected_seats = request.form.getlist('selected_seat')

        session['passenger_name'] = passenger_name
        session['passenger_age'] = passenger_age
        session['gender'] = gender
        session['travel_class'] = travel_class
        session['payment_method'] = payment_method

        # store all seats
        session['selected_seats'] = selected_seats

        # ❌ check all seats before booking
        for seat in selected_seats:
            if seat in booked_seats:
                flash(f'Seat {seat} already booked', 'danger')
                return redirect('/book')

        # ✅ book all seats
        for seat in selected_seats:
            booked_seats.append(seat)

        return render_template(
            'payment.html',
            passenger_name=passenger_name,
            passenger_age=passenger_age,
            gender=gender,
            passenger_type=passenger_type,
            travel_class=travel_class,
            payment_method=payment_method,
            selected_seats=selected_seats   # FIXED HERE
        )

    return render_template('book.html', booked_seats=booked_seats)

@app.route('/logout')

def logout():

    session.clear()
    flash('Logged out successfully', 'info')
    return redirect('/')


@app.route('/results', methods=['POST'])
def results():

    source = request.form['source']
    destination = request.form['destination']
    date = request.form['date']
    time = request.form['time']

    session['source'] = source
    session['destination'] = destination
    session['date'] = date
    session['time'] = time

    flights = get_flights(source, destination, date)

    return render_template(
        'results.html',
        flights=flights,
        source=source,
        destination=destination,
        date=date
    )


@app.route('/payment')

@app.route('/payment_success', methods=['POST'])
def payment_success():

    ticket_id = 'FL' + str(random.randint(100000, 999999))
    pnr = 'PNR' + str(random.randint(100000, 999999))

    passenger_data = {
        "ticket_id": ticket_id,
        "pnr": pnr,
        "name": session.get('passenger_name'),
        "age": session.get('passenger_age'),
        "gender": session.get('gender'),
        "source": session.get('source'),
        "destination": session.get('destination'),
        "date": session.get('date'),
        "time": session.get('time'),
        "travel_class": session.get('travel_class'),
        "seats": session.get('selected_seats'),
        "payment_method": session.get('payment_method'),
        "amount": 5500
    }

    passengers_collection.insert_one(passenger_data)

    qr_data = f"""
Name: {session.get('passenger_name')}
PNR: {pnr}
Ticket: {ticket_id}
From: {session.get('source')}
To: {session.get('destination')}
Date: {session.get('date')}
Seat: {', '.join(session.get('selected_seats', []))}
"""

    print("========== QR DATA ==========")
    print(qr_data)
    print("=============================")

    qr = qrcode.QRCode(
        version=4,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=6
    )

    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    qr_filename = f"ticket_{pnr}.png"
    img.save(os.path.join("static", qr_filename))

    return render_template(
        'ticket.html',
        name=session.get('passenger_name'),
        age=session.get('passenger_age'),
        gender=session.get('gender'),
        source=session.get('source'),
        destination=session.get('destination'),
        date=session.get('date'),
        time=session.get('time'),
        travel_class=session.get('travel_class'),
        seat=', '.join(session.get('selected_seats', [])),
        payment_method=session.get('payment_method'),
        amount='5500',
        ticket_id=ticket_id,
        pnr=pnr,
        qr_image=qr_filename
    )
@app.route("/trip-planner")
def trip_planner():

    if not session.get('logged_in'):
        return redirect('/login')

    return render_template("trip_planner.html")
@app.route("/generate-trip", methods=["POST"])
def generate_trip():

    source = request.form["source"]
    destination = request.form["destination"]
    budget = request.form["budget"]
    days = request.form["days"]

    prompt = f"""
    Create a detailed travel plan.

    Source: {source}
    Destination: {destination}
    Budget: ₹{budget}
    Days: {days}

    Give:
    1. Best way to travel
    2. Estimated expenses
    3. Famous tourist places
    4. Day-wise itinerary
    5. Food recommendations
    6. Travel tips
    """

    result = get_ai_response(prompt)

    return render_template(
        "trip_result.html",
        result=result
    )
@app.route('/send-ticket-email', methods=['POST'])
def send_ticket_email():

    email = session.get('email')  # make sure you store email during login/register

    if not email:
        flash("Email not found", "danger")
        return redirect('/ticket')

    ticket_info = f"""
    Name: {session.get('passenger_name')}
    From: {session.get('source')}
    To: {session.get('destination')}
    Date: {session.get('date')}
    Seats: {', '.join(session.get('selected_seats', []))}
    """

    msg = MIMEMultipart()
    msg['Subject'] = "Your Flight Ticket"
    msg['From'] = "your_email@gmail.com"
    msg['To'] = email

    msg.attach(MIMEText(ticket_info, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(
    "varshithasaipasupuleti05@gmail.com",
    "uvmc yrin eart cfvq"
)
        server.send_message(msg)
        server.quit()

        flash("Ticket sent to email successfully!", "success")

    except Exception as e:
     print("EMAIL ERROR:", str(e))
     flash(f"Email Error: {str(e)}", "danger")

    return redirect('/dashboard')
@app.route('/test')
def test():
    return "Flask is working"
@app.route('/send-ticket-email-test')
def send_ticket_email_test():
    return "Email route working"

if __name__ == '__main__':
    app.run(debug=True)