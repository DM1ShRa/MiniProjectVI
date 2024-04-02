from flask import Flask, render_template,redirect, request, jsonify, session, abort, url_for
import joblib
import requests
import pickle
import firebase_admin
import secrets
from firebase_admin import credentials, db
from flask_socketio import SocketIO, emit
import time
import threading
import pandas as pd
import pyrebase
import folium
from folium.plugins import MarkerCluster, HeatMap
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline



secret_key = secrets.token_hex(16)

app = Flask(__name__)
app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = secret_key
socketio = SocketIO(app, cors_allowed_origins='*')

firebase_config = {
    "apiKey": "AIzaSyAtZb6-LRZMpCpPasCbk_vycTcRQ5fl7KA",
    "authDomain": "dpps-23928.firebaseapp.com",
    "databaseURL": "https://dpps-23928-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "dpps-23928",
    "storageBucket": "dpps-23928.appspot.com",
    "messagingSenderId": "114905554074",
    "appId": "1:114905554074:web:d527757221e8fabe115323",
    "measurementId": "G-ES3ZDPZC4F",
}
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
fb = firebase.database()
config = {
  "apiKey": "AIzaSyC_sYbyfyI9l7O5yzMGMltS7Jm051HNDU0",
  "authDomain": "auth-3538a.firebaseapp.com",
  "databaseURL" : "https://auth-3538a-default-rtdb.firebaseio.com/",
  "projectId": "auth-3538a",
  "storageBucket": "auth-3538a.appspot.com",
  "messagingSenderId": "776411640881",
  "appId": "1:776411640881:web:1ffbc1128e7978b2869110"
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

firebaseConfig = {
  "apiKey": "AIzaSyBn-z_lpT8UM4qNViGuaJ0qFmPW9b49n5Y",
  "authDomain": "authorityauth-810cd.firebaseapp.com",
  "databaseURL": "https://authorityauth-810cd-default-rtdb.firebaseio.com",
  "projectId": "authorityauth-810cd",
  "storageBucket": "authorityauth-810cd.appspot.com",
  "messagingSenderId": "414719593107",
  "appId": "1:414719593107:web:399817fc20c85c73649b66"
}
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
authoritydb = firebase.database()

person = {"is_logged_in": False, "name": "", "email": "", "uid": "","DHT":False,"MPU":False,"location":""}
authority={"is_logged_in": False, "name": "", "email": "", "uid": ""}
with open('pipeline_min_temp.pkl', 'rb') as f:
    pipeline_min_temp = pickle.load(f)

with open('pipeline_max_temp.pkl', 'rb') as f:
    pipeline_max_temp = pickle.load(f)

# Function to make predictions
def predict_temperature(input_data):
    min_temp = pipeline_min_temp.predict(input_data)
    max_temp = pipeline_max_temp.predict(input_data)
    return min_temp[0], max_temp[0]

data_path = "/Sensor/DHT/Temperature"
@app.before_request
def before_request():
    if request.endpoint == 'input' and not person["is_logged_in"]:
        return redirect(url_for('login'))
    elif request.endpoint == 'sensors' and not person["is_logged_in"]:
        return redirect(url_for('login'))
    elif request.endpoint == 'dht_sensor' and not person["is_logged_in"]:
        return redirect(url_for('login'))
    elif request.endpoint == 'mpu_sensor' and not person["is_logged_in"]:
        return redirect(url_for('login'))
    elif request.endpoint == 'urdht_sensor' and (not person["is_logged_in"] or not person["DHT"]):
        return redirect(url_for('home'))

@app.route("/login")
def login():
    return render_template("login.html")
@app.route("/authoritylogin")
def authoritylogin():
    return render_template("authority_login.html")

#Sign up/ Register
@app.route("/signup")
def signup():
    return render_template("signup.html")
@app.route("/authoritysignup")
def authosignup():
    return render_template("authority_signup.html")

@app.route('/authorityHome')
def authoHome():
    if authority["is_logged_in"] == True:
        return render_template("authority_home.html",authority=authority)
    else:
        return redirect(url_for('authoritylogin'))
@socketio.on('alert_clicked')
def handle_alert():
    message = "There is an Emergency!"
    emit('alert_message', message, broadcast=True)
@socketio.on('emergency_alert')
def handle_emergencyalert(message):
    emit('emergency_alert', message, broadcast=True)
@socketio.on('temperature_alert')
def handle_temperature_alert(data):
    
    temperature = data.get('temperature')
    user_latitude = person.get("latitude")
    user_longitude = person.get("longitude")

    emit('temperature_alert', {'temperature': temperature, 'user_latitude': user_latitude,'user_longitude':user_longitude}, broadcast=True)
@app.route("/authorityresult", methods = ["POST", "GET"])
def authoresult():
    if request.method == "POST":
        result = request.form
        email = result["email"]
        password = result["pass"]
        try:
            govtAuthority = auth.sign_in_with_email_and_password(email, password)
            if govtAuthority is None:
                raise Exception("Authentication failed")
            global authority
            authority["is_logged_in"] = True
            authority["email"] = govtAuthority["email"]
            authority["uid"] = govtAuthority["localId"]
            data = authoritydb.child("authorities").get()
            authority["name"] = data.val()[authority["uid"]]["name"]
            return redirect(url_for('authoHome'))
        except Exception as e:
            print("Error occurred during authority login:", e)
            return redirect(url_for('authoritylogin'))
    else:
        if authority["is_logged_in"]:
            return redirect(url_for('authoHome'))
        else:
            return redirect(url_for('authoritylogin'))
@app.route("/authorityregister", methods=["POST", "GET"])
def authorityregister():
    if request.method == "POST":  # Only listen to POST
        result = request.form  
        email = result["authemail"]
        password = result["authpass"]
        name = result["authname"]
        try:
           
            auth.create_user_with_email_and_password(email, password)
           
            govtAuth = auth.sign_in_with_email_and_password(email, password)
            # Add data to global person
            global authority
            authority["is_logged_in"] = True
            authority["email"] = govtAuth["email"]
            authority["uid"] = govtAuth["localId"]
            authority["name"] = name
            # Append data to the firebase realtime database
            data = {"name": name, "email": email}
            authoritydb.child("authorities").child(authority["uid"]).set(data)
            # Go to welcome page
            return redirect(url_for('authoHome'))
        except Exception as e:
            # Print out the error for debugging
            print("Error occurred during registration:", e)
            # If there is any error, redirect to register
            return redirect(url_for('authorityregister'))

    else:
        if authority["is_logged_in"] == True:
            return redirect(url_for('authoHome'))
        else:
            return redirect(url_for('authorityregister'))

@app.route('/authlogout')
def authlogout():
    global authority
    authority["is_logged_in"] = False
    authority["name"] = ""
    authority["email"] = ""
    authority["uid"] = ""
    return redirect(url_for('authoritylogin'))
@app.route('/')
def home():
    if person["is_logged_in"] == True:
        return render_template('index.html', person=person)
    else:
        return redirect(url_for('login'))

@app.route("/result", methods = ["POST", "GET"])
def result():
    if request.method == "POST":        #Only if data has been posted
        result = request.form           #Get the data
        email = result["email"]
        password = result["pass"]
        try:
            #Try signing in the user with the given information
            user = auth.sign_in_with_email_and_password(email, password)
            #Insert the user data in the global person
            global person
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            #Get the name of the user
            data = db.child("users").get()
            person["name"] = data.val()[person["uid"]]["name"]
            person["DHT"]=data.val()[person["uid"]]["DHT"]
            person["longitude"]=data.val()[person["uid"]]["longitude"]
            person["latitude"]=data.val()[person["uid"]]["latitude"]
            #Redirect to welcome page
            return redirect(url_for('home'))
        except Exception as e:
            #If there is any error, redirect back to login
            print("Error occurred during login:", e)
            return redirect(url_for('login'))
    else:
        if person["is_logged_in"] == True:
            return redirect(url_for('home'))
        else:
            return redirect(url_for('login'))

#If someone clicks on register, they are redirected to /register
@app.route("/register", methods = ["POST", "GET"])
def register():
    if request.method == "POST":        #Only listen to POST
        result = request.form           #Get the data submitted
        email = result["email"]
        password = result["pass"]
        name = result["name"]
        try:
            #Try creating the user account using the provided data
            auth.create_user_with_email_and_password(email, password)
            #Login the user
            user = auth.sign_in_with_email_and_password(email, password)
            #Add data to global person
            global person
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            person["name"] = name
            person["DHT"]=True
            person["MPU"]=False
            #Append data to the firebase realtime database
            data = {"name": name, "email": email,"DHT":True,"MPU":False}
            db.child("users").child(person["uid"]).set(data)
            #Go to welcome page
            return redirect(url_for('home'))
        except:
            #If there is any error, redirect to register
            return redirect(url_for('register'))

    else:
        if person["is_logged_in"] == True:
            return redirect(url_for('home'))
        else:
            return redirect(url_for('register'))
        
@app.route('/logout')
def logout():
    global person
    person["is_logged_in"] = False
    person["name"] = ""
    person["email"] = ""
    person["uid"] = ""
    return redirect(url_for('login'))

@app.route('/realtime_data')
def realtime_data():
    # Simulated data fetching from Firebase (replace this with your actual data retrieval)
    data = {"timestamp": int(time.time()), "value": get_updated_value()}
    return jsonify(data)

def update_data():
    while True:
        # Fetch and update data every 3 seconds
        data = {"timestamp": int(time.time()), "value": get_updated_value()}
        # Simulated data update to Firebase (replace this with your actual data update)
        time.sleep(3)

def get_updated_value():
    data = fb.child("/Sensor/DHT/HeatIndex").get().val()
    return data

@app.route('/input_fields')
def input():
    return render_template('input_fields.html', person=person)
@app.route('/sensors')
def sensors():
    return render_template('sensors.html', person=person)
@app.route('/dht_sensor')
def dht_sensor():
    return render_template('dhtSensor.html', person=person)
@app.route('/mpu_sensor')
def mpu_sensor():
    return render_template('mpuSensor.html', person=person)
@app.route('/urDHT_sensor')
def urdht_sensor():
    return render_template('yourSensor_DHT.html', person=person)

@app.route('/predict', methods=['POST'])
def predict():
    # Get input data from the request
    if request.method == 'POST':
        temp9am = float(request.form['temp9am'])
        temp3pm = float(request.form['temp3pm'])
        humidity9am = float(request.form['humidity9am'])
        humidity3pm = float(request.form['humidity3pm'])
        month = int(request.form['month'])
        season = request.form['season']

        # Convert season to one-hot encoding
        season_mapping = {'Fall': [1, 0, 0, 0], 'Spring': [0, 1, 0, 0], 'Summer': [0, 0, 1, 0], 'Winter': [0, 0, 0, 1]}
        season_encoded = season_mapping[season]

        # Prepare input data for prediction
        input_data = pd.DataFrame({
            'Temp9am': [temp9am],
            'Temp3pm': [temp3pm],
            'Humidity9am': [humidity9am],
            'Humidity3pm': [humidity3pm],
            'Month': [month],
            'Season_Fall': [season_encoded[0]],
            'Season_Spring': [season_encoded[1]],
            'Season_Summer': [season_encoded[2]],
            'Season_Winter': [season_encoded[3]]
        })

        # Make predictions
        min_temp, max_temp = predict_temperature(input_data)

        return f'<h3>Predicted Min Temperature: {min_temp:.2f}</h3><h3>Predicted Max Temperature: {max_temp:.2f}</h3>'
    
if __name__ == '__main__':
    # Start a thread for updating data in the background
    data_update_thread = threading.Thread(target=update_data)
    data_update_thread.start()
    # Run the Flask app
    socketio.run(app, debug=True,allow_unsafe_werkzeug=True)
