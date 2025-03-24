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
        return api_key if response.status_code == 200 else None
    except Exception as e:
        print(f"⚠️ Authentication error: {e}")
        return None

def check_for_updates():
    try:
        todays_actions = pd.read_excel('todays_actions.xlsx')
        needing_update = pd.read_excel('todays_actions_needing_update.xlsx')
        return todays_actions, needing_update
    except Exception as e:
        print(f"⚠️ File read error: {e}")
        return None, None

def update_leads_file(todays_actions, needing_update):
    try:
        # Read leads and ensure Emails Sent Count exists
        leads_df = pd.read_excel('leads.xlsx')
        if 'Emails Sent Count' not in leads_df.columns:
            leads_df['Emails Sent Count'] = 0
            print("✅ Created Emails Sent Count column")
        
        # Update logic (modify this section with your actual update requirements)
        # ...
        
        leads_df.to_excel('leads.xlsx', index=False)
        return leads_df
    except Exception as e:
        print(f"⚠️ Update error: {e}")
        return None

def fetch_leads_needing_email(df):
    try:
        # Ensure Emails Sent Count exists and handle missing values
        df['Emails Sent Count'] = df.get('Emails Sent Count', 0).fillna(0).astype(int)
        
        # Filter valid leads
        valid_leads = df[
            (df['Email'].notna()) & 
            (df['Email'] != '') &
            (df['Next Action'] == 'Email') &
            (df['Days Until Next Action'] <= 1) &
            (df['Pause Trigger'].isna()) &
            (df['Emails Sent Count'] < 4)  # Max 4 emails in sequence
        ].copy()
        
        # Remove duplicates
        email_counts = valid_leads['Email'].str.lower().value_counts()
        duplicates = email_counts[email_counts > 1].index.tolist()
        clean_leads = valid_leads[~valid_leads['Email'].str.lower().isin(duplicates)]
        
        if len(duplicates) > 0:
            print(f"⚠️ Skipped {len(valid_leads)-len(clean_leads)} duplicate emails")
        
        return clean_leads
    except Exception as e:
        print(f"⚠️ Fetch error: {e}")
        return pd.DataFrame()

def send_emails(email_leads):
    try:
        sent_records = []
        for _, lead in email_leads.iterrows():
            # Simulate email sending
            step = lead['Emails Sent Count'] + 1
            print(f"📧 Sent email #{step} to {lead['Email']}")
            sent_records.append({
                'Email': lead['Email'],
                'Step': step,
                'Completion_Date': datetime.now().strftime('%Y-%m-%d')
            })
        return sent_records
    except Exception as e:
        print(f"⚠️ Send error: {e}")
        return []

def update_email_counts(sent_records):
    try:
        # Read current leads
        leads_df = pd.read_excel('leads.xlsx')
        
        # Ensure Emails Sent Count column exists
        if 'Emails Sent Count' not in leads_df.columns:
            leads_df['Emails Sent Count'] = 0
        
        # Update counts and dates
        for record in sent_records:
            mask = leads_df['Email'].str.lower() == record['Email'].lower()
            if any(mask):
                # Update sent count
                leads_df.loc[mask, 'Emails Sent Count'] += 1
                
                # Update completion date for specific action
                step_col = f"Day {record['Step']} Action 1 Complete Date"
                if step_col in leads_df.columns:
                    leads_df.loc[mask, step_col] = record['Completion_Date']
                
                # Update last action date
                leads_df.loc[mask, 'Last Action Date'] = record['Completion_Date']
        
        # Save updates
        leads_df.to_excel('leads.xlsx', index=False)
        print(f"✅ Updated {len(sent_records)} email counts")
    except Exception as e:
        print(f"⚠️ Count update error: {e}")

def main():
    api_key = authenticate_with_smartlead()
    if not api_key:
        print("❌ Authentication failed")
        return

    while True:
        try:
            # Check for manual updates
            todays_actions, needing_update = check_for_updates()
            
            # Process updates
            updated_leads = update_leads_file(todays_actions, needing_update)
            
            if updated_leads is not None:
                # Find leads needing emails
                email_leads = fetch_leads_needing_email(updated_leads)
                
                if not email_leads.empty:
                    # Send emails and get confirmation
                    sent_records = send_emails(email_leads)
                    
                    # Update counts and dates
                    if sent_records:
                        update_email_counts(sent_records)
            
            # Wait for next cycle
            time.sleep(1200)  # 20 minutes
            
        except KeyboardInterrupt:
            print("\n🛑 Process stopped by user")
            break
        except Exception as e:
            print(f"⚠️ Critical error: {e}")
            time.sleep(1200)

if __name__ == "__main__":
    main()
