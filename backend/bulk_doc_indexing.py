# backend/gleanuser_indexer.py
import requests
import json
from requests_oauthlib import OAuth1
import time
from db import get_connection # To fetch credentials from the database
import os


# This function will encapsulate the core logic of your script
def bulk_doc_index():
    conn = None
    cursor = None
    try:
        # Step 1: Fetch credentials from the database
        conn = get_connection()
        if conn is None:
            return {"success": False, "error": "Failed to connect to the database"}
        
        cursor = conn.cursor(dictionary=True) # Use dictionary=True to access columns by name
        
        # Fetch the FIRST (oldest by ID) inserted credentials
        cursor.execute("""
            SELECT glean_account, 
            glean_api_token
            FROM auth_credentials 
            ORDER BY id ASC
            LIMIT 1
        """)
        creds = cursor.fetchone()

        if not creds:
            return {"success": False, "error": "No credentials found in the database."}


        GLEAN_ACCOUNT_ID = creds['glean_account']
        GLEAN_TOKEN = creds['glean_api_token']


        # Path to the bulk_data.txt file
        file_path = os.path.join(os.path.dirname(__file__), 'NetsuiteData', 'bulk_data.txt')
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            return None
        
        # Read the file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        # The file contains JSON objects separated by commas and newlines
        # We need to wrap them in a list structure
        # First, remove the trailing comma if it exists
        if content.rstrip().endswith(','):
            content = content.rstrip()[:-1]
        
        # Wrap the content in square brackets to make it a valid JSON array
        json_content = f"[{content}]"

        documents_array = json.loads(json_content)
        
        unique_number = str(int(time.time() * 1000))

        GleanData = {
            "uploadId": unique_number,
            "isFirstPage": True,
            "isLastPage": True,
            "forceRestartUpload": True,
            "datasource": "netsuite",
            "documents": documents_array
        }        

        gleanUrl = f"https://{GLEAN_ACCOUNT_ID}-be.glean.com/api/index/v1/bulkindexdocuments"
        gleanHeaders = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {GLEAN_TOKEN}'
            }
        userIndexResp = requests.request("POST", gleanUrl, headers=gleanHeaders, data=json.dumps(GleanData))
        print("Glean Response: ", userIndexResp.status_code)
        
        if userIndexResp.status_code == 200:
            print("✅ Successfully Bulk Indexed Netsuite Data to Glean.")
        else:
            print(f"❌ Failed to Bulk Index Netsuite Data to Glean. Status Code: {userIndexResp.status_code}")
            print(f"Response: {userIndexResp.text}")
            return {"success": False, "error": f"Failed to Bulk Index Netsuite Data to Glean. Status Code: {userIndexResp.text}"}


    except Exception as e:
        error_message = f"An unexpected error occurred during Bulk Indexing Data: {str(e)}"
        print(f"❌ {error_message}")
        # import traceback
        # traceback.print_exc() # For more detailed debugging during development
        return {"success": False, "error": error_message}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


