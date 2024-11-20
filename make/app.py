from flask import Flask, jsonify, render_template
import json
import os
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

TRACKER_FILE = os.path.join('log', 'index.json')

@app.route('/tracker')
def get_tracker_data():
    try:
        if os.path.exists(TRACKER_FILE):
            with open(TRACKER_FILE, 'r') as file:
                data = json.load(file)
                return jsonify(data)
        else:
            return jsonify({"error": "Tracker file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run main.py as a subprocess
    subprocess.Popen(['python', 'main.py'])
    app.run(debug=True, port=5000)
