#!/usr/bin/env python3
"""
Minimal Flask app for Cloud Run testing
"""

import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello from NIE Flask App!"

@app.route('/health')
def health():
    return {"status": "healthy"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask app on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)