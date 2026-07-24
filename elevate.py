import os
import sys

hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
try:
    with open(hosts_path, "a") as f:
        f.write("\n127.0.0.1 reimbursements.bridgebox.ai\n")
    print("Successfully added to hosts file.")
except Exception as e:
    print(f"Failed: {e}")
