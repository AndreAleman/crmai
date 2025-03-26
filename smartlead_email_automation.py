import requests
import os
import pandas as pd
from datetime import datetime
import time
import logging
import random


# Set up logging to track script execution and errors
logging.basicConfig(filename='email_automation.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def authenticate_with_smartlead():
    """
    Authenticate with the Smartlead API using the API key stored in a file.
    Returns the API key if authentication is successful, otherwise returns None.
    """
    print("Step 1: Authenticating with Smartlead API...")
    try:
        # Read the API key from a text file
        with open('smartlead_api.txt', 'r') as file:
            api_key = file.read().strip()
        
        # Make an API call to verify the key and retrieve campaigns
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
    """
    Check for updates in today's actions and leads needing updates by reading Excel files.
    Returns two DataFrames: todays_actions and needing_update.
    """
    print("Checking for updates in today's actions...")
    try:
        # Read data from Excel files
        todays_actions = pd.read_excel('todays_actions.xlsx')
        needing_update = pd.read_excel('todays_actions_needing_update.xlsx')
        
        # Print the number of actions and leads found
        print(f"Found {len(todays_actions)} actions and {len(needing_update)} leads needing updates.")
        return todays_actions, needing_update
    except Exception as e:
        print(f"⚠️ File read error: {e}")
        return None, None

def update_leads_file(todays_actions, needing_update):
    """
    Update the leads.xlsx file with new information from today's actions.
    Ensures the 'Emails Sent Count' column exists and saves updates back to the file.
    """
    print("Updating leads.xlsx with new information...")
    try:
        # Read leads data from Excel file
        leads_df = pd.read_excel('leads.xlsx')
        
        # Ensure 'Emails Sent Count' column exists; initialize if missing
        if 'Emails Sent Count' not in leads_df.columns:
            leads_df['Emails Sent Count'] = 0
        
        # Save updates back to the Excel file (custom logic can be added here)
        leads_df.to_excel('leads.xlsx', index=False)
        
        print("✅ leads.xlsx updated successfully (no new leads created or deleted).")
        return leads_df
    except Exception as e:
        print(f"⚠️ Update error: {e}")
        return None

def fetch_leads_needing_email(df, test_mode=False):
    """
    Identify leads that need emails based on filters. 
    In test mode, bypass filters except email validity checks.
    """
    try:
        # Ensure 'Emails Sent Count' column exists and handle missing values
        df['Emails Sent Count'] = df.get('Emails Sent Count', 0).fillna(0).astype(int)
        
        if test_mode:
            # TEST MODE: Include all valid emails without filtering other criteria
            valid_leads = df[
                (df['Email'].notna()) & 
                (df['Email'] != '')
            ].copy()
            print("🛠️ TEST MODE: Bypassing all filters except email validity")
        else:
            # PRODUCTION MODE: Apply filters to find eligible leads for email sending
            valid_leads = df[
                (df['Next Action'] == 'Email') &
                (df['Days Until Next Action'] <= 1) &
                (df['Pause Trigger'].isna()) &
                (df['Emails Sent Count'] < 4)
            ].copy()

        # Remove duplicate emails from the filtered list
        email_counts = valid_leads['Email'].str.lower().value_counts()
        duplicates = email_counts[email_counts > 1].index.tolist()
        clean_leads = valid_leads[~valid_leads['Email'].str.lower().isin(duplicates)]
        
        if not test_mode and len(duplicates) > 0:
            print(f"⚠️ Skipped {len(valid_leads)-len(clean_leads)} duplicate emails")

        # Check if lead was part of another campaign within the last 3 months (production mode only)
        if not test_mode:
            recent_campaign_leads = []
            for _, lead in clean_leads.iterrows():
                if 'Last Campaign Date' in lead and lead['Last Campaign Date'] and (datetime.now() - lead['Last Campaign Date']).days < 90:
                    recent_campaign_leads.append(lead['Email'])
            final_leads = clean_leads[~clean_leads['Email'].isin(recent_campaign_leads)]
        else:
            final_leads = clean_leads
        
        # Print results of filtering process
        print(f"Found {len(final_leads)} valid leads needing email actions.")
        for _, lead in final_leads.iterrows():
            print(f"Preparing to email: {lead['First Name']} {lead['Last Name']} ({lead['Email']})")
        
        return final_leads
    
    except Exception as e:
        print(f"⚠️ Fetch error: {e}")
        return pd.DataFrame()

def update_email_counts(sent_records, file_path='leads.xlsx'):
    print("Updating completion dates...")
    try:
        leads_df = pd.read_excel(file_path)
        
        for record in sent_records:
            mask = leads_df['Email'] == record['Email']
            leads_df.loc[mask, 'Emails Sent Count'] += 1
            leads_df.loc[mask, 'Last Action Date'] = record['Sent_Date']
            
            # Update First Email Date only if it's empty
            if pd.isnull(leads_df.loc[mask, 'First Email Date']).any():
                leads_df.loc[mask, 'First Email Date'] = record['Sent_Date']
        
        leads_df.to_excel(file_path, index=False)
        print("✅ Completion dates updated successfully.")
    except Exception as e:
        print(f"⚠️ Error updating completion dates: {e}")

    return leads_df  # Return the updated DataFrame


def get_template_name(email_step, campaign_date="0325"):
    """
    Determine the template name based on email step and available variations.
    """
    base_name = f"call{campaign_date}_email{email_step}"
    variations = ['A', 'B']
    
    # Check if varA exists
    if template_exists(f"{base_name}_varA"):
        # Check if varB exists
        if template_exists(f"{base_name}_varB"):
            # Both A and B exist, randomly choose
            variation = random.choice(variations)
        else:
            # Only A exists
            variation = 'A'
    else:
        # No variations, use base template
        return base_name
    
    return f"{base_name}_var{variation}"

def template_exists(template_name):
    """
    Check if a template exists in Smartlead.
    This is a placeholder function - you'll need to implement the actual check.
    """
    # TODO: Implement actual check, possibly via Smartlead API
    return True  # Placeholder return







def send_emails(email_leads):
    print("Adding leads to email campaigns...")
    sent_records = []
    
    try:
        with open('smartlead_api.txt', 'r') as f:
            API_KEY = f.read().strip()
        
        for _, lead in email_leads.iterrows():
            try:
                email_step = lead['Emails Sent Count'] + 1
                
                # Determine the appropriate campaign based on email step
                if email_step == 1:
                    campaign_id = "1669416"  # call0325_email1
                    campaign_name = "call0325_email1"
                elif email_step == 2:
                    campaign_id = "1715364"  # call0325_email2
                    campaign_name = "call0325_email2"
                elif email_step == 3:
                    campaign_id = "1715373"  # call0325_email3
                    campaign_name = "call0325_email3"
                else:
                    print(f"⚠️ Skipping lead {lead['Email']}: Maximum email step reached")
                    continue
                
                # Print which campaign the lead will be added to
                print(f"Adding lead {lead['Email']} to campaign: {campaign_name} (ID: {campaign_id})")
                
                # Prepare payload with lead information, including Technology field
                payload = {
                    "lead_list": [{
                        "email": lead['Email'],
                        "first_name": lead['First Name'],
                        "last_name": lead['Last Name'],
                        "custom_fields": {
                            "Technology": lead['Technology']  # Include Technology field
                        }
                    }]
                }
                
                # Send POST request to Smartlead API
                SMARTLEAD_URL = f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/leads?api_key={API_KEY}"
                response = requests.post(SMARTLEAD_URL, json=payload)
                
                if response.status_code == 200:
                    print(f"✅ Lead added to campaign: {lead['Email']} - Campaign: {campaign_name} (ID: {campaign_id})")
                    sent_records.append({
                        'Email': lead['Email'],
                        'Campaign': campaign_id,
                        'Step': email_step,
                        'Sent_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                else:
                    print(f"⚠️ Failed to add lead to campaign: {lead['Email']} - Error: {response.text}")
            
            except Exception as e:
                print(f"⚠️ Error processing lead {lead['Email']}: {str(e)}")
    
    except Exception as e:
        print(f"🚨 Critical error in send_emails: {str(e)}")
    
    print(f"\nTotal leads added to campaigns: {len(sent_records)}")
    return sent_records


















def get_operation_mode():
    while True:
        mode = input("Run in automation mode? (yes/no): ").lower()
        if mode in ['yes', 'no']:
            return mode == 'yes'
        print("Please enter 'yes' or 'no'.")

def confirm_email_sends(email_leads):
    # Define campaign IDs
    campaign_ids = {
        1: "1669416",  # call0325_email1
        2: "1715364",  # call0325_email2
        3: "1715373",  # call0325_email3
    }
    
    # Determine the campaign for each lead
    email_leads['Campaign'] = email_leads['Emails Sent Count'].apply(lambda x: campaign_ids.get(x+1, "Unknown"))
    email_leads['Campaign Name'] = email_leads['Emails Sent Count'].apply(lambda x: f"call0325_email{x+1}")
    
    # Save leads with campaign information to Excel
    email_leads.to_excel('leads_to_email.xlsx', index=False)
    print("Leads to be emailed have been saved to 'leads_to_email.xlsx'")
    
    # Display campaign information
    for _, lead in email_leads.iterrows():
        print(f"Lead: {lead['Email']} - Campaign: {lead['Campaign Name']} (ID: {lead['Campaign']})")
    
    while True:
        confirm = input("Proceed with adding these leads to campaigns? (yes/no): ").lower()
        if confirm == 'yes':
            return True
        elif confirm == 'no':
            return False
        print("Please enter 'yes' or 'no'.")



def main():
    api_key = authenticate_with_smartlead()
    
    if not api_key:
        logging.error("Authentication failed. Exiting.")
        return

    automation_mode = get_operation_mode()
    cycle_count = 0

    while True:
        cycle_count += 1
        logging.info(f"Starting automation cycle {cycle_count}")
        
        print(f"\n{'='*40}\nCycle {cycle_count}: Checking for updates and processing emails...")
        
        try:
            todays_actions, needing_update = check_for_updates()
            
            if todays_actions is not None and needing_update is not None:
                updated_leads = update_leads_file(todays_actions, needing_update)
                
                if updated_leads is not None:
                    email_leads = fetch_leads_needing_email(updated_leads)
                    
                    if not email_leads.empty:
                        if not automation_mode:
                            if confirm_email_sends(email_leads):
                                sent_records = send_emails(email_leads)
                            else:
                                print("Email sending cancelled by user.")
                                continue
                        else:
                            sent_records = send_emails(email_leads)
                        
                        if sent_records:
                            update_email_counts(sent_records)
                            logging.info(f"Successfully sent {len(sent_records)} emails")
                        else:
                            logging.warning("No emails were sent in this cycle")
                    else:
                        logging.info("No leads needing emails at this time")
                else:
                    logging.warning("Failed to update leads file")
            else:
                logging.warning("No updates or actions found")
            
            print(f"Cycle {cycle_count} completed. Next check in 20 minutes.")
            logging.info(f"Automation cycle {cycle_count} completed")
            
            time.sleep(1200)  # Wait for 20 minutes before next cycle
            
        except KeyboardInterrupt:
            logging.info("Process stopped by user")
            print("\n🛑 Process stopped by user")
            break
        
        except Exception as e:
            logging.error(f"Critical error in cycle {cycle_count}: {str(e)}")
            print(f"⚠️ Critical error in cycle {cycle_count}: {e}")
            
            time.sleep(1200)

if __name__ == "__main__":
    main()
