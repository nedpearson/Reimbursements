import json
import os
import requests

def notify_comment(item_id, author, text):
    try:
        cfg_path = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r') as f:
                cfg = json.load(f)
        else:
            cfg = {}
            
        # Send to the main user account (form_email/user_email)
        target_email = cfg.get('form_email') or cfg.get('user_email') or 'nedpearson@gmail.com'
        
        url = f"https://formsubmit.co/ajax/{target_email}"
        
        payload = {
            "name": f"Divorce Ledger Chat - {author}",
            "subject": f"New chat message on {item_id}",
            "message": f"New comment from {author} on item {item_id}:\n\n{text}\n\nLog in to the portal to reply."
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Alert successfully sent to {target_email} via FormSubmit.")
        else:
            print("Failed to send alert via FormSubmit:", response.text)
            
    except Exception as e:
        print("Error sending alert:", e)
