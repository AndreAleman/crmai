import pandas as pd  # Import pandas library for data manipulation
from datetime import datetime, date  # Import datetime for date operations
import os  # Import os for file path operations

def load_and_prepare_data():
    print("Step 1: Loading and preparing data...")  # Print status message
    try:
        # Define file path
        folder = os.path.expanduser("~/Documents/crmai")  # Get the full path to the crmai folder
        file_name = "leads.xlsx"  # Set the name of the Excel file
        file_path = os.path.join(folder, file_name)  # Combine folder path and file name
        
        # Load Excel file
        df = pd.read_excel(file_path)  # Read the Excel file into a pandas DataFrame
        print("Excel file loaded successfully!")  # Print success message
        
        # Convert date columns to datetime
        date_columns = ['Start Date', 'Last Date']  # List of columns to convert to datetime
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')  # Convert column to datetime, invalid values become NaT
            print(f"Converted '{col}' to datetime.")  # Print conversion confirmation
        
        # Calculate Days Since Start
        df['Days Since Start'] = (datetime.now() - df['Start Date']).dt.days  # Calculate days between now and Start Date
        print("Calculated 'Days Since Start'.")  # Print calculation confirmation
        
        # Show sample data
        print("\nSample Data After Preparation:")
        print(df[['First Name', 'Last Name', 'Start Date', 'Days Since Start']].head())  # Print first 5 rows of selected columns
        
        return df  # Return the prepared DataFrame
    
    except FileNotFoundError:
        print(f"File not found: {file_path}")  # Print error if file is not found
        return None  # Return None if there's an error
    except Exception as e:
        print(f"An error occurred: {e}")  # Print any other error that occurs
        return None  # Return None if there's an error


# Add this new function after load_and_prepare_data()
def filter_active_leads(df):
    print("Step 2: Filtering active leads...")
    
    # Count total leads before filtering
    total_leads = len(df)
    
    # Filter out leads where 'Pause Trigger' is not blank
    active_leads = df[df['Pause Trigger'].isna() | (df['Pause Trigger'] == '')]
    
    # Count active leads after filtering
    active_lead_count = len(active_leads)
    
    print(f"Total leads: {total_leads}")
    print(f"Active leads: {active_lead_count}")
    print(f"Paused leads: {total_leads - active_lead_count}")
    
    return active_leads


def filter_active_leads(df):
    print("Step 2: Filtering active leads...")
    
    # Create an explicit copy of the filtered DataFrame to avoid SettingWithCopyWarning
    active_leads = df[(df['Pause Trigger'].isna()) | (df['Pause Trigger'] == '')].copy()
    
    # Count total leads before filtering
    total_leads = len(df)
    
    # Count active leads after filtering
    active_lead_count = len(active_leads)
    
    print(f"Total leads: {total_leads}")
    print(f"Active leads: {active_lead_count}")
    print(f"Paused leads: {total_leads - active_lead_count}")
    
    return active_leads

def determine_next_action(df):
    print("Step 3: Determining next action for each lead...")
    
    # Generate a list of all action columns (e.g., Day 1 Action 1, Day 4 Action 1)
    action_columns = [col for col in df.columns if col.startswith('Day') and 'Action' in col and not col.endswith('Complete Date')]
    
    # Define a function to find the next incomplete action for each row
    def find_next_action(row):
        # Iterate through each action column
        for action_col in action_columns:
            # Generate the name of the corresponding completion date column
            complete_col = action_col + ' Complete Date'
            # Check if the completion date is null (action not completed)
            if pd.isnull(row[complete_col]):
                # Return the action column name and the action itself
                return action_col, row[action_col]
        # If all actions are completed, return None for both
        return None, None

    # Use .loc to assign new columns and avoid SettingWithCopyWarning
    df.loc[:, 'Next Action Column'], df.loc[:, 'Next Action'] = zip(*df.apply(find_next_action, axis=1))
    
    print("Next actions determined.")
    return df

