import pandas as pd
from datetime import datetime, date
import os

def load_and_prepare_data():
    print("Step 1: Loading and preparing data...")
    try:
        # Define file path
        folder = os.path.expanduser("~/Documents/crmai")
        file_name = "leads.xlsx"
        file_path = os.path.join(folder, file_name)
        
        # Load Excel file
        df = pd.read_excel(file_path)
        print("Excel file loaded successfully!")
        
        # Convert date columns to datetime
        date_columns = ['Start Date', 'Last Date']
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            print(f"Converted '{col}' to datetime.")
        
        # Calculate Days Since Start
        df['Days Since Start'] = (datetime.now() - df['Start Date']).dt.days
        print("Calculated 'Days Since Start'.")
        
        # Determine Next Action
        action_columns = [col for col in df.columns if col.startswith('Day') and 'Action' in col and not col.endswith('Complete Date')]
        
        def find_next_action(row):
            for action_col in action_columns:
                complete_col = action_col + ' Complete Date'
                if pd.isnull(row[complete_col]):
                    return action_col, row[action_col]
            return None, None
        
        # Add Next Action Column and Next Action to the DataFrame
        df['Next Action Column'], df['Next Action'] = zip(*df.apply(find_next_action, axis=1))
        print("Next actions determined.")
        
        # Calculate Days Until Next Action
        def days_until_next(row):
            if pd.notnull(row['Next Action Column']):
                day_number = int(row['Next Action Column'].split(' ')[1])
                return day_number - row['Days Since Start']
            return None
        
        df['Days Until Next Action'] = df.apply(days_until_next, axis=1)
        print("Days until next actions calculated.")
        
        # Save the updated DataFrame back to the original Excel file
        df.to_excel(file_path, index=False)
        print("Updated Excel file saved with new columns.")
        
        # Show sample data
        print("\nSample Data After Preparation:")
        print(df[['First Name', 'Last Name', 'Start Date', 'Days Since Start', 'Next Action Column', 'Next Action', 'Days Until Next Action']].head())
        
        return df
    
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def filter_active_leads(df):
    print("Step 2: Filtering active leads...")
    
    active_leads = df[(df['Pause Trigger'].isna()) | (df['Pause Trigger'] == '')].copy()
    
    total_leads = len(df)
    active_lead_count = len(active_leads)
    
    print(f"Total leads: {total_leads}")
    print(f"Active leads: {active_lead_count}")
    print(f"Paused leads: {total_leads - active_lead_count}")
    
    return active_leads

def determine_next_action(df):
    print("Step 3: Determining next action for each lead...")
    
    action_columns = [col for col in df.columns if col.startswith('Day') and 'Action' in col and not col.endswith('Complete Date')]
    
    def find_next_action(row):
        for action_col in action_columns:
            complete_col = action_col + ' Complete Date'
            if pd.isnull(row[complete_col]):
                return action_col, row[action_col]
        return None, None

    df.loc[:, 'Next Action Column'], df.loc[:, 'Next Action'] = zip(*df.apply(find_next_action, axis=1))
    
    print("Next actions determined.")
    return df

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

def split_and_save_todays_actions(df):
    print("Step 5: Splitting and saving today's actions...")
    
    todays_actions = df[df['Days Until Next Action'] <= 0].copy()
    
    actionable_leads = todays_actions[todays_actions['Next Action'].notna()]
    needs_update_leads = todays_actions[todays_actions['Next Action'].isna()]
    
    try:
        actionable_path = os.path.join(os.path.expanduser("~/Documents/crmai"), "todays_actions.xlsx")
        actionable_leads.to_excel(actionable_path, index=False)
        print(f"✅ Actionable leads saved to: {actionable_path}")
        
        needs_update_path = os.path.join(os.path.expanduser("~/Documents/crmai"), "todays_actions_needing_update.xlsx")
        needs_update_leads.to_excel(needs_update_path, index=False)
        print(f"✅ Leads needing updates saved to: {needs_update_path}")
        
    except Exception as e:
        print(f"⚠️ Error saving files: {e}")
    
    return actionable_leads, needs_update_leads

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
        
        actionable_df, needs_update_df = split_and_save_todays_actions(active_df)
        print("\nStep 5 completed successfully!")
        
        print("\nSample of actionable leads today:")
        print(actionable_df[['First Name', 'Last Name', 'Next Action Column', 'Next Action']].head())
        
        print("\nSample of leads needing updates:")
        print(needs_update_df[['First Name', 'Last Name', 'Next Action Column']].head())
