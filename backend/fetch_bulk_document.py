# backend/gleanuser_indexer.py
import requests
import json
from requests_oauthlib import OAuth1
import time
from db import get_connection # To fetch credentials from the database
import os

# This function will encapsulate the core logic of your script
def fetch_bulk_ns_data():
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


        if ACCOUNT_ID:
            REALM = ACCOUNT_ID.replace('-', '_').upper()
        else:
            return {"success": False, "error": "NetSuite Account ID is missing from credentials."}

        # === OAuth1 Setup ===
        auth = OAuth1(
            client_key=CONSUMER_KEY,
            client_secret=CONSUMER_SECRET,
            resource_owner_key=TOKEN,
            resource_owner_secret=TOKEN_SECRET,
            realm=REALM,
            signature_method='HMAC-SHA256'
        )
        
        # === Headers ===
        HEADERS = {
            "Content-Type": "application/json",
            "Prefer": "transient, maxpagesize=1000"
        }
        
        #Setting Up Allowed users for each transaction
        def allowedUsers(auth, headers, ACCOUNT_ID):
        
            # SuiteQL query
            query_text = """
                SELECT e.id AS employee_id, e.firstname, e.lastname, e.email, e.entityid, r.subsidiaryrestriction AS role_subsidiary_restriction, rp.name AS permission_name, rp.permLevel AS permission_level FROM employee e JOIN employeeRolesForSearch erfs ON e.id = erfs.entity JOIN role r ON erfs.role = r.id JOIN rolePermissions rp ON r.id = rp.role WHERE e.giveaccess = 'T' AND e.isinactive = 'F' AND rp.name IN ('Bills', 'Customers', 'Estimate', 'Invoice', 'Items', 'Opportunity', 'Purchase Order', 'Sales Order', 'Vendors' ) AND rp.permLevel IS NOT NULL ORDER BY rp.name, e.lastname
            """
            
            # Function to extract next link
            def get_next_link(links):
                for link in links:
                    if link.get("rel") == "next":
                        return link.get("href")
                return None
            
            # Initial query payload
            query_payload = {
                "q": query_text
            }
            
            # Start URL
            url = f"https://{ACCOUNT_ID}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"
            
            # Collect results
            invoice_list = []
            
            # Step 1: First POST
            response = requests.post(url, headers=headers, auth=auth, data=json.dumps(query_payload))
            if response.status_code != 200:
                print(f"❌ Initial request failed: {response.status_code}")
                print(response.text)
                exit()
            
            result = response.json()
            invoice_list.extend(result.get("items", []))
            next_link = get_next_link(result.get("links", []))
            
            # Step 2: Pagination loop
            while next_link:
                # POST to next_link with same query_payload
                response = requests.post(next_link, headers=headers, auth=auth, data=json.dumps(query_payload))
                if response.status_code == 200:
                    result = response.json()
                    invoice_list.extend(result.get("items", []))
                    next_link = get_next_link(result.get("links", []))
                else:
                    print(f"❌ Pagination failed: {response.status_code}")
                    print(response.text)
                    break
        
            result = {}
            for entry in invoice_list:
                original_permission = entry.get("permission_name")
                email = entry.get("email")
                subsidiary_string = entry.get("role_subsidiary_restriction")
        
                permission_mapping = {
                    "Bills": "vendorbill",
                    "Customers": "custjob",
                    "Estimate": "estimate",
                    "Invoice": "custinvc",
                    "Items": "item",
                    "Opportunity": "opprtnty",
                    "Purchase Order": "purchord",
                    "Sales Order": "salesord",
                    "Vendors": "vendor"
                }
        
        
                if not (original_permission and email and subsidiary_string):
                    continue  # Skip if required data is missing
        
                # Convert permission name
                permission = permission_mapping.get(original_permission, original_permission)
                subsidiaries = [sub.strip() for sub in subsidiary_string.split(",")]   
        
                if permission not in result:
                    result[permission] = {}
        
                for sub_id in subsidiaries:
                    if sub_id not in result[permission]:
                        result[permission][sub_id] = []
        
                    user_data = {"email": email, "datasourceUserId": "netsuite"}
        
                    if user_data not in result[permission][sub_id]:
                        result[permission][sub_id].append(user_data)
        
            return result
        
        allowedUsersList = allowedUsers(auth,HEADERS,ACCOUNT_ID)

        #All User List
        def allAllowUser(auth, headers, ACCOUNT_ID):
        
            # SuiteQL query
            query_text = """
                SELECT BUILTIN_RESULT.TYPE_INTEGER(employee.ID) AS ID, BUILTIN_RESULT.TYPE_STRING(employee.entityid) AS entityid, BUILTIN_RESULT.TYPE_STRING(employee.email) AS email, BUILTIN_RESULT.TYPE_BOOLEAN(employee.giveaccess) AS giveaccess FROM employee WHERE employee.giveaccess = 'T'
            """
            
            # Function to extract next link
            def get_next_link(links):
                for link in links:
                    if link.get("rel") == "next":
                        return link.get("href")
                return None
            
            # Initial query payload
            query_payload = {
                "q": query_text
            }
            
            # Start URL
            url = f"https://{ACCOUNT_ID}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"
            
            # Collect results
            invoice_list = []
            
            # Step 1: First POST
            response = requests.post(url, headers=headers, auth=auth, data=json.dumps(query_payload))
            if response.status_code != 200:
                print(f"❌ Initial request failed: {response.status_code}")
                print(response.text)
                exit()
            
            result = response.json()
            invoice_list.extend(result.get("items", []))
            next_link = get_next_link(result.get("links", []))
            
            # Step 2: Pagination loop
            while next_link:
                # POST to next_link with same query_payload
                response = requests.post(next_link, headers=headers, auth=auth, data=json.dumps(query_payload))
                if response.status_code == 200:
                    result = response.json()
                    invoice_list.extend(result.get("items", []))
                    next_link = get_next_link(result.get("links", []))
                else:
                    print(f"❌ Pagination failed: {response.status_code}")
                    print(response.text)
                    break
        
            if len(invoice_list) > 1 :
        
                Respresult = [
                    {"email": entry["email"], "datasourceUserId": "netsuite"}
                    for entry in invoice_list if "email" in entry
                ]
            return Respresult
        
        allUsersList = allAllowUser(auth,HEADERS,ACCOUNT_ID)
        
        
        # === Helper: Get Pagination Link ===
        
        def get_next_link(links):
            return next((link.get("href") for link in links if link.get("rel") == "next"), None)
        
        # === Run SuiteQL Query with Pagination ===
        def run_suiteql_query(query_text):
            url = f"https://{ACCOUNT_ID}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"
            query_payload = {"q": query_text}
            data_list = []
        
            response = requests.post(url, headers=HEADERS, auth=auth, data=json.dumps(query_payload))
            if response.status_code != 200:
                print(f"❌ Initial request failed: {response.status_code}")
                print(response.text)
                return []
        
            result = response.json()
            data_list.extend(result.get("items", []))
            next_link = get_next_link(result.get("links", []))
        
            while next_link:
                response = requests.post(next_link, headers=HEADERS, auth=auth, data=json.dumps(query_payload))
                if response.status_code == 200:
                    result = response.json()
                    data_list.extend(result.get("items", []))
                    next_link = get_next_link(result.get("links", []))
                else:
                    print(f"❌ Pagination failed: {response.status_code}")
                    print(response.text)
                    break
        
            return data_list
        
        # === Build Glean Document Object ===
        def create_document_object(data, object_type, keys,alloweduserList):
            if object_type == "item":
                allowed_users = alloweduserList  # Return the full mapping
            else:
                subsidiary=data.get("subsidiary")
                allowed_users = alloweduserList.get(object_type, {}).get(subsidiary, [])
        
            record_url_paths = {
                "item": "common/item/item.nl",
                "vendor": "common/entity/vendor.nl",
                "custjob": "common/entity/custjob.nl"
            }
            url_path = record_url_paths.get(object_type, f"accounting/transactions/{object_type}.nl")
        
            return {
                "id": f"DOCNS_{data.get(keys[0], 'unknown')}_{data.get('internalid', 'unknown')}",
                "datasource": "netsuite",
                "objectType": object_type,
                "title": data.get(keys[0], "Untitled"),
                "viewURL": f"https://{ACCOUNT_ID}.app.netsuite.com/app/{url_path}?id={data.get('internalid', '')}",
                "permissions": {
                    "allowedUsers": allowed_users,
                    "allowAnonymousAccess": False,
                    "allowAllDatasourceUsersAccess": True
                },
                "customProperties": [
                    {
                        "name": key,
                        "value": data.get(key, "")
                    } for key in keys
                ]
            }
        
        # === Create Bulk Glean Format ===
        def create_bulk_glean_format(data_set, object_type, keys,alloweduserList):

            return [create_document_object(data, object_type, keys,alloweduserList) for data in data_set]


            
            # unique_number = str(int(time.time() * 1000))
            # return {
            #     "uploadId": unique_number,
            #     "isFirstPage": True,
            #     "isLastPage": True,
            #     "forceRestartUpload": True,
            #     "datasource": "netsuite",
            #     "documents": [create_document_object(data, object_type, keys,alloweduserList) for data in data_set]
            # }
            

        
        # Invoice Query
        invoice_query = "SELECT t.id AS internalid, t.tranid AS InvoiceNumber, t.otherrefnum AS PONumber, t.DueDate, t.status, CASE t.status WHEN 'A' THEN 'Pending Approval' WHEN 'B' THEN 'Open' WHEN 'C' THEN 'Paid In Full' ELSE 'Other' END AS status_name, t.entity AS customer_internal_id, customer.entityid AS customer_id, customer.altname AS netsuitecustomer, SUM(ABS(transactionLine.netamount)) AS UnPaidAmount,subsidiary.id AS subsidiary, subsidiary.name AS subsidiary_name, t.type AS transaction_type, so.transactionnumber AS sales_order_number FROM transaction t LEFT JOIN transactionLine ON transactionLine.transaction = t.id LEFT JOIN customer ON customer.id = t.entity LEFT JOIN subsidiary ON subsidiary.id = transactionLine.subsidiary LEFT JOIN transaction so ON so.id = transactionLine.createdfrom WHERE t.type = 'CustInvc' AND transactionLine.mainline = 'F' GROUP BY t.id, t.tranid, t.otherrefnum, t.duedate, t.status, t.entity, customer.entityid, customer.altname,subsidiary.id, subsidiary.name, t.type, so.transactionnumber"

        # Vendor Bill Query
        bill_query = "SELECT vb.id AS internalid, vb.tranid AS vendorinvoicenumber, vb.transactionnumber AS VendorBillNumber, vb.duedate AS billduedate, vb.status, CASE vb.status WHEN 'B' THEN 'Open' WHEN 'C' THEN 'Paid In Full' WHEN 'A' THEN 'Pending Approval' ELSE 'Other' END AS vendorbillstatus, vb.entity AS vendor_internal_id, vendor.entityid AS vendor_id, vendor.altname AS vendor, SUM(ABS(vbl.netamount)) AS billamount, subsidiary.id AS subsidiary, subsidiary.name AS subsidiary_name, currency.name AS currency_name, vb.type AS transaction_type, po.transactionnumber AS nsponumber FROM transaction vb LEFT JOIN transactionline vbl ON vbl.transaction = vb.id LEFT JOIN vendor ON vendor.id = vb.entity LEFT JOIN subsidiary ON subsidiary.id = vbl.subsidiary LEFT JOIN transaction po ON po.id = vbl.createdfrom LEFT JOIN currency ON currency.id = vb.currency WHERE vb.type = 'VendBill' AND vbl.mainline = 'F' GROUP BY vb.id, vb.tranid, vb.transactionnumber, vb.duedate, vb.status, vb.entity, vendor.entityid, vendor.altname, subsidiary.id, subsidiary.name, currency.name, vb.type, po.transactionnumber"

        # PO Query
        po_query = "SELECT t.id AS internalid, t.tranid AS nsponumberpo, e.entityid AS vendor_name, ABS(t.foreigntotal) AS nspoamountpo, t.shipdate AS eta, t.status AS status_code, CASE t.status WHEN 'A' THEN 'Pending Supervisor Approval' WHEN 'B' THEN 'Pending Receipt' WHEN 'C' THEN 'Rejected by Supervisor' WHEN 'D' THEN 'Partially Received' WHEN 'E' THEN 'Pending Billing/Partially Received' WHEN 'F' THEN 'Pending Bill' WHEN 'G' THEN 'Fully Billed' WHEN 'H' THEN 'Closed' ELSE 'Unknown' END AS nspostatus, c.symbol AS currency, vendor.altname AS nspovendorpo, pol.subsidiary AS subsidiary FROM transaction t LEFT JOIN entity e ON t.entity = e.id LEFT JOIN currency c ON t.currency = c.id LEFT JOIN vendor ON vendor.id = t.entity LEFT JOIN transactionline pol ON pol.transaction = t.id WHERE t.type = 'PurchOrd' ORDER BY t.trandate DESC"

        #Opprtunity Query
        opp_query = "SELECT t.id AS internalid, t.tranid AS nsopportunitynumber, t.title AS nsoptitle, c.entityid AS customer_name, t.projectedtotal AS nsopexpectedamount, customer.altname AS nsopcustomer, tl.subsidiary AS subsidiary, CASE t.status WHEN 'A' THEN 'In Progress' WHEN 'B' THEN 'Issued Estimate' WHEN 'C' THEN 'Closed – Won' WHEN 'D' THEN 'Closed – Lost' ELSE 'Unknown' END AS nsopstatus, t.duedate AS nsopexpectedclosedate FROM transaction t LEFT JOIN entity c ON t.entity = c.id LEFT JOIN customer ON customer.id = t.entity LEFT JOIN transactionLine tl ON tl.transaction = t.id WHERE t.type = 'Opprtnty' AND tl.mainline = 'T' ORDER BY t.trandate DESC"

        #Estimate Query
        est_query = "SELECT TRANSACTION.entity AS entity_id, TRANSACTION.id AS internalid, Customer.altname AS nsquotecustomer, TRANSACTION.foreigntotal AS nsquoteamount, TRANSACTION.tranid AS nsqoutenumber, employee.firstname || ' ' || employee.lastname AS nsquotesalesrep, subsidiary.id AS subsidiary, CASE TRANSACTION.status WHEN 'A' THEN 'Open' WHEN 'B' THEN 'Processed' WHEN 'C' THEN 'Closed' WHEN 'V' THEN 'Voided' WHEN 'X' THEN 'Expired' ELSE 'Other' END AS nsquotestatus, TRANSACTION.currency AS currency_id, TRANSACTION.tosubsidiary AS tosubsidiary_id FROM TRANSACTION LEFT JOIN Customer ON TRANSACTION.entity = Customer.id LEFT JOIN transactionline ebl ON ebl.transaction = TRANSACTION.id LEFT JOIN subsidiary ON subsidiary.id = ebl.subsidiary LEFT JOIN employee ON employee.id = TRANSACTION.employee WHERE TRANSACTION.TYPE IN ('Estimate') AND ebl.mainline = 'T'"

        #SO Query
        so_query = "SELECT t.id AS internalid, t.tranid AS nssonumber, e.entitytitle AS nssocustomer, t.trandate AS nssodate, ABS(t.foreigntotal) AS nssoamount, tl.subsidiary AS subsidiary, CASE t.status WHEN 'A' THEN 'Pending Approval' WHEN 'B' THEN 'Pending Fulfillment' WHEN 'C' THEN 'Partially Fulfilled' WHEN 'D' THEN 'Pending Billing/Partially Fulfilled' WHEN 'E' THEN 'Pending Billing' WHEN 'F' THEN 'Billed' WHEN 'G' THEN 'Closed' ELSE 'Unknown' END AS nssostatus FROM transaction t LEFT JOIN transactionline tl ON tl.transaction = t.id AND tl.mainline = 'T' LEFT JOIN entity e ON t.entity = e.id WHERE t.type = 'SalesOrd' ORDER BY t.trandate DESC"

        #item Query
        item_query="SELECT BUILTIN_RESULT.TYPE_INTEGER(item.ID) AS internalid, BUILTIN_RESULT.TYPE_STRING(item.itemid) AS nsitemname, BUILTIN_RESULT.TYPE_STRING(item.itemtype) AS itemtype, BUILTIN_RESULT.TYPE_STRING(item.description) AS itemdesc FROM item"

        #vendor Query
        vendor_query="SELECT BUILTIN_RESULT.TYPE_INTEGER(Vendor.ID) AS internalid, BUILTIN_RESULT.TYPE_STRING(NVL(Vendor.companyname, 'N/A')) AS nsvendorname, BUILTIN_RESULT.TYPE_INTEGER(NVL(VendorSubsidiaryRelationship.subsidiary, -1)) AS subsidiary, BUILTIN_RESULT.TYPE_STRING(NVL(currency.symbol, '') || ' ' || TO_CHAR(NVL(Vendor.balanceprimary, 0))) AS nsvendorbalance, BUILTIN_RESULT.TYPE_STRING(NVL(currency.symbol, '') || ' ' || TO_CHAR(NVL(Vendor.unbilledordersprimary, 0))) AS nsvendorunbillamt, BUILTIN_RESULT.TYPE_STRING(NVL(currency.symbol, 'N/A')) AS vendorcurrency FROM Vendor LEFT JOIN VendorSubsidiaryRelationship ON Vendor.ID = VendorSubsidiaryRelationship.entity LEFT JOIN currency ON Vendor.currency = currency.id"

        #customer Query
        customer_query="SELECT BUILTIN_RESULT.TYPE_INTEGER(Customer.ID) AS internalid, BUILTIN_RESULT.TYPE_INTEGER(CustomerSubsidiaryRelationship.subsidiary) AS subsidiary, BUILTIN_RESULT.TYPE_STRING(Subsidiary.name) AS nscustomersubsidiary, BUILTIN_RESULT.TYPE_STRING(Customer.entityid || ' - ' || Customer.companyname) AS nscustomername, BUILTIN_RESULT.TYPE_STRING(COALESCE(currency.symbol, 'N/A') || ' ' || TO_CHAR(NVL(Customer.overduebalancesearch, 0))) AS nscustomeroverdue FROM Customer LEFT JOIN CustomerSubsidiaryRelationship ON Customer.ID = CustomerSubsidiaryRelationship.entity LEFT JOIN Subsidiary ON CustomerSubsidiaryRelationship.subsidiary = Subsidiary.ID LEFT JOIN Currency ON Customer.currency = Currency.ID"

        # Fetch data
        invoices = run_suiteql_query(invoice_query)
        vendor_bills = run_suiteql_query(bill_query)
        purchase_order = run_suiteql_query(po_query)
        opprtunity_list = run_suiteql_query(opp_query)
        estimate_list = run_suiteql_query(est_query)
        so_list = run_suiteql_query(so_query)
        item_list = run_suiteql_query(item_query)
        vendor_list = run_suiteql_query(vendor_query)
        customer_list = run_suiteql_query(customer_query)

        unique_invoices = {entry["internalid"]: entry for entry in invoices}.values()
        unique_invoices_list = list(unique_invoices)

        unique_vendor_bills = {entry["internalid"]: entry for entry in vendor_bills}.values()
        unique_vendor_bills_list = list(unique_vendor_bills)

        unique_po = {entry["internalid"]: entry for entry in purchase_order}.values()
        unique_po_list = list(unique_po)

        unique_opprtunity = {entry["internalid"]: entry for entry in opprtunity_list}.values()
        unique_opprtunity_list = list(unique_opprtunity)

        unique_estimate = {entry["internalid"]: entry for entry in estimate_list}.values()
        unique_estimate_list = list(unique_estimate)

        unique_so = {entry["internalid"]: entry for entry in so_list}.values()
        unique_so_list = list(unique_so)

        unique_item = {entry["internalid"]: entry for entry in item_list}.values()
        unique_item_list = list(unique_item)

        unique_vendor = {entry["internalid"]: entry for entry in vendor_list}.values()
        unique_vendor_list = list(unique_vendor)

        unique_customer = {entry["internalid"]: entry for entry in customer_list}.values()
        unique_customer_list = list(unique_customer)

        # Sample data for testing
        sample_invoices = unique_invoices_list
        sample_bills = unique_vendor_bills_list
        sample_pos = unique_po_list
        sample_opps = unique_opprtunity_list
        sample_estimate = unique_estimate_list
        sample_so_list = unique_so_list
        sample_item_list = unique_item_list
        sample_vendor_list= unique_vendor_list
        sample_customer_list= unique_customer_list


        # Glean keys
        invoice_keys=["invoicenumber", "duedate", "netsuitecustomer", "unpaidamount", "ponumber","internalid"]
        bill_keys = ["vendorinvoicenumber", "vendor", "billamount", "nsponumber", "billduedate", "vendorbillstatus"]
        po_keys = ["nsponumberpo", "nspovendorpo", "nspoamountpo", "nspostatus"]
        opp_keys = ["nsopportunitynumber","nsoptitle", "nsopcustomer", "nsopexpectedamount", "nsopstatus","nsopsalesrep","nsopexpectedclosedate"]
        estimate_keys = ["nsqoutenumber", "nsquotecustomer", "nsquotesalesrep", "nsquoteamount", "nsquotestatus"]
        so_keys = ["nssonumber", "nssodate", "nssoamount", "nssostatus",]
        item_keys = ["nsitemname", "itemtype", "itemdesc"]
        vendor_keys = ["nsvendorname", "nsvendorbalance","nsvendorunbillamt"]
        customer_keys = ["nscustomername", "nscustomersubsidiary","nscustomeroverdue"]


        # Ensure directory exists
        os.makedirs('NetsuiteData', exist_ok=True)
        # Define file path
        file_path = os.path.join(os.path.dirname(__file__), 'NetsuiteData', 'bulk_data.txt')
        # Step 1: Clear existing file content
        open(file_path, 'w').close()

        # Generate and print Glean Bulk formats
        glean_invoice_bulk = create_bulk_glean_format(sample_invoices, "custinvc", invoice_keys,allowedUsersList) #invoice
        # Create directory if it doesn't exist
        os.makedirs('NetsuiteData', exist_ok=True)
        file_path = os.path.join(os.path.dirname(__file__), 'NetsuiteData', 'bulk_data.txt')
        with open(file_path, 'a') as f:  # 'a' mode for appending
            for obj in glean_invoice_bulk:
                json_str = json.dumps(obj, indent=2)
                f.write(json_str + ',\n')


        glean_bill_bulk = create_bulk_glean_format(sample_bills, "vendorbill", bill_keys,allowedUsersList) #VendorBill
        # Create directory if it doesn't exist
        os.makedirs('NetsuiteData', exist_ok=True)
        file_path = os.path.join(os.path.dirname(__file__), 'NetsuiteData', 'bulk_data.txt')
        with open(file_path, 'a') as f:  # 'a' mode for appending
            for obj in glean_bill_bulk:
                json_str = json.dumps(obj, indent=2)
                f.write(json_str + ',\n')

        glean_PO_bulk = create_bulk_glean_format(sample_pos, "purchord", po_keys,allowedUsersList) #purchord
        # Create directory if it doesn't exist
        os.makedirs('NetsuiteData', exist_ok=True)
        file_path = os.path.join(os.path.dirname(__file__), 'NetsuiteData', 'bulk_data.txt')
        with open(file_path, 'a') as f:  # 'a' mode for appending
            for obj in glean_PO_bulk:
                json_str = json.dumps(obj, indent=2)
                f.write(json_str + ',\n')

        glean_op_bulk = create_bulk_glean_format(sample_opps, "opprtnty", opp_keys,allowedUsersList) #oprtunity
        # Create directory if it doesn't exist
        os.makedirs('NetsuiteData', exist_ok=True)
        file_path = os.path.join(os.path.dirname(__file__), 'NetsuiteData', 'bulk_data.txt')
        with open(file_path, 'a') as f:  # 'a' mode for appending
            for obj in glean_op_bulk:
                json_str = json.dumps(obj, indent=2)
                f.write(json_str + ',\n')

        glean_estimate_bulk = create_bulk_glean_format(sample_estimate, "estimate", estimate_keys,allowedUsersList) #Estimate
        # Create directory if it doesn't exist
        os.makedirs('NetsuiteData', exist_ok=True)
        file_path = os.path.join(os.path.dirname(__file__), 'NetsuiteData', 'bulk_data.txt')
        with open(file_path, 'a') as f:  # 'a' mode for appending
            for obj in glean_estimate_bulk:
                json_str = json.dumps(obj, indent=2)
                f.write(json_str + ',\n')

        glean_so_bulk = create_bulk_glean_format(sample_so_list, "salesord", so_keys,allowedUsersList) #Sales order
        # Create directory if it doesn't exist
        os.makedirs('NetsuiteData', exist_ok=True)
        file_path = os.path.join(os.path.dirname(__file__), 'NetsuiteData', 'bulk_data.txt')
        with open(file_path, 'a') as f:  # 'a' mode for appending
            for obj in glean_so_bulk:
                json_str = json.dumps(obj, indent=2)
                f.write(json_str + ',\n')

        glean_item_bulk = create_bulk_glean_format(sample_item_list, "item", item_keys,allUsersList) #Item
        # Create directory if it doesn't exist
        os.makedirs('NetsuiteData', exist_ok=True)
        file_path = os.path.join(os.path.dirname(__file__), 'NetsuiteData', 'bulk_data.txt')
        with open(file_path, 'a') as f:  # 'a' mode for appending
            for obj in glean_item_bulk:
                json_str = json.dumps(obj, indent=2)
                f.write(json_str + ',\n')

        glean_vendor_bulk = create_bulk_glean_format(sample_vendor_list, "vendor", vendor_keys,allowedUsersList) #vendor
        # Create directory if it doesn't exist
        os.makedirs('NetsuiteData', exist_ok=True)
        file_path = os.path.join(os.path.dirname(__file__), 'NetsuiteData', 'bulk_data.txt')
        with open(file_path, 'a') as f:  # 'a' mode for appending
            for obj in glean_vendor_bulk:
                json_str = json.dumps(obj, indent=2)
                f.write(json_str + ',\n')

        glean_customer_bulk = create_bulk_glean_format(sample_customer_list, "custjob", customer_keys,allowedUsersList) #customer
        # Create directory if it doesn't exist
        os.makedirs('NetsuiteData', exist_ok=True)
        file_path = os.path.join(os.path.dirname(__file__), 'NetsuiteData', 'bulk_data.txt')
        with open(file_path, 'a') as f:  # 'a' mode for appending
            for obj in glean_customer_bulk:
                json_str = json.dumps(obj, indent=2)
                f.write(json_str + ',\n')

        return {"success": True, "message": f"Successfully fetched the Netsuite Data for bulk processing"}




    except Exception as e:
        error_message = f"An unexpected error occurred during Fetching Netsuite Data: {str(e)}"
        print(f"❌ {error_message}")
        # import traceback
        # traceback.print_exc() # For more detailed debugging during development
        return {"success": False, "error": error_message}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

