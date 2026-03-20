import json
import os

# PASTE YOUR CODE FROM THE BROWSER HERE
AUTH_CODE = "PASTE_YOUR_CODE_HERE"

# This mimics the format the MCP server expects
token_data = {
    "code": AUTH_CODE,
    "redirect_uri": "http://localhost"
}

with open("token.json", "w") as f:
    json.dump(token_data, f)

print("✅ Manual token.json created. Try running 'docker compose up -d' now!")