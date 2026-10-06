
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json",
    scopes=["https://www.googleapis.com/auth/youtube.upload"]
)

creds = flow.run_local_server(port=0)
open("token.json","w").write(creds.to_json())
print("✅ token.json CREATED! Upload it to GitHub + Render")