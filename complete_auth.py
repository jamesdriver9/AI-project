import json
from google_auth_oauthlib.flow import InstalledAppFlow

# 1. Load your credentials
with open('credentials.json', 'r') as f:
    config = json.load(f)

# 2. Setup the flow
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
flow = InstalledAppFlow.from_client_config(config, SCOPES)
flow.redirect_uri = 'http://localhost'

# 3. Generate the URL
auth_url, _ = flow.authorization_url(prompt='consent')

print("\n1. OPEN THIS URL IN YOUR BROWSER:")
print(auth_url)

# 4. Wait for you to paste the code
code = input("\n2. PASTE THE 'CODE' FROM THE BROKEN LOCALHOST URL HERE: ").strip()

# 5. Exchange the code for the real token (This carries the verifier automatically)
print("\n📡 Exchanging code for tokens...")
flow.fetch_token(code=code)

# 6. Save the final token.json
with open('token.json', 'w') as f:
    # We save the full credentials data including access/refresh tokens
    creds = flow.credentials
    token_dict = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
        "expiry": creds.expiry.isoformat() if creds.expiry else None
    }
    json.dump(token_dict, f, indent=2)

print("\n✅ SUCCESS! token.json is created. You can now run 'docker compose up -d'.")