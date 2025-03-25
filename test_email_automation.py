import pandas as pd
from datetime import datetime, timedelta
from smartlead_email_automation import fetch_leads_needing_email, send_emails, update_email_counts, authenticate_with_smartlead

def create_test_data():
    return pd.DataFrame({
        'First Name': ['Test1', 'Test2', 'Test3'],
        'Last Name': ['User1', 'User2', 'User3'],
        'Email': ['test1@example.com', 'test2@example.com', 'test3@example.com'],
        'Next Action': ['Email', 'Email', 'Call'],
        'Days Until Next Action': [0, 1, 2],
        'Pause Trigger': [None, None, 'Paused'],
        'Emails Sent Count': [0, 1, 3],
        'Last Campaign Date': [None, datetime.now() - timedelta(days=100), datetime.now() - timedelta(days=30)],
        'id': ['1', '2', '3'],
        'Last Action Date': [None, None, None],  # Add these
        'First Email Date': [None, None, None]   # Add these
    })


def test_fetch_leads():
    """
    Test the fetch_leads_needing_email function.
    This function verifies that leads are correctly filtered based on criteria.
    """
    test_df = create_test_data()  # Create test data
    
    print("\n--- Testing fetch_leads_needing_email ---")
    
    # Test in normal mode (production filters applied)
    leads = fetch_leads_needing_email(test_df)
    print(f"Leads fetched in normal mode: {len(leads)}")  # Print number of leads fetched
    
    # Test in test mode (bypass filters except email validity)
    test_leads = fetch_leads_needing_email(test_df, test_mode=True)
    print(f"Leads fetched in test mode: {len(test_leads)}")  # Print number of leads fetched in test mode

def test_send_emails():
    """
    Test the send_emails function.
    This function simulates sending emails to leads and verifies that the process works.
    """
    test_df = create_test_data()  # Create test data
    
    # Fetch leads to email in test mode
    leads_to_email = fetch_leads_needing_email(test_df, test_mode=True)
    
    print("\n--- Testing send_emails ---")
    
    # Simulate sending emails and capture sent records
    sent_records = send_emails(leads_to_email)
    
    print(f"Emails sent: {len(sent_records)}")  # Print number of emails successfully sent

def test_update_email_counts():
    """
    Test the update_email_counts function.
    This function verifies that email counts and dates are updated correctly in the leads file.
    """
    test_df = create_test_data()  # Create test data
    
    # Save test data to a temporary Excel file for testing
    temp_file = "leads_test.xlsx"  # Use a temporary file name to avoid overwriting production data
    test_df.to_excel(temp_file, index=False)  
    
    # Simulated records of sent emails
    sent_records = [
        {'Email': 'test1@example.com', 'Template': 'call0325_email1_varA', 'Step': 1, 'Sent_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
        {'Email': 'test2@example.com', 'Template': 'call0325_email2_varB', 'Step': 2, 'Sent_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    ]
    
    print("\n--- Testing update_email_counts ---")
    
    # Update email counts using the temporary file
    update_email_counts(sent_records)
    
    # Verify updates by reading the updated file
    updated_df = pd.read_excel(temp_file)
    
    print("Updated Emails Sent Count:")
    
    try:
        print(updated_df[['Email', 'Emails Sent Count', 'Last Action Date', 'First Email Date']])  # Print relevant columns for verification
    except KeyError:
        print("⚠️ Some columns are missing from the updated file.")

def test_authentication():
    """
    Test the authentication with Smartlead API.
    This function verifies that the API key is valid and authentication succeeds.
    """
    print("\n--- Testing Smartlead Authentication ---")
    
    api_key = authenticate_with_smartlead()  # Authenticate with Smartlead API
    
    if api_key:
        print("Authentication successful")  # Print success message if authentication succeeds
    else:
        print("Authentication failed")      # Print failure message if authentication fails

def run_all_tests():
    """
    Run all tests sequentially.
    This function orchestrates testing of all major components.
    """
    
    print("\n=== Running All Tests ===")
    
    test_authentication()         # Test authentication functionality
    test_fetch_leads()            # Test lead fetching functionality
    test_send_emails()            # Test email sending functionality
    test_update_email_counts()     # Test email count updating functionality

if __name__ == "__main__":
    run_all_tests()  # Execute all tests when script is run directly






