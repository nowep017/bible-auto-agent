import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# LOAD TOKEN
creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
youtube = build("youtube", "v3", credentials=creds)

# YOUR VIDEO FOLDER
video_folder = "videos"

for file in os.listdir(video_folder):
    if file.endswith(".mp4"):
        path = os.path.join(video_folder, file)
        title = file.replace(".mp4", "")[:95] # title from filename

        print(f"Uploading {file}...")

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": f"{title}\n\n#shorts",
                    "tags": ["shorts"],
                    "categoryId": "22"
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False
                }
            },
            media_body=MediaFileUpload(path, chunksize=-1, resumable=True)
        )
        response = request.execute()
        print(f"Done! https://youtu.be/{response['id']}")

print("All uploaded!")