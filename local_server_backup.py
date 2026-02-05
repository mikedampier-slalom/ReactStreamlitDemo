#!/usr/bin/env python3
"""
Local development server that simulates AWS Lambda + API Gateway
Run this instead of SAM local when Docker is unavailable
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import sys
import os

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lambda'))

from app import lambda_handler

app = Flask(__name__)
CORS(app)  # Enable CORS for React app

@app.route('/hello', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def hello():
    """Simulate API Gateway + Lambda invocation"""
    
    # Create a mock API Gateway event
    event = {
        "body": request.get_data(as_text=True) if request.data else None,
        "resource": "/hello",
        "path": "/hello",
        "httpMethod": request.method,
        "isBase64Encoded": False,
        "queryStringParameters": dict(request.args) if request.args else None,
        "pathParameters": None,
        "stageVariables": None,
        "headers": dict(request.headers),
        "requestContext": {
            "accountId": "123456789012",
            "resourceId": "123456",
            "stage": "local",
            "requestId": "local-request",
            "identity": {
                "sourceIp": request.remote_addr
            },
            "resourcePath": "/hello",
            "httpMethod": request.method,
            "apiId": "local"
        }
    }
    
    # Call Lambda handler
    response = lambda_handler(event, None)
    
    # Parse Lambda response
    status_code = response.get('statusCode', 200)
    headers = response.get('headers', {})
    body = response.get('body', '{}')
    
    # Return Flask response
    return body, status_code, headers


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Local Lambda Development Server")
    print("=" * 60)
    print(f"📍 Server running at: http://127.0.0.1:3000")
    print(f"🔗 Test endpoint: http://127.0.0.1:3000/hello")
    print(f"💡 Press CTRL+C to quit")
    print("=" * 60)
    
    app.run(host='127.0.0.1', port=3000, debug=True)
