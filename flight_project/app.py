from flask import Flask, render_template
from flask import request, redirect
from flask import flash, session

from flask_bcrypt import Bcrypt
from flask_session import Session

from models import users_collection

import pyotp
import qrcode
import os
import random
import qrcode
import random

from ai_agent import get_ai_response

app = Flask(__name__)

app.secret_key = "secretkey"

app.config["SESSION_TYPE"] = "filesystem"

Session(app)

bcrypt = Bcrypt(app)

# =========================
# HOME
# =========================
@app.route('/')
def home():

    return render_template('index.html')


# =========================
# REGISTER
# =========================
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

            flash(
                'Username already exists',
                'danger'
            )

            return redirect('/register')

        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode('utf-8')

        secret = pyotp.random_base32()

        user_data = {

            "username": username,
            "email": email,
            "password": hashed_password,
            "secret": secret
        }

        users_collection.insert_one(user_data)

        # QR CODE
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name="Flight AI"
        )

        qr = qrcode.make(totp_uri)

        qr_folder = os.path.join(
            'static',
            'qr_codes'
        )

        if not os.path.exists(qr_folder):

            os.makedirs(qr_folder)

        qr_path = os.path.join(
            qr_folder,
            f'{username}.png'
        )

        qr.save(qr_path)

        image_path = f'/static/qr_codes/{username}.png'

        flash(
            'Registration Successful',
            'success'
        )

        return render_template(
            'register.html',
            qr_image=image_path
        )

    return render_template('register.html')


# =========================
# LOGIN
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        user = users_collection.find_one({
            "username": username
        })

        if user and bcrypt.check_password_hash(
            user['password'],
            password
        ):

            session['username'] = username

            return redirect('/verify')

        flash(
            'Invalid Credentials',
            'danger'
        )

    return render_template('login.html')


# =========================
# OTP VERIFY
# =========================
@app.route('/verify', methods=['GET', 'POST'])
def verify():

    username = session.get('username')

    user = users_collection.find_one({
        "username": username
    })

    if not user:

        flash(
            'User not found',
            'danger'
        )

        return redirect('/login')

    secret = user['secret']

    totp = pyotp.TOTP(secret)

    if request.method == 'POST':

        otp = request.form['otp']

        current_otp = totp.now()

        print("Entered OTP:", otp)

        print("Generated OTP:", current_otp)

        if otp == current_otp:

            session['logged_in'] = True

            flash(
                'Login Successful',
                'success'
            )

            return redirect('/dashboard')

        else:

            flash(
                'Invalid OTP',
                'danger'
            )

    return render_template('verify.html')


# =========================
# DASHBOARD
# =========================
@app.route('/dashboard')
def dashboard():

    if not session.get('logged_in'):

        return redirect('/login')

    return render_template('dashboard.html')


# =========================
# FLIGHT SEARCH
# =========================
@app.route('/flight')
def flight():
    return render_template('flight.html')

# =========================
# AI CHATBOT
# =========================
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():

    response = ""

    if request.method == 'POST':

        user_message = request.form['message']

        response = get_ai_response(user_message)

    return render_template(
        'chatbot.html',
        response=response
    )


# =========================
# BOOKED SEATS
# =========================
booked_seats = [

    'A1',
    'A2',
    'C2',
    'D3'

]


# =========================
# BOOK FLIGHT
# =========================
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

        selected_seat = request.form['selected_seat']
        session['passenger_name'] = passenger_name
        session['passenger_age'] = passenger_age
        session['gender'] = gender
        session['travel_class'] = travel_class
        session['payment_method'] = payment_method
        session['selected_seat'] = selected_seat
        

        # CHECK ALREADY BOOKED
        if selected_seat in booked_seats:

            flash(
                'Seat already booked',
                'danger'
            )

            return redirect('/book')

        # ADD NEW BOOKED SEAT
        booked_seats.append(selected_seat)

        return render_template(

            'payment.html',

            passenger_name=passenger_name,

            passenger_age=passenger_age,

            gender=gender,

            passenger_type=passenger_type,

            travel_class=travel_class,

            payment_method=payment_method,

            selected_seat=selected_seat
        )
    
    

    return render_template(

        'book.html',

        booked_seats=booked_seats
    )


# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():

    session.clear()

    flash(
        'Logged out successfully',
        'info'
    )

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

    return render_template(
        'results.html',
        source=source,
        destination=destination,
        date=date,
        time=time
    )
@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/payment_success', methods=['POST'])
def payment_success():
    print("Passenger Name =", session.get('passenger_name'))

    name = session.get('passenger_name')
    age = session.get('passenger_age')
    gender = session.get('gender')

    source = session.get('source')
    destination = session.get('destination')
    date = session.get('date')
    time = session.get('time')

    travel_class = session.get('travel_class')
    seat = session.get('selected_seat')
    payment_method = session.get('payment_method')

    ticket_id = 'FL' + str(random.randint(100000,999999))
    pnr = 'PNR' + str(random.randint(100000,999999))
    

    qr_data = f"""
Passenger: {name}
PNR: {pnr}
Ticket ID: {ticket_id}
Source: {source}
Destination: {destination}
Date: {date}
Time: {time}
Seat: {seat}
Class: {travel_class}
"""

    img = qrcode.make(qr_data)
    img.save("static/ticket_qr.png")

    return render_template(
        'ticket.html',

        name=name,
        age=age,
        gender=gender,

        source=source,
        destination=destination,
        date=date,
        time=time,

        travel_class=travel_class,
        seat=seat,
        payment_method=payment_method,

        amount='5500',

        ticket_id=ticket_id,
        pnr=pnr
    )
@app.route('/ticket')
def ticket():

    print("TICKET ROUTE CALLED")

    pnr = "SKY" + str(random.randint(100000,999999))
    print("Passenger Name:", session.get('passenger_name'))

    qr_data = f"""
Passenger: 
PNR: {pnr}
Flight: AI203
Source: Hyderabad
Destination: Delhi
Seat: A12
Date: 15-08-2025
Time: 10:30 AM
"""

    img = qrcode.make(qr_data)

    img.save("static/ticket_qr.png")

    print("QR SAVED SUCCESSFULLY")

    return render_template(
        'ticket.html',
        name="Rahul Kumar",
        email="rahul@gmail.com",
        ticket_id="FL" + str(random.randint(100000,999999)),
        pnr=pnr,
        flight_no="AI203",
        source="Hyderabad",
        destination="Delhi",
        date="15-08-2025",
        time="10:30 AM",
        seat="A12",
        amount="5500"
    )
# =========================
# RUN APP
# =========================
if __name__ == '__main__':

    app.run(debug=True)