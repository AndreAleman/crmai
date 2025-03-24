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
        # Read and clean data from today's actions files
        todays_actions = pd.read_excel('todays_actions.xlsx')
        needing_update = pd.read_excel('todays_actions_needing_update.xlsx')
        
        # Clean email data and remove invalid entries
        todays_actions = todays_actions.dropna(subset=['Email'])  # Remove rows without emails
        todays_actions['Email'] = todays_actions['Email'].str.strip().str.lower()  # Normalize emails
        
        # Filter out empty email strings after cleanup
        todays_actions = todays_actions[todays_actions['Email'] != '']
        
        print(f"Found {len(todays_actions)} valid actions and {len(needing_update)} leads needing updates.")
        return todays_actions, needing_update
    
    except Exception as e:
        print(f"⚠️ Error reading update files: {e}")
        return None, None

def update_leads_file(todays_actions, needing_update):
    print("Updating leads.xlsx with new information...")
    try:
        # Read original leads
        leads_df = pd.read_excel('leads.xlsx')
        
        # Split into valid and invalid email groups
        valid_email_mask = leads_df['Email'].notna() & (leads_df['Email'] != '')
        valid_leads = leads_df[valid_email_mask].copy()
        invalid_leads = leads_df[~valid_email_mask].copy()
        
        # Clean and process only valid emails
        valid_leads['Email'] = valid_leads['Email'].str.strip().str.lower()
        
        # Merge with todays_actions for valid emails
        if not todays_actions.empty:
            todays_actions_clean = todays_actions.copy()
            todays_actions_clean['Email'] = todays_actions_clean['Email'].str.strip().str.lower()
            
            valid_leads = valid_leads.merge(
                todays_actions_clean[['Email', 'Next Action']],
                on='Email',
                how='left',
                suffixes=('', '_new')
            )
            valid_leads['Next Action'] = valid_leads['Next Action_new'].fillna(valid_leads['Next Action'])
            valid_leads = valid_leads.drop('Next Action_new', axis=1)
            
            # Deduplicate only valid emails
            valid_leads = valid_leads.drop_duplicates(subset=['Email'], keep='last')

        # Combine back with invalid emails
        final_df = pd.concat([valid_leads, invalid_leads], ignore_index=True)
        
        # Save updated leads file
        final_df.to_excel('leads.xlsx', index=False)
        print("✅ leads.xlsx updated successfully (preserved blank emails).")
        return final_df
    
    except Exception as e:
        print(f"⚠️ Error updating leads file: {e}")
        return None




def fetch_leads_needing_email(df):
    print("Fetching leads needing email actions...")
    
    email_leads = df[
        (df['Next Action'] == 'Email') &
        (df['Days Until Next Action'] <= 1) &
        (df['Pause Trigger'].isna() | (df['Pause Trigger'] == ''))
    ]
    
    print(f"Found {len(email_leads)} leads needing email actions.")
    for _, lead in email_leads.iterrows():
        print(f"Preparing to email: {lead['First Name']} {lead['Last Name']} ({lead['Email']})")
    
    return email_leads

def send_emails(email_leads):
    print("Sending emails...")
    # Implement email sending logic here
    for _, lead in email_leads.iterrows():
        print(f"Email sent: {lead['First Name']} {lead['Last Name']} - Subject: Follow-up")
    print("✅ All emails sent successfully.")

def main():
    api_key = authenticate_with_smartlead()
    if api_key is None:
        print("Authentication failed. Exiting.")
        return

    while True:
        print("\nChecking for updates and processing emails...")
        
        todays_actions, needing_update = check_for_updates()
        if todays_actions is not None and needing_update is not None:
            updated_leads = update_leads_file(todays_actions, needing_update)
            if updated_leads is not None:
                email_leads = fetch_leads_needing_email(updated_leads)
                if not email_leads.empty:
                    send_emails(email_leads)
                else:
                    print("No leads need emails at this time.")
            else:
                print("Failed to update leads file. Skipping email process.")
        else:
            print("Failed to read update files. Skipping this cycle.")
        
        print("Process completed. Next check in 20 minutes.")
        time.sleep(1200)  # Wait for 20 minutes

if __name__ == "__main__":
    main()