def split_and_save_todays_actions(df):
    print("Step 5: Splitting and saving today's actions...")
    
    # Filter leads needing action today (Days Until Next Action <= 0)
    todays_actions = df[df['Days Until Next Action'] <= 0].copy()
    
    # Split into two groups:
    # - Leads with actions defined (`Next Action` is not empty)
    # - Leads needing updates (`Next Action` is empty)
    actionable_leads = todays_actions[todays_actions['Next Action'].notna()]
    needs_update_leads = todays_actions[todays_actions['Next Action'].isna()]
    
    try:
        # Save actionable leads to "todays_actions.xlsx"
        actionable_path = os.path.join(os.path.expanduser("~/Documents/crmai"), "todays_actions.xlsx")
        actionable_leads.to_excel(actionable_path, index=False)
        print(f"✅ Actionable leads saved to: {actionable_path}")
        
        # Save leads needing updates to "todays_actions_needing_update.xlsx"
        needs_update_path = os.path.join(os.path.expanduser("~/Documents/crmai"), "todays_actions_needing_update.xlsx")
        needs_update_leads.to_excel(needs_update_path, index=False)
        print(f"✅ Leads needing updates saved to: {needs_update_path}")
        
    except Exception as e:
        print(f"⚠️ Error saving files: {e}")
    
    return actionable_leads, needs_update_leads




def split_and_save_todays_actions(df):
    print("Step 5: Splitting and saving today's actions...")
    
    # Filter leads needing action today (Days Until Next Action <= 0)
    todays_actions = df[df['Days Until Next Action'] <= 0].copy()
    
    # Split into two groups:
    # - Leads with actions defined (`Next Action` is not empty)
    # - Leads needing updates (`Next Action` is empty)
    actionable_leads = todays_actions[todays_actions['Next Action'].notna()]
    needs_update_leads = todays_actions[todays_actions['Next Action'].isna()]
    
    try:
        # Save actionable leads to "todays_actions.xlsx"
        actionable_path = os.path.join(os.path.expanduser("~/Documents/crmai"), "todays_actions.xlsx")
        actionable_leads.to_excel(actionable_path, index=False)
        print(f"✅ Actionable leads saved to: {actionable_path}")
        
        # Save leads needing updates to "todays_actions_needing_update.xlsx"
        needs_update_path = os.path.join(os.path.expanduser("~/Documents/crmai"), "todays_actions_needing_update.xlsx")
        needs_update_leads.to_excel(needs_update_path, index=False)
        print(f"✅ Leads needing updates saved to: {needs_update_path}")
        
    except Exception as e:
        print(f"⚠️ Error saving files: {e}")
    
    return actionable_leads, needs_update_leads


def calculate_days_until_next_action(df):
    print("Step 4: Calculating days until next action...")
    
    def days_until_next(row):
        if pd.notnull(row['Next Action Column']):
            day_number = int(row['Next Action Column'].split(' ')[1])
            return day_number - row['Days Since Start']
        return None
    
    df['Days Until Next Action'] = df.apply(days_until_next, axis=1)
    
    print("Days until next actions calculated.")
    return df



if __name__ == "__main__":
    df = load_and_prepare_data()
    if df is not None:
        print("\nStep 1 completed successfully!")
        active_df = filter_active_leads(df)
        print("\nStep 2 completed successfully!")
        active_df = determine_next_action(active_df)
        print("\nStep 3 completed successfully!")
        active_df = calculate_days_until_next_action(active_df)
        print("\nStep 4 completed successfully!")
        
        # Step 5: Split and save today's actions
        actionable_df, needs_update_df = split_and_save_todays_actions(active_df)
        print("\nStep 5 completed successfully!")
        
        # Print samples
        print("\nSample of actionable leads today:")
        print(actionable_df[['First Name', 'Last Name', 'Next Action Column', 'Next Action']].head())
        
        print("\nSample of leads needing updates:")
        print(needs_update_df[['First Name', 'Last Name', 'Next Action Column']].head())
