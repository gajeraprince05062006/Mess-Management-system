from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql.cursors
import random
from twilio.rest import Client

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flash messages

# Twilio Configuration (Replace with actual credentials)
TWILIO_ACCOUNT_SID = 'AC4e0aa03e7f5f64def50de992f6cca778'
TWILIO_AUTH_TOKEN = '23c559e49fd4bb4478561b1ce5a295df'
TWILIO_PHONE_NUMBER = '+18152835602'

# Admin verification phone number (Fixed)
ADMIN_PHONE_NUMBER = '+917862017545'

# Temporary storage for OTPs (Dictionary)
otp_storage = {}

# Function to connect to MySQL
def get_db_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            port=3307,
            user='root',
            password='',
            db='track_serve',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Function to send OTP via Twilio
def send_otp(fullname, phone, email):
    otp = random.randint(100000, 999999)  # Generate a 6-digit OTP

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message_body = f"🚀 New Signup Request:\n👤 Name: {fullname}\n📞 Phone: {phone}\n✉ Email: {email}\n🔢 OTP: {otp}"

        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=ADMIN_PHONE_NUMBER
        )
        
        print(f"OTP {otp} sent successfully to {ADMIN_PHONE_NUMBER}")
        print(f"Message SID: {message.sid}")

        # Store OTP in memory
        otp_storage['admin_otp'] = otp
    except Exception as e:
        print(f"Failed to send OTP: {e}")

@app.route('/')
def home():
    return render_template('try.html')

@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        phone_no = request.form['phone_no']
        password = request.form['password']

        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                query = "SELECT * FROM admin WHERE phone_no = %s AND password = %s"
                cursor.execute(query, (phone_no, password))
                user = cursor.fetchone()

                if user:
                    return redirect(url_for('dashboard'))  # Successful login
                else:
                    return render_template('admin_login.html', error="Invalid username or password")

            except pymysql.MySQLError as e:
                print(f"Database error: {e}")
                return render_template('admin_login.html', error="Error while checking credentials")
            finally:
                cursor.close()
                connection.close()
        else:
            return render_template('admin_login.html', error="Failed to connect to the database")

    return render_template('admin_login.html')

@app.route('/dashboard')
def dashboard():
    return render_template("admin_dashboard.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form['fullname']
        phone = request.form['phone_no']
        email = request.form['email']
        password = request.form['password']

        # Send OTP with user details to the admin's registered phone
        send_otp(fullname, phone, email)

        # Temporarily store admin details
        otp_storage['admin_details'] = {'fullname': fullname, 'phone': phone, 'email': email, 'password': password}

        flash("OTP sent to admin's registered phone. Please verify.", "info")
        return redirect(url_for('verify_otp'))

    return render_template('signup.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']

        # Validate OTP
        if 'admin_otp' in otp_storage and int(entered_otp) == otp_storage['admin_otp']:
            connection = get_db_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    admin_data = otp_storage['admin_details']

                    sql = "INSERT INTO admin (fullname, phone_no, email_id, password) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, (admin_data['fullname'], admin_data['phone'], admin_data['email'], admin_data['password']))
                    connection.commit()


                except pymysql.MySQLError as e:
                    print(f"Database error: {e}")
                    flash("Database error occurred. Try again!", "danger")

                finally:
                    cursor.close()
                    connection.close()

            # Remove OTP and admin details after successful signup
            del otp_storage['admin_otp']
            del otp_storage['admin_details']

            return redirect(url_for('home'))
        else:
            flash("Invalid OTP. Please try again.", "danger")

    return render_template('verify_otp.html')

@app.route("/menu")
def menu():
    return render_template('menu.html')

if __name__ == '__main__':
    app.run(debug=True)
