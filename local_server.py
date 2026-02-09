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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lambda'))

from app import (
    lambda_handler,
    test_snowflake_handler,
    cortex_analyst_chat_handler,
    execute_sql_snowpark_handler,
)

app = Flask(__name__)
CORS(app)  # Enable CORS for React app

def create_api_gateway_event(path, method):
    """Create a mock API Gateway event"""
    return {
        "body": request.get_data(as_text=True) if request.data else None,
        "resource": path,
        "path": path,
        "httpMethod": method,
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
            "resourcePath": path,
            "httpMethod": method,
            "apiId": "local"
        }
    }

@app.route('/hello', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def hello():
    """Simulate API Gateway + Lambda invocation"""
    event = create_api_gateway_event("/hello", request.method)
    response = lambda_handler(event, None)
    
    status_code = response.get('statusCode', 200)
    headers = response.get('headers', {})
    body = response.get('body', '{}')
    
    return body, status_code, headers


@app.route('/test-snowflake', methods=['GET', 'POST'])
def test_snowflake():
    """Test Snowflake connection endpoint"""
    event = create_api_gateway_event("/test-snowflake", request.method)
    response = test_snowflake_handler(event, None)
    
    status_code = response.get('statusCode', 200)
    headers = response.get('headers', {})
    body = response.get('body', '{}')
    
    return body, status_code, headers


@app.route('/chat', methods=['POST'])
def chat():
    """Cortex Analyst chat endpoint"""
    event = create_api_gateway_event("/chat", request.method)
    response = cortex_analyst_chat_handler(event, None)
    
    status_code = response.get('statusCode', 200)
    headers = response.get('headers', {})
    body = response.get('body', '{}')
    
    return body, status_code, headers


@app.route('/execute-sql', methods=['POST'])
def execute_sql():
    """Execute SQL query endpoint"""
    event = create_api_gateway_event("/execute-sql", request.method)
    response = execute_sql_snowpark_handler(event, None)
    
    status_code = response.get('statusCode', 200)
    headers = response.get('headers', {})
    body = response.get('body', '{}')
    
    return body, status_code, headers


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Local Lambda Development Server")
    print("=" * 60)
    print(f"📍 Server running at: http://127.0.0.1:3000")
    print(f"🔗 Endpoints:")
    print(f"   - http://127.0.0.1:3000/hello")
    print(f"   - http://127.0.0.1:3000/test-snowflake")
    print(f"   - http://127.0.0.1:3000/chat (POST)")
    print(f"   - http://127.0.0.1:3000/execute-sql (POST)")
    print(f"💡 Press CTRL+C to quit")
    print("=" * 60)
    
    app.run(host='127.0.0.1', port=3000, debug=False, threaded=True)
