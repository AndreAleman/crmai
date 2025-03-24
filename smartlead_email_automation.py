import requests
import os
import pandas as pd
from datetime import datetime, timedelta


def authenticate_with_smartlead():
    print("Step 1: Authenticating with Smartlead API...")
    
    # Load API key from file
    api_key_file = 'smartlead_api.txt'  # File is one directory up
    try:
        with open(api_key_file, 'r') as file:
            api_key = file.read().strip()
    except FileNotFoundError:
        print(f"⚠️ API key file not found: {api_key_file}")
        return None
    
    # Set API endpoint
    api_endpoint = 'https://server.smartlead.ai/api/v1/campaigns'
    
    # Make a GET request to test authentication
    try:
        response = requests.get(f"{api_endpoint}?api_key={api_key}")
        if response.status_code == 200:
            print("✅ Authentication successful.")
            return api_key
        else:
            print(f"⚠️ Authentication failed. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Request error: {e}")
        return None


# Call the function to authenticate
api_key = authenticate_with_smartlead()
if api_key is not None:
    print("API key is valid and ready for use.")
else:
    print("Authentication failed. Please check your API key.")





def fetch_leads_needing_email():
    print("Step 2: Fetching leads needing email actions...")
    
    try:
        df = pd.read_excel('leads.xlsx')
        print("Column names in leads.xlsx:", df.columns.tolist())

        # Filter leads needing email actions
        email_leads = df[
            (
                (df['Next Action'] == 'Email') &  # Next action is Email
                (
                    (df['Days Until Next Action'] <= 0) |  # Due today or overdue
                    (df['Days Until Next Action'] == 1)    # Due tomorrow
                )
            ) &
            (df['Pause Trigger'].isna() | (df['Pause Trigger'] == ''))  # Not paused
        ]
        
        print(f"Found {len(email_leads)} leads needing email actions.")
        return email_leads
    
    except FileNotFoundError:
        print("⚠️ 'leads.xlsx' file not found.")
        return None
    except Exception as e:
        print(f"⚠️ Error fetching leads: {e}")
        return None



# Call the function to fetch leads
email_leads = fetch_leads_needing_email()
if email_leads is not None and not email_leads.empty:
    print("\nSample of leads needing email actions:")
    print(email_leads[['First Name', 'Last Name', 'Next Action', 'Days Until Next Action']].head())
else:
    print("No leads found needing email actions or an error occurred.")
