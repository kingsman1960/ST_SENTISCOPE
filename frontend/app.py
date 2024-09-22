from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# Assuming your Streamlit app is running on this port
STREAMLIT_URL = "http://localhost:8501"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze_sector', methods=['POST'])
def analyze_sector():
    sector = request.form['sector']
    try:
        # Make a request to your Streamlit backend
        response = requests.post(f"{STREAMLIT_URL}/analyze_sector", json={"sector": sector})
        response.raise_for_status()  # Raise an exception for bad responses
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze_article', methods=['POST'])
def analyze_article():
    article = request.form['article']
    try:
        # Make a request to your Streamlit backend
        response = requests.post(f"{STREAMLIT_URL}/analyze_article", json={"article": article})
        response.raise_for_status()  # Raise an exception for bad responses
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_sectors')
def get_sectors():
    # This should match the sectors in your Streamlit app
    sectors = ['Banking', 'Technology', 'Healthcare', 'Energy', 'Retail']
    return jsonify(sectors)

if __name__ == '__main__':
    # Ensure the NEWSAPI_KEY is set
    if 'NEWSAPI_KEY' not in os.environ:
        print("Warning: NEWSAPI_KEY environment variable is not set.")
    app.run(debug=True)