import os
import time
import math
import hmac
import hashlib
import base64
import requests
import telebot
from flask import Flask
from threading import Thread

# ===================== CONFIG =====================
# Render Environment Variables se Token lega
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("⚠️ Error: BOT_TOKEN Environment Variable missing hai!")

bot = telebot.TeleBot(BOT_TOKEN)

# Secret key for Gameskinbo Token
SECRET = "GAMESKINBOFFIDCHECKERSECURITYPROTOCOL"

# ===================== KEEP ALIVE SERVER (Render Sleep Protector) =====================
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    # Render default port 8080 ya PORT env variable use karega
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# ===================== TOKEN GENERATOR =====================
def generate_token(uid: str) -> str:
    timestamp_ms = int(time.time() * 1000)
    time_block = math.floor(timestamp_ms / 30000)
    nonce = hmac.new(SECRET.encode(), str(time_block).encode(), hashlib.sha256).hexdigest()[:32]
    signature = hmac.new(nonce.encode(), f"{uid}|{timestamp_ms}".encode(), hashlib.sha256).hexdigest()
    raw = f"{uid}|{timestamp_ms}|{signature}"
    return base64.b64encode(raw.encode()).decode()

# ===================== API CALL FUNCTION =====================
import requests

def get_player_info(uid: str, region: str = "IND"):
    # Main Working FF Public APIs
    api_urls = [
        f"https://free-ff-api-src-5plp.onrender.com/api/v1/account?region={region}&uid={uid}",
        f"https://freefireinfo-zy9l.onrender.com/api/v1/search-players?keyword={uid}&server={region}"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for url in api_urls:
        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                
                # Format 1 (free-ff-api)
                if "basicInfo" in data:
                    info = data["basicInfo"]
                    return {
                        "name": info.get("nickname", "Unknown"),
                        "level": info.get("level", "N/A"),
                        "likes": info.get("liked", 0),
                        "br_rank": info.get("rankingPoints", "N/A"),
                        "region": info.get("region", region),
                        "guild_name": data.get("clanBasicInfo", {}).get("clanName", "None")
                    }
                
                # Format 2 (freefireinfo-zy9l)
                elif "infos" in data and len(data["infos"]) > 0:
                    info = data["infos"][0]
                    return {
                        "name": info.get("nickname", "Unknown"),
                        "level": info.get("level", "N/A"),
                        "likes": info.get("liked", 0),
                        "br_rank": info.get("rankingPoints", "N/A"),
                        "region": info.get("region", region),
                        "guild_name": "N/A"
                    }
        except Exception as e:
            print(f"API Attempt Failed: {e}")
            continue

    return None
# ===================== BOT COMMAND HANDLERS =====================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(
        message, 
        "👋 **Welcome to Free Fire ID Checker Bot!**\n\n"
        "Player Info dekhne ke liye command bhejein:\n"
        "`/info <UID>`\n\n"
        "**Example:** `/info 2722004155`",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['info'])
def info_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ **UID Dena bhool gaye!**\nSahi tarika: `/info 2722004155`", parse_mode="Markdown")
        return

    uid = args[1]
    if not uid.isdigit():
        bot.reply_to(message, "❌ **Error:** UID sirf numbers mein hoti hai!")
        return

    msg = bot.reply_to(message, "🔎 **Searching Player Details...**")

    # API Call
    data = get_player_info(uid, region="ind")

    if data:
        # Response Formatting
        text = f"🎮 **FREE FIRE PLAYER DETAILS** 🎮\n"
        text += f"━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"👤 **Name:** `{data.get('name', 'N/A')}`\n"
        text += f"🆔 **UID:** `{uid}`\n"
        text += f"⭐ **Level:** `{data.get('level', 'N/A')}`\n"
        text += f"👍 **Likes:** `{data.get('likes', 0):,}`\n"
        text += f"🛡️ **Guild:** `{data.get('guild_name', 'None')}`\n"
        text += f"🏆 **BR Rank:** `{data.get('br_rank', 'N/A')}`\n"
        text += f"🌐 **Region:** `{data.get('region', 'IND').upper()}`\n"
        text += f"━━━━━━━━━━━━━━━━━━━━━"

        bot.edit_message_text(text, chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text("❌ **Player Not Found!** Check karein ki UID sahi hai ya nahi.", chat_id=message.chat.id, message_id=msg.message_id)

# ===================== BOT START =====================
if __name__ == "__main__":
    print("🚀 Starting Web Server for Render Keep-Alive...")
    keep_alive()  # Web server start karega
    
    print("🤖 Bot is polling for updates...")
    bot.infinity_polling()
