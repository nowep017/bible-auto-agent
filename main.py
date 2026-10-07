from flask import Flask
import os, json, asyncio, requests, random
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from google import genai
import edge_tts
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)

# --- SECRETS FROM RENDER ENV ---
GEMINI_KEY = os.environ.get("GEMINI_KEY")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_ID = os.environ.get("PHONE_ID")
YOUR_NUMBER = os.environ.get("YOUR_NUMBER")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=prompt
)
text = response.text

def send_whatsapp(msg):
    try:
        url = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
        data = {"messaging_product":"whatsapp","to":YOUR_NUMBER,"text":{"body":msg[:3800]}}
        requests.post(url, headers=headers, json=data)
    except Exception as e: print(e)

def upload_to_youtube(video_path, title, desc):
    try:
        creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
        youtube = build("youtube","v3",credentials=creds)
        request = youtube.videos().insert(
            part="snippet,status",
            body={"snippet":{"title":title,"description":desc,"tags":["bible","jesus","shorts"],"categoryId":"22"},"status":{"privacyStatus":"public","selfDeclaredMadeForKids":False}},
            media_body=MediaFileUpload(video_path)
        )
        response = request.execute()
        vid_id = response['id']
        return f"https://youtu.be/{vid_id}"
    except Exception as e:
        print(f"YouTube Error {e}")
        return f"Upload failed: {e}"

async def make_voice(text, out="voice.mp3"):
    communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
    await communicate.save(out)
    return out

def generate_content_job():
    try:
        # Load calendar
        with open("calendar.json") as f: cal = json.load(f)
        day = datetime.now().day % len(cal)
        topic = cal[day]

        prompt = f"You are viral bible shorts agent. Topic: {topic}. Write 1 SHORT 60sec script (120 words, hook shocking US audience) + Title + Description + 3 image prompts. Format: TITLE: | SCRIPT: | DESC: | IMAGES: prompt1 | prompt2 | prompt3"
        res = model.generate_content(prompt).text

        # Parse simple
        title = f"{topic} - This Will Shock You #Shorts"
        # For demo, extract script part
        script = res[:500]

        send_whatsapp(f"🔥 GENERATING: {topic}\n\n{res[:1000]}")

        # Create voice
        asyncio.run(make_voice(script))

        # Create video from 3 AI images (using Pollinations free)
        image_prompts = ["bible cinematic dark heaven","angel glowing","jesus cross dramatic light"]
        clips = []
        for i,p in enumerate(image_prompts):
            url = f"https://image.pollinations.ai/prompt/{p}?width=1080&height=1920&nologo=true&seed={random.randint(1,9999)}"
            img_data = requests.get(url).content
            open(f"img{i}.jpg","wb").write(img_data)
            clips.append(ImageClip(f"img{i}.jpg").set_duration(3))

        audio = AudioFileClip("voice.mp3")
        video = concatenate_videoclips(clips, method="compose").set_audio(audio).set_duration(audio.duration)
        video.write_videofile("final_short.mp4", fps=24, codec="libx264", audio_codec="aac")

        # Upload
        link = upload_to_youtube("final_short.mp4", title, res[:1000])
        send_whatsapp(f"✅ LIVE NOW: {link}\nTitle: {title}\n\nYour channel is hands-free. Next auto at 6AM Ghana.")
        print(f"Uploaded: {link}")

    except Exception as e:
        print(e)
        send_whatsapp(f"Agent Error: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(generate_content_job, 'cron', hour=6, minute=0) # 6AM UTC = 6AM Ghana
scheduler.start()

@app.route("/")
def home(): return "BIBLE AGENT LIVE 24/7 ON RENDER - 6AM DAILY"

@app.route("/run-now")
def run_now():
    generate_content_job()
    return "Running - Check WhatsApp & YouTube!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
