import json
import os
from getpass import getpass

cfg_path = os.path.join(os.path.dirname(__file__), 'config.json')

if os.path.exists(cfg_path):
    with open(cfg_path, 'r') as f:
        cfg = json.load(f)
else:
    cfg = {}

print("=== Divorce Ledger Setup ===")
print("Leave any field blank to keep the current value or skip it.\n")

# SMTP / Email Alerts
print("--- Email Alerts ---")
smtp_user = input("SMTP User / Gmail Address (e.g. your.email@gmail.com): ").strip()
if smtp_user:
    cfg['smtp_user'] = smtp_user
    # Using getpass hides the typing
    smtp_pass = getpass("SMTP App Password (typing will be hidden): ").strip()
    if smtp_pass:
        cfg['smtp_pass'] = smtp_pass
    
    notify_email = input("Email address to send alerts TO (e.g. your.email@gmail.com): ").strip()
    if notify_email:
        cfg['notify_emails'] = [notify_email]
        
    cfg['smtp_host'] = 'smtp.gmail.com'
    cfg['smtp_port'] = 587

print("\n--- Plaid Bank Sync ---")
print("You can get these from your Plaid Developer Dashboard.")
client_id = input("Plaid Client ID: ").strip()
if client_id:
    cfg['plaid_client_id'] = client_id
    secret = getpass("Plaid Secret (typing will be hidden): ").strip()
    if secret:
        cfg['plaid_secret'] = secret

with open(cfg_path, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=4)

print("\n✅ Setup complete! Your config.json has been securely updated.")
print("Restart server.py to apply the changes.")
