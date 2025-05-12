# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from db import get_connection # Assuming your db.py and get_connection function are set up
from gleanuser_indexer import perform_user_indexing 
from fetch_bulk_document import fetch_bulk_ns_data
from bulk_doc_indexing import bulk_doc_index      

print("--- FLASK APP SCRIPT IS STARTING ---")

app = Flask(__name__)
# Using permissive CORS for now, you can restrict it later if needed:
# e.g., CORS(app, origins=['http://localhost:3000'])
CORS(app)

print("--- FLASK APP INITIALIZED, CORS APPLIED ---")

@app.route('/api/auth', methods=['POST']) # Flask-CORS handles OPTIONS automatically
def save_auth():
    print(f"--- /api/auth ROUTE HIT --- Method: {request.method}")
    data = request.json
    print(f"--- RECEIVED DATA: {data} ---")

    conn = None  # Initialize conn and cursor to None
    cursor = None

    try:
        conn = get_connection()
        if conn is None: # Check if connection was successful
            print("--- FAILED TO GET DATABASE CONNECTION ---")
            return jsonify({"error": "Failed to connect to the database"}), 500
        
        cursor = conn.cursor()
        if cursor is None: # Should not happen if conn is valid, but good practice
            print("--- FAILED TO GET DATABASE CURSOR ---")
            return jsonify({"error": "Failed to create database cursor"}), 500

        # In app.py, inside the save_auth() function:

        query = """
        INSERT INTO auth_credentials (
            glean_account, glean_api_token,  
            netsuite_account_id, netsuite_consumer_key, netsuite_consumer_secret, 
            netsuite_token, netsuite_token_secret 
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        # The 'values' tuple should map correctly to these new column names.
        # The data.get() keys are based on your frontend payload and seem okay.
        values = (
            data.get("gleanAccount"),     # Corresponds to glean_account
            data.get("gleanToken"),       # Corresponds to glean_api_token
            data.get("accountId"),        # Corresponds to netsuite_account_id
            data.get("consumerKey"),      # Corresponds to netsuite_consumer_key
            data.get("consumerSecret"),   # Corresponds to netsuite_consumer_secret
            data.get("token"),            # Corresponds to netsuite_token
            data.get("tokenSecret")       # Corresponds to netsuite_token_secret
        )

        cursor.execute(query, values)
        conn.commit()
        print("--- DATA INSERTED AND COMMITTED SUCCESSFULLY ---")
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        print(f"--- ERROR IN /api/auth: {str(e)} ---")
        if conn: # Rollback in case of error after connection but before commit
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            print("--- CLOSING CURSOR ---")
            cursor.close()
        if conn:
            print("--- CLOSING CONNECTION ---")
            conn.close()


# New route for indexing users
@app.route('/api/index_users', methods=['POST']) # Frontend calls this with POST
def index_users_route():
    print(f"--- /api/index_users ROUTE HIT --- Method: {request.method}")
    
    # Call the function from glean_indexer.py
    # This function now handles fetching credentials from DB itself
    result = perform_user_indexing() 
    
    if result.get("success"):
        # Send back the message from perform_user_indexing and other details if needed
        return jsonify({
            "message": result.get("message", "User indexing process completed."), 
            "users_indexed": result.get("users_indexed"),
            "glean_response": result.get("glean_response")
        }), 200
    else:
        # Send back the error from perform_user_indexing
        return jsonify({
            "error": result.get("error", "User indexing failed."),
            "details": result.get("details") # This might contain detailed error from NetSuite/Glean
        }), 500
    
    
@app.route('/api/fetch_ns_bulk_data', methods=['POST']) # Frontend calls this with POST
def fetch_ns_bulk_data_route():
    print(f"--- /api/fetch_ns_bulk_data ROUTE HIT --- Method: {request.method}")
    
    # Call the function from glean_indexer.py
    # This function now handles fetching credentials from DB itself
    result = fetch_bulk_ns_data() 
    
    if result.get("success"):
        # Send back the message from perform_user_indexing and other details if needed
        return jsonify({
            "message": result.get("message", "Successfully fetched bulk data from Netsuite."),
        }), 200
    else:
        # Send back the error from perform_user_indexing
        return jsonify({
            "error": result.get("error", "Bulk Fetch NS Data failed."),
            "details": result.get("details") # This might contain detailed error from NetSuite/Glean
        }), 500
    
@app.route('/api/bulk_doc_index', methods=['POST']) # Frontend calls this with POST
def bulk_doc_index_route():
    print(f"--- /api/bulk_doc_index ROUTE HIT --- Method: {request.method}")
    
    # Call the function from glean_indexer.py
    # This function now handles fetching credentials from DB itself
    result = bulk_doc_index() 
    
    if result.get("success"):
        # Send back the message from perform_user_indexing and other details if needed
        return jsonify({
            "message": result.get("message", "Successfully fetched bulk data from Netsuite."),
        }), 200
    else:
        # Send back the error from perform_user_indexing
        return jsonify({
            "error": result.get("error", "Bulk Fetch NS Data failed."),
            "details": result.get("details") # This might contain detailed error from NetSuite/Glean
        }), 500
       

if __name__ == '__main__':
    print("--- STARTING FLASK DEVELOPMENT SERVER ---")
    # Changed port to 5001 to avoid conflict with AirTunes on port 5000
    app.run(host='localhost', port=5001, debug=True)