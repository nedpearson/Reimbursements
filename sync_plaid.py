import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
import json
import os
import datetime

# =======================================================================
# PLAID SYNC FRAMEWORK
# To use this, you must have a Plaid Developer account and provide your
# Client ID and Secret in config.json.
# =======================================================================

def get_plaid_client():
    cfg_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.exists(cfg_path):
        print("config.json not found.")
        return None
        
    with open(cfg_path, 'r') as f:
        cfg = json.load(f)
        
    client_id = cfg.get('plaid_client_id')
    secret = cfg.get('plaid_secret')
    env = cfg.get('plaid_env', 'sandbox')
    
    if not client_id or not secret:
        print("Plaid credentials missing from config.json.")
        return None
        
    environments = {
        'sandbox': plaid.Environment.Sandbox,
        'development': plaid.Environment.Development,
        'production': plaid.Environment.Production
    }
    
    configuration = plaid.Configuration(
        host=environments[env],
        api_key={
            'clientId': client_id,
            'secret': secret,
        }
    )
    
    api_client = plaid.ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)
    return client

def fetch_transactions(access_token, start_date, end_date):
    client = get_plaid_client()
    if not client:
        return []
        
    try:
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
            options=TransactionsGetRequestOptions()
        )
        response = client.transactions_get(request)
        return response['transactions']
    except plaid.ApiException as e:
        print("Plaid API error:", e)
        return []

if __name__ == '__main__':
    print("Plaid Sync Framework initialized.")
    print("Add your 'plaid_client_id' and 'plaid_secret' to config.json to connect.")
    # Example usage (requires an access_token generated via Plaid Link frontend):
    # transactions = fetch_transactions(ACCESS_TOKEN, datetime.date(2026, 1, 1), datetime.date.today())
    # for t in transactions:
    #     print(t.date, t.name, t.amount)
