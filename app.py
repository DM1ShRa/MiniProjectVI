from flask import Flask, render_template,redirect, request, jsonify, session, abort, url_for
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

app = Flask(__name__)

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

person = {"is_logged_in": False, "name": "", "email": "", "uid": ""}

# Removed Firebase initialization and authentication code
# Removed 'db' object since it's not used

data_path = "/Sensor/DHT/Temperature"

@app.route("/login")
def login():
    return render_template("login.html")

#Sign up/ Register
@app.route("/signup")
def signup():
    return render_template("signup.html")

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
            #Redirect to welcome page
            return redirect(url_for('home'))
        except:
            #If there is any error, redirect back to login
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
            #Append data to the firebase realtime database
            data = {"name": name, "email": email}
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
    # Simulated data fetching from Firebase (replace this with your actual data retrieval)
    return 25.0  # Replace with your logic to get the updated value

@app.before_request
def before_request():
    if request.endpoint == 'input' and not person["is_logged_in"]:
        # Redirect to login page if not logged in
        return redirect(url_for('login'))

@app.route('/input_fields')
def input():
    return render_template('input_fields.html', person=person)
@app.before_request
def before_request():
    if request.endpoint == 'sensors' and not person["is_logged_in"]:
        # Redirect to login page if not logged in
        return redirect(url_for('login'))
@app.route('/sensors')
def sensors():
    return render_template('sensors.html', person=person)
@app.before_request
def before_request():
    if request.endpoint == 'dht_sensor' and not person["is_logged_in"]:
        # Redirect to login page if not logged in
        return redirect(url_for('login'))
@app.route('/dht_sensor')
def dht_sensor():
    return render_template('dhtSensor.html', person=person)

@app.before_request
def before_request():
    if request.endpoint == 'mpu_sensor' and not person["is_logged_in"]:
        # Redirect to login page if not logged in
        return redirect(url_for('login'))
@app.route('/mpu_sensor')
def mpu_sensor():
    return render_template('mpuSensor.html', person=person)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get user input from the form
        temperature = float(request.form['temperature_celsius'])
        country = request.form['country']
        region = request.form['region']

        # Load your dataset
        data = pd.read_csv("miniProjectData.csv")

        # Train the machine learning model
        X = data[['latitude', 'longitude', 'temperature_celsius', 'country', 'region']]
        y = data['Alert']

        categorical_columns = ['country', 'region']
        preprocessor = ColumnTransformer(
            transformers=[
                ('cat', OneHotEncoder(), categorical_columns),
            ],
            remainder='passthrough'
        )

        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', RandomForestClassifier(random_state=42))
        ])

        pipeline.fit(X, y)

        # Make prediction using the trained model
        user_input = pd.DataFrame({
            'country': [country],
            'region': [region],
            'temperature_celsius': [temperature],
            'latitude': [0],  # Replace with the user's latitude
            'longitude': [0]  # Replace with the user's longitude
        })

        prediction = pipeline.predict(user_input)[0]

        # Create a map using Folium
        map_center = [data['latitude'].mean(), data['longitude'].mean()]
        my_map = folium.Map(location=map_center, zoom_start=6)

        # Create MarkerCluster for better visualization of markers
        marker_cluster = MarkerCluster().add_to(my_map)

        # Add markers for each data point with popup information
        for i, row in data.iterrows():
            folium.Marker([row['latitude'], row['longitude']],
                          popup=f"Location: {row['location_name']}<br>Temperature: {row['temperature_celsius']}°C<br> Alert: {row['Alert']}").add_to(marker_cluster)

        # Create a HeatMap layer based on alert categories
        heat_data = [[row['latitude'], row['longitude']] for i, row in data.iterrows()]
        HeatMap(heat_data).add_to(my_map)

        # Save the map as an HTML file
        my_map.save('templates/map_with_heatmap.html')

        return render_template('index.html', prediction=prediction)

    except Exception as e:
        return render_template('error.html', error=str(e))
    
if __name__ == '__main__':
    # Start a thread for updating data in the background
    data_update_thread = threading.Thread(target=update_data)
    data_update_thread.start()
    # Run the Flask app
    app.run(debug=True)
