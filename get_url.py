import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Load your credentials
with open('credentials.json', 'r') as f:
    config = json.load(f)

# Define the scopes the AI needs to see your Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Create the flow
flow = InstalledAppFlow.from_client_config(config, SCOPES)
flow.redirect_uri = 'http://localhost'

# Generate the URL
auth_url, _ = flow.authorization_url(prompt='consent')

print("\n--- COPY AND PASTE THIS URL INTO YOUR BROWSER ---")
print(auth_url)
print("--------------------------------------------------\n")