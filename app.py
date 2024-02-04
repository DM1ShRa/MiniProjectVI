from flask import Flask, render_template, request, jsonify
from pyrebase import pyrebase
import time
import threading
import pandas as pd
import folium
import sklearn
from folium.plugins import MarkerCluster, HeatMap
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
import time
import threading
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

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

data_path = "/Sensor/DHT/Temperature"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/realtime_data')
def realtime_data():
    data = db.child(data_path).get().val()
    return jsonify(data)

def update_data():
    while True:
        # Fetch and update data every 3 seconds
        data = {"timestamp": int(time.time()), "value": get_updated_value()}
        db.child(data_path).set(data)
        time.sleep(3)

def get_updated_value():
    data = db.child("/Sensor/DHT/Temperature/value").get().val()
    return data


@app.route('/input_fields')
def input():
    return render_template('input_fields.html')

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
