from flask import Flask, render_template, request
import pandas as pd
import folium
import sklearn
from folium.plugins import MarkerCluster, HeatMap
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

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
                          popup=f"Temperature: {row['temperature_celsius']}, Alert: {row['Alert']}").add_to(marker_cluster)

        # Create a HeatMap layer based on alert categories
        heat_data = [[row['latitude'], row['longitude']] for i, row in data.iterrows()]
        HeatMap(heat_data).add_to(my_map)

        # Save the map as an HTML file
        my_map.save('templates/map_with_heatmap.html')

        return render_template('result.html', prediction=prediction)

    except Exception as e:
        return render_template('error.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=True)
