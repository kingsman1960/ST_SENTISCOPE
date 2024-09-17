from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Assuming your Streamlit app is running on this port
STREAMLIT_URL = "http://localhost:8501"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    text = request.form['text']
    # Here you would make a request to your Streamlit backend
    # This is a placeholder - you'll need to implement the actual API call
    response = requests.post(f"{STREAMLIT_URL}/analyze", json={"text": text})
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(debug=True)