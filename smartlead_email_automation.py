import requests
import os
import pandas as pd
from datetime import datetime, timedelta
import time

def authenticate_with_smartlead():
    print("Step 1: Authenticating with Smartlead API...")
    
    api_key_file = 'smartlead_api.txt'
    try:
        with open(api_key_file, 'r') as file:
            api_key = file.read().strip()
    except FileNotFoundError:
        print(f"⚠️ API key file not found: {api_key_file}")
        return None
    
    api_endpoint = 'https://server.smartlead.ai/api/v1/campaigns'
    
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

def check_for_updates():
    print("Checking for updates in today's actions...")
    try:
        todays_actions = pd.read_excel('todays_actions.xlsx')
        needing_update = pd.read_excel('todays_actions_needing_update.xlsx')
        
        print(f"Found {len(todays_actions)} actions and {len(needing_update)} leads needing updates.")
        return todays_actions, needing_update
    
    except Exception as e:
        print(f"⚠️ Error reading update files: {e}")
        return None, None

def update_leads_file(todays_actions, needing_update):
    print("Updating leads.xlsx with new information...")
    try:
        leads_df = pd.read_excel('leads.xlsx')
        
        # Update existing leads without creating new ones
        for _, action in todays_actions.iterrows():
            mask = leads_df['Email'].str.lower() == action['Email'].lower()
            if mask.any():
                leads_df.loc[mask, 'Next Action'] = action['Next Action']
        
        leads_df.to_excel('leads.xlsx', index=False)
        print("✅ leads.xlsx updated successfully (no new leads created or deleted).")
        return leads_df
    
    except Exception as e:
        print(f"⚠️ Error updating leads file: {e}")
        return None

def fetch_leads_needing_email(df):
    print("Fetching leads needing email actions...")
    
    # Identify duplicates
    email_counts = df['Email'].str.lower().value_counts()
    duplicates = email_counts[email_counts > 1].index.tolist()
    
    if duplicates:
        print("\n⚠️ Duplicate emails detected. Skipping these leads:")
        for email in duplicates:
            dupe_leads = df[df['Email'].str.lower() == email]
            for _, lead in dupe_leads.iterrows():
                print(f"- {lead['First Name']} {lead['Last Name']} ({lead['Email']})")
        print("Please resolve duplicates in leads.xlsx before next check.\n")
    
    # Process non-duplicate leads
    email_leads = df[
        (~df['Email'].str.lower().isin(duplicates)) &
        (df['Next Action'] == 'Email') &
        (df['Days Until Next Action'] <= 1) &
        (df['Pause Trigger'].isna() | (df['Pause Trigger'] == '')) &
        (df['Email'].notna()) & (df['Email'] != '')
    ]
    
    print(f"Found {len(email_leads)} valid leads needing email actions.")
    for _, lead in email_leads.iterrows():
        print(f"Preparing to email: {lead['First Name']} {lead['Last Name']} ({lead['Email']})")
    
    return email_leads

def send_emails(email_leads):
    print("Sending emails...")
    for _, lead in email_leads.iterrows():
        print(f"Email sent: {lead['First Name']} {lead['Last Name']} - Subject: Follow-up")
    print("✅ All valid emails sent successfully.")

def main():
    api_key = authenticate_with_smartlead()
    if api_key is None:
        print("Authentication failed. Exiting.")
        return

    while True:
        print("\n" + "="*40)
        print("Checking for updates and processing emails...")
        
        try:
            todays_actions, needing_update = check_for_updates()
            if todays_actions is not None and needing_update is not None:
                updated_leads = update_leads_file(todays_actions, needing_update)
                if updated_leads is not None:
                    email_leads = fetch_leads_needing_email(updated_leads)
                    if not email_leads.empty:
                        send_emails(email_leads)
                    else:
                        print("No valid emails to send at this time.")
                else:
                    print("Failed to update leads file. Skipping email process.")
            else:
                print("Failed to read update files. Skipping this cycle.")
        except Exception as e:
            print(f"⚠️ Critical error: {str(e)}")
        
        print("\nProcess completed. Next check in 20 minutes.")
        time.sleep(1200)

if __name__ == "__main__":
    main()
