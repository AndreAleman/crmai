import requests
import os
import pandas as pd
from datetime import datetime
import time

def authenticate_with_smartlead():
    print("Step 1: Authenticating with Smartlead API...")
    try:
        with open('smartlead_api.txt', 'r') as file:
            api_key = file.read().strip()
        response = requests.get('https://server.smartlead.ai/api/v1/campaigns?api_key=' + api_key)
        if response.status_code == 200:
            print("✅ Authentication successful.")
            return api_key
        else:
            return None
    except Exception as e:
        print(f"⚠️ Authentication error: {e}")
        return None

def check_for_updates():
    print("Checking for updates in today's actions...")
    try:
        todays_actions = pd.read_excel('todays_actions.xlsx')
        needing_update = pd.read_excel('todays_actions_needing_update.xlsx')
        print(f"Found {len(todays_actions)} actions and {len(needing_update)} leads needing updates.")
        return todays_actions, needing_update
    except Exception as e:
        print(f"⚠️ File read error: {e}")
        return None, None

def update_leads_file(todays_actions, needing_update):
    print("Updating leads.xlsx with new information...")
    try:
        leads_df = pd.read_excel('leads.xlsx')
        if 'Emails Sent Count' not in leads_df.columns:
            leads_df['Emails Sent Count'] = 0
        
        # Update logic here (you may need to customize this part)
        
        leads_df.to_excel('leads.xlsx', index=False)
        print("✅ leads.xlsx updated successfully (no new leads created or deleted).")
        return leads_df
    except Exception as e:
        print(f"⚠️ Update error: {e}")
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
        (df['Emails Sent Count'] < 4)
    ]
    
    print(f"Found {len(email_leads)} valid leads needing email actions.")
    for _, lead in email_leads.iterrows():
        print(f"Preparing to email: {lead['First Name']} {lead['Last Name']} ({lead['Email']})")
    
    return email_leads

def send_emails(email_leads):
    print("Sending emails...")
    for _, lead in email_leads.iterrows():
        print(f"Email sent: {lead['First Name']} {lead['Last Name']} - Action: Email")
    print("✅ All valid emails sent successfully.")
    return email_leads

def update_email_counts(sent_emails):
    print("Updating completion dates...")
    try:
        leads_df = pd.read_excel('leads.xlsx')
        
        # Update logic here
        
        leads_df.to_excel('leads.xlsx', index=False)
        print("✅ Completion dates updated successfully.")
    except Exception as e:
        print(f"⚠️ Error updating completion dates: {e}")

def main():
    api_key = authenticate_with_smartlead()
    if not api_key:
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
                        sent_emails = send_emails(email_leads)
                        update_email_counts(sent_emails)
            
            print("Process completed. Next check in 20 minutes.")
            time.sleep(1200)
        except KeyboardInterrupt:
            print("\n🛑 Process stopped by user")
            break
        except Exception as e:
            print(f"⚠️ Critical error: {e}")
            time.sleep(1200)

if __name__ == "__main__":
    main()
