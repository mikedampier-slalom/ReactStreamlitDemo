import json
import os

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
