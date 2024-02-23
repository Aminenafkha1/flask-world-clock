import logging
import time  # Step 2: Import the time module
from elasticsearch import Elasticsearch
from flask import Flask, request, render_template
import requests

app = Flask(__name__)
es = Elasticsearch(['http://localhost:9200'])  # Adjust host and port as needed

logging.basicConfig(filename='search.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/search", methods=["POST"])
def search():
    # Step 3: Measure latency
    start_time = time.time()

    # Get the search query
    query = request.form["q"]

    # Pass the search query to the Nominatim API to get a location
    location = requests.get(
        "https://nominatim.openstreetmap.org/search",
        {"q": query, "format": "json", "limit": "1"},
    ).json()

    # If a location is found, pass the coordinate to the Time API to get the current time
    if location:
        coordinate = [location[0]["lat"], location[0]["lon"]]

        time_api_response = requests.get(
            "https://timeapi.io/api/Time/current/coordinate",
            {"latitude": coordinate[0], "longitude": coordinate[1]},
        )

        # Step 4: Log metrics into a file
        latency = time.time() - start_time
        logging.info(f"Search Query: {query}, Latency: {latency} seconds")

        es.index(index='search_metrics', body={'query': query, 'latency': latency, 'timestamp': time.time()})

        return render_template("success.html", location=location[0], time=time_api_response.json())

    # If a location is NOT found, return the error page
    else:
        # Step 4: Log metrics into a file
        latency = time.time() - start_time
        logging.info(f"Search Query: {query}, Latency: {latency} seconds (Failed)")
        
        es.index(index='search_metrics', body={'query': query, 'latency': latency, 'timestamp': time.time(), 'status': 'failed'})

        return render_template("fail.html")

if __name__ == "__main__":
    app.run(debug=True)
