#!/usr/bin/env python3
"""
Test script for Lambda handlers
This allows testing the Python Lambda functions directly without the Flask server
"""

import json
import os
import sys
from dotenv import load_dotenv

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lambda'))

from app import (
    lambda_handler,
    test_snowflake_handler,
    cortex_analyst_chat_handler,
    execute_sql_handler,
    execute_sql_snowpark_handler
)

# Load environment variables
load_dotenv()

def create_test_event(body=None):
    """Create a mock API Gateway event"""
    return {
        'body': json.dumps(body) if body else None,
        'headers': {'Content-Type': 'application/json'},
        'httpMethod': 'POST',
        'path': '/test',
        'queryStringParameters': None,
        'pathParameters': None,
        'stageVariables': None,
        'requestContext': {},
        'isBase64Encoded': False
    }

def test_basic_lambda():
    """Test 1: Basic Lambda handler"""
    print("=" * 60)
    print("TEST 1: Basic Lambda Handler")
    print("=" * 60)
    
    event = create_test_event()
    try:
        response = lambda_handler(event, None)
        print(f"✅ Status Code: {response['statusCode']}")
        print(f"Response: {response['body']}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    print()

def test_snowflake_connection():
    """Test 2: Snowflake connection"""
    print("=" * 60)
    print("TEST 2: Snowflake Connection")
    print("=" * 60)
    
    event = create_test_event()
    try:
        response = test_snowflake_handler(event, None)
        print(f"✅ Status Code: {response['statusCode']}")
        body = json.loads(response['body'])
        print(f"Message: {body.get('message')}")
        print(f"Snowflake Version: {body.get('snowflake_version')}")
        print(f"Warehouse: {body.get('warehouse')}")
        print(f"Database: {body.get('database')}")
        print(f"Schema: {body.get('schema')}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    print()

def test_cortex_analyst_chat():
    """Test 3: Cortex Analyst chat"""
    print("=" * 60)
    print("TEST 3: Cortex Analyst Chat")
    print("=" * 60)
    
    body = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What questions can I ask?"
                    }
                ]
            }
        ],
        "semantic_model": "DAMPIERMIKE.REVENUE_TIMESERIES.RAW_DATA/revenue_timeseries.yaml"
    }
    
    event = create_test_event(body)
    try:
        response = cortex_analyst_chat_handler(event, None)
        print(f"✅ Status Code: {response['statusCode']}")
        body_response = json.loads(response['body'])
        
        if 'error' in body_response:
            print(f"❌ Error: {body_response['error']}")
            if 'details' in body_response:
                print(f"Details: {json.dumps(body_response['details'], indent=2)}")
        elif 'message' in body_response:
            print(f"Request ID: {body_response.get('request_id')}")
            print(f"Message content: {json.dumps(body_response['message'], indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    print()

def test_execute_sql():
    """Test 4: Execute SQL"""
    print("=" * 60)
    print("TEST 4: Execute SQL")
    print("=" * 60)
    
    body = {
        "sql": "SELECT CURRENT_VERSION() as version, CURRENT_WAREHOUSE() as warehouse, CURRENT_DATABASE() as database"
    }
    
    event = create_test_event(body)
    try:
        response = execute_sql_handler(event, None)
        print(f"✅ Status Code: {response['statusCode']}")
        body_response = json.loads(response['body'])
        
        if 'error' in body_response:
            print(f"❌ Error: {body_response['error']}")
        else:
            print(f"Columns: {body_response.get('columns')}")
            print(f"Row Count: {body_response.get('row_count')}")
            print(f"Data: {json.dumps(body_response.get('data'), indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    print()


def test_execute_sql_snowpark():
    """Test 5: Execute SQL via Snowpark"""
    print("=" * 60)
    print("TEST 5: Execute SQL (Snowpark)")
    print("=" * 60)

    body = {
        "sql": "SELECT CURRENT_VERSION() as version, CURRENT_WAREHOUSE() as warehouse, CURRENT_DATABASE() as database"
    }

    event = create_test_event(body)
    try:
        response = execute_sql_snowpark_handler(event, None)
        print(f"✅ Status Code: {response['statusCode']}")
        body_response = json.loads(response['body'])

        if 'error' in body_response:
            print(f"❌ Error: {body_response['error']}")
        else:
            print(f"Columns: {body_response.get('columns')}")
            print(f"Row Count: {body_response.get('row_count')}")
            print(f"Data: {json.dumps(body_response.get('data'), indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    print()

def main():
    print("\n" + "=" * 60)
    print("🧪 LAMBDA HANDLER TEST SUITE")
    print("=" * 60)
    print()
    
    # Check environment variables
    required_vars = ['SNOWFLAKE_ACCOUNT', 'SNOWFLAKE_USER', 'SNOWFLAKE_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please ensure .env file exists with required Snowflake credentials")
        return
    
    print(f"✅ Environment variables loaded")
    print(f"   Account: {os.getenv('SNOWFLAKE_ACCOUNT')}")
    print(f"   User: {os.getenv('SNOWFLAKE_USER')}")
    print(f"   Database: {os.getenv('SNOWFLAKE_DATABASE')}")
    print()
    
    # Run tests
    test_basic_lambda()
    test_snowflake_connection()
    test_execute_sql()
    test_execute_sql_snowpark()
    test_cortex_analyst_chat()
    
    print("=" * 60)
    print("🏁 TEST SUITE COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    main()
