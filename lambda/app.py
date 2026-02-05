import json
import os
import requests
import snowflake.connector
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime
from decimal import Decimal

def lambda_handler(event, context):
    """
    Lambda function handler
    
    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format
        
    context: object, required
        Lambda Context runtime methods and attributes

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict
    """
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "message": "Hello from Lambda!",
            "event": event
        })
    }


def get_snowflake_connection():
    """Get Snowflake connection with credentials from environment"""
    account = os.environ.get('SNOWFLAKE_ACCOUNT')
    user = os.environ.get('SNOWFLAKE_USER')
    token = os.environ.get('SNOWFLAKE_TOKEN')
    warehouse = os.environ.get('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH')
    database = os.environ.get('SNOWFLAKE_DATABASE')
    schema = os.environ.get('SNOWFLAKE_SCHEMA', 'PUBLIC')
    
    # Clean account identifier
    if account and '.snowflakecomputing.com' in account:
        account = account.split('.snowflakecomputing.com')[0]
    
    return snowflake.connector.connect(
        user=user,
        password=token,
        account=account,
        warehouse=warehouse,
        database=database,
        schema=schema,
        login_timeout=10,
        network_timeout=10
    )


def cortex_analyst_chat_handler(event, context):
    """
    Handle Cortex Analyst chat requests using Snowflake REST API with PAT
    
    Expects JSON body:
    {
        "messages": [...],  // conversation history
        "semantic_model": "path/to/model.yaml"
    }
    
    Uses PAT (Personal Access Token) with PROGRAMMATIC_ACCESS_TOKEN authentication.
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        messages = body.get('messages', [])
        semantic_model = body.get('semantic_model', 'DAMPIERMIKE.REVENUE_TIMESERIES.RAW_DATA/revenue_timeseries.yaml')
        
        if not messages:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "No messages provided"
                })
            }
        
        # Get credentials from environment
        account = os.getenv('SNOWFLAKE_ACCOUNT', '')
        token = os.getenv('SNOWFLAKE_TOKEN', '')
        warehouse = os.getenv('SNOWFLAKE_WAREHOUSE', 'MYWAREHOUSE')
        database = os.getenv('SNOWFLAKE_DATABASE', 'DAMPIERMIKE')
        schema = os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC')
        
        # Remove .snowflakecomputing.com if present
        if '.snowflakecomputing.com' in account:
            account = account.replace('.snowflakecomputing.com', '')
        
        # Replace underscores with hyphens for REST API URL
        account_url = account.replace('_', '-')
        
        if not account or not token:
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "Missing Snowflake credentials"
                })
            }
        
        # Construct the REST API URL
        base_url = f"https://{account_url}.snowflakecomputing.com"
        api_endpoint = "/api/v2/cortex/analyst/message"
        url = f"{base_url}{api_endpoint}"
        
        # Prepare request body for Cortex Analyst
        request_body = {
            "messages": messages,
            "semantic_model_file": f"@{semantic_model}"
        }
        
        # Set up headers with PAT authentication
        # Use PROGRAMMATIC_ACCESS_TOKEN for PAT authentication
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
            "X-Snowflake-Warehouse": warehouse,
            "X-Snowflake-Database": database,
            "X-Snowflake-Schema": schema
        }
        
        # Make the REST API call with PAT
        # Use longer timeout for Cortex Analyst (can take time to generate queries)
        response = requests.post(
            url,
            headers=headers,
            json=request_body,
            timeout=120  # 2 minutes timeout
        )
        
        # Check response
        if response.status_code == 200:
            response_data = response.json()
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps(response_data)
            }
        else:
            # Handle error responses
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text}
            
            return {
                "statusCode": response.status_code,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": f"Cortex Analyst API error: {response.status_code}",
                    "details": error_data
                })
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": f"REST API request failed: {str(e)}",
                "type": "RequestException"
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": str(e),
                "type": type(e).__name__
            })
        }


def execute_sql_handler(event, context):
    """
    Execute SQL query and return results
    
    Expects JSON body:
    {
        "sql": "SELECT * FROM table"
    }
    """
    try:
        body = json.loads(event.get('body', '{}'))
        sql = body.get('sql', '')
        
        if not sql:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "No SQL query provided"
                })
            }
        
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        cursor.execute(sql)
        
        # Fetch results
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries with proper JSON serialization
        results = []
        for row in rows:
            row_dict = {}
            for col, value in zip(columns, row):
                # Convert non-JSON-serializable types to strings
                if isinstance(value, (date, datetime)):
                    row_dict[col] = value.isoformat()
                elif isinstance(value, Decimal):
                    row_dict[col] = float(value)
                elif value is None:
                    row_dict[col] = None
                else:
                    row_dict[col] = value
            results.append(row_dict)
        
        cursor.close()
        conn.close()
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "columns": columns,
                "data": results,
                "row_count": len(results)
            })
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": str(e),
                "type": type(e).__name__
            })
        }


def test_snowflake_handler(event, context):
    """
    Test Snowflake REST API connection using Personal Access Token (PAT)
    
    Returns connection status and test query results
    """
    try:
        import snowflake.connector
        
        # Get Snowflake credentials from environment variables
        account = os.environ.get('SNOWFLAKE_ACCOUNT')
        user = os.environ.get('SNOWFLAKE_USER')
        token = os.environ.get('SNOWFLAKE_TOKEN')  # Personal Access Token
        warehouse = os.environ.get('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH')
        database = os.environ.get('SNOWFLAKE_DATABASE')
        schema = os.environ.get('SNOWFLAKE_SCHEMA', 'PUBLIC')
        
        # Clean account identifier (remove .snowflakecomputing.com if present)
        if account and '.snowflakecomputing.com' in account:
            account = account.split('.snowflakecomputing.com')[0]
        
        if not all([account, user, token]):
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "Missing Snowflake credentials",
                    "message": "Please set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, and SNOWFLAKE_TOKEN environment variables"
                })
            }
        
        # Connect to Snowflake using Personal Access Token as password
        conn = snowflake.connector.connect(
            user=user,
            password=token,  # PAT is passed as password
            account=account,
            warehouse=warehouse,
            database=database,
            schema=schema,
            login_timeout=10,  # Set timeout for connection
            network_timeout=10
        )
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_VERSION(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "message": "Successfully connected to Snowflake!",
                "snowflake_version": result[0],
                "warehouse": result[1],
                "database": result[2],
                "schema": result[3]
            })
        }
        
    except ImportError:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Snowflake connector not installed",
                "message": "Run: pip install snowflake-connector-python"
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": str(e),
                "type": type(e).__name__
            })
        }
