import requests
import pandas as pd

def get_smartlead_campaigns(api_key):
    """Retrieve list of campaigns from Smartlead"""
    url = "https://server.smartlead.ai/api/v1/campaigns"
    try:
        response = requests.get(url, params={"api_key": api_key})
        if response.status_code == 200:
            return response.json()
        print(f"⚠️ API Error: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        print(f"⚠️ Connection error: {e}")
        return None

def print_campaigns(campaigns):
    """Display campaigns in a readable format"""
    if not campaigns:
        print("No campaigns found")
        return
    
    df = pd.DataFrame(campaigns)[['id', 'name', 'status', 'created_at']]
    df['created_at'] = pd.to_datetime(df['created_at'])
    print("\nYour Smartlead Campaigns:")
    print(df.to_string(index=False))

def main():
    # Get API key
    try:
        with open('smartlead_api.txt', 'r') as f:
            api_key = f.read().strip()
    except FileNotFoundError:
        print("Error: smartlead_api.txt not found")
        return

    # Get campaigns
    campaigns = get_smartlead_campaigns(api_key)
    
    if campaigns:
        print_campaigns(campaigns)
    else:
        print("Failed to retrieve campaigns")

if __name__ == "__main__":
    main()
