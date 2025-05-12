# backend/gleanuser_indexer.py
import requests
import json
from requests_oauthlib import OAuth1
import time
from db import get_connection # To fetch credentials from the database

# This function will encapsulate the core logic of your script
def perform_user_indexing():
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
            SELECT glean_account, glean_api_token AS glean_token, 
                   netsuite_account_id AS account_id, 
                   netsuite_consumer_key AS consumer_key, 
                   netsuite_consumer_secret AS consumer_secret, 
                   netsuite_token AS token, 
                   netsuite_token_secret AS token_secret
            FROM auth_credentials 
            ORDER BY id ASC 
            LIMIT 1
        """)
        creds = cursor.fetchone()

        if not creds:
            return {"success": False, "error": "No credentials found in the database."}

        ACCOUNT_ID = creds['account_id']
        CONSUMER_KEY = creds['consumer_key']
        CONSUMER_SECRET = creds['consumer_secret']
        TOKEN = creds['token']
        TOKEN_SECRET = creds['token_secret']
        GLEAN_ACCOUNT_ID = creds['glean_account'] # Assuming 'glean_account' from DB is the Glean Account ID
        GLEAN_TOKEN = creds['glean_token']

        # Derive REALM from ACCOUNT_ID (e.g., '9855553-sb1' -> '9855553_SB1')
        # This logic might need adjustment based on actual ACCOUNT_ID format
        if ACCOUNT_ID:
            REALM = ACCOUNT_ID.replace('-', '_').upper()
        else:
            return {"success": False, "error": "NetSuite Account ID is missing from credentials."}

        # --- Your existing NetSuite and Glean logic starts here ---
        
        # OAuth1 setup
        auth = OAuth1(
            client_key=CONSUMER_KEY,
            client_secret=CONSUMER_SECRET,
            resource_owner_key=TOKEN,
            resource_owner_secret=TOKEN_SECRET,
            realm=REALM,
            signature_method='HMAC-SHA256'
        )
        
        # Headers for NetSuite
        netsuite_headers = {
            "Content-Type": "application/json",
            "Prefer": "transient, maxpagesize=1000" # Good for pagination
        }

        # SuiteQL query
        query_text = """
            SELECT BUILTIN_RESULT.TYPE_INTEGER(employee.ID) AS ID, 
                   BUILTIN_RESULT.TYPE_STRING(employee.entityid) AS entityid, 
                   BUILTIN_RESULT.TYPE_STRING(employee.email) AS email, 
                   BUILTIN_RESULT.TYPE_BOOLEAN(employee.giveaccess) AS giveaccess 
            FROM employee 
            WHERE employee.giveaccess = 'T'
        """
        
        def get_next_link(links):
            for link in links:
                if link.get("rel") == "next":
                    return link.get("href")
            return None
        
        query_payload = {"q": query_text}
        netsuite_url = f"https://{ACCOUNT_ID}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"
        
        employee_list = []
        
        print(f"Attempting initial NetSuite query to: {netsuite_url}")
        response = requests.post(netsuite_url, headers=netsuite_headers, auth=auth, data=json.dumps(query_payload))
        
        if response.status_code != 200:
            error_message = f"NetSuite initial request failed: {response.status_code} - {response.text}"
            print(f"❌ {error_message}")
            return {"success": False, "error": error_message, "details": response.text}
        
        result = response.json()
        employee_list.extend(result.get("items", []))
        next_link = get_next_link(result.get("links", []))
        print(f"Initial fetch: {len(employee_list)} employees. Next link: {next_link is not None}")

        while next_link:
            print(f"Fetching next page from NetSuite: {next_link}")
            response = requests.post(next_link, headers=netsuite_headers, auth=auth, data=json.dumps(query_payload))
            if response.status_code == 200:
                result = response.json()
                employee_list.extend(result.get("items", []))
                next_link = get_next_link(result.get("links", []))
                print(f"Fetched page: {len(result.get('items', []))} employees. Total: {len(employee_list)}. Next link: {next_link is not None}")
            else:
                error_message = f"NetSuite pagination failed: {response.status_code} - {response.text}"
                print(f"❌ {error_message}")
                return {"success": False, "error": error_message, "details": response.text}
        
        if not employee_list:
            print("No active employees found in NetSuite to index.")
            return {"success": True, "message": "No active employees found in NetSuite to index.", "users_indexed": 0}

        user_emails = [entry["email"] for entry in employee_list if entry.get("email")] # Ensure email exists
        print(f"✅ Total active employees retrieved from NetSuite: {len(employee_list)}")
        print(f"Emails to index in Glean: {len(user_emails)}")

        if not user_emails:
            print("No employees with email addresses found to index.")
            return {"success": True, "message": "No employees with email addresses found to index.", "users_indexed": 0}

        glean_url = f"https://{GLEAN_ACCOUNT_ID}-be.glean.com/api/index/v1/bulkindexusers"
        glean_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {GLEAN_TOKEN}'
        }

        payload_list = [{"email": email, "isActive": "true"} for email in user_emails]
        unique_upload_id = str(int(time.time() * 1000))

        glean_user_index_payload = {
            "uploadId": unique_upload_id,
            "isFirstPage": "true", # For simplicity, sending all users in one batch
            "isLastPage": "true",
            "forceRestartUpload": "true", # Set to true to ensure this batch is processed fresh
            "datasource": "netsuite", # Or your specific Glean datasource name
            "users": payload_list,
            "disableStaleDataDeletionCheck": "true" # Consider implications of this
        }

        print(f"Attempting to index {len(payload_list)} users in Glean for datasource 'netsuite'. Upload ID: {unique_upload_id}")
        user_index_resp = requests.post(glean_url, headers=glean_headers, data=json.dumps(glean_user_index_payload))

        print(f"Glean API Response Status: {user_index_resp.status_code}")
        print(f"Glean API Response Body: {user_index_resp.text}")

        if user_index_resp.status_code == 200 or user_index_resp.status_code == 202: # 202 Accepted is also common for bulk APIs
            print("✅ Successfully submitted user data to Glean for indexing.")
            return {"success": True, "message": f"Successfully submitted {len(payload_list)} users to Glean for indexing.", "users_indexed": len(payload_list), "glean_response": user_index_resp.json() if user_index_resp.content else {}}
        else:
            error_message = f"Failed to index user data in Glean: {user_index_resp.status_code}"
            print(f"❌ {error_message}")
            return {"success": False, "error": error_message, "details": user_index_resp.text}

    except Exception as e:
        error_message = f"An unexpected error occurred during user indexing: {str(e)}"
        print(f"❌ {error_message}")
        # import traceback
        # traceback.print_exc() # For more detailed debugging during development
        return {"success": False, "error": error_message}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# If you want to test this file directly (optional)
# if __name__ == '__main__':
#     print("Testing perform_user_indexing directly...")
#     # Ensure your db.py is configured and you have credentials in the DB
#     # You might need to temporarily hardcode credentials in db.py for this direct test
#     # OR ensure your Flask app has run once to save some credentials.
#     result = perform_user_indexing()
#     print("\n--- Test Result ---")
#     print(json.dumps(result, indent=2))
