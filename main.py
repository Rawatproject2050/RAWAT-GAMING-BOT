import os
import logging
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Render web server to keep the service active
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is active 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

SUPPORTED_REGIONS = {
    "ind": "India 🇮🇳",
    "pk": "Pakistan 🇵🇰",
    "bd": "Bangladesh 🇧🇩",
    "sg": "Singapore 🇸🇬",
    "br": "Brazil 🇧🇷",
    "na": "North America 🌎",
    "sac": "South America 🌎",
    "id": "Indonesia 🇮🇩",
    "th": "Thailand 🇹🇭",
    "me": "Middle East 🇸🇦",
    "cis": "Europe / CIS 🇪🇺"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to RAWAT GAMING BOT!**\n\n"
        "Aap kisi bhi Free Fire player ki UID ki details check kar sakte hain.\n\n"
        "📌 **Kaise use karein:**\n"
        "• India Server: `/info 123456789`\n"
        "• Other Servers: `/info <region> <uid>` (e.g. `/info pk 123456789`)\n\n"
        "🌍 **Available Regions:** `ind`, `pk`, `bd`, `sg`, `br`, `na`, `sac`, `id`, `th`, `me`, `cis`"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def id_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if not args:
        help_msg = (
            "❌ **Sahi format use karein!**\n\n"
            "👉 **Example (India):** `/info 123456789`\n"
            "👉 **Example (Pakistan):** `/info pk 123456789`\n\n"
            "🌍 **Available Region Codes:**\n"
            "`ind`, `pk`, `bd`, `sg`, `br`, `na`, `sac`, `id`, `th`, `me`, `cis`"
        )
        await update.message.reply_text(help_msg, parse_mode="Markdown")
        return

    if len(args) == 1:
        region = "ind"
        uid = args[0]
    else:
        region = args[0].lower()
        uid = args[1]

    if region not in SUPPORTED_REGIONS:
        await update.message.reply_text(
            f"❌ Invalid region code `{region}`!\n"
            f"Sahi codes: `ind`, `pk`, `bd`, `sg`, `br`, `na`, `sac`, `id`, `th`, `me`, `cis`", 
            parse_mode="Markdown"
        )
        return

    region_name = SUPPORTED_REGIONS[region]
    await update.message.reply_text(f"🔍 Fetching details for UID: `{uid}` ({region_name})...", parse_mode="Markdown")

    # Updated Multiple Live APIs
    api_urls = [
        f"https://free-fire-api-three.vercel.app/info?uid={uid}&region={region}",
        f"https://ff-api-ind.vercel.app/api/info?uid={uid}&region={region}",
        f"https://api.vytal.dev/ff?uid={uid}&region={region}"
    ]

    data = None
    for url in api_urls:
        try:
            res = requests.get(url, timeout=7)
            if res.status_code == 200:
                json_data = res.json()
                if "basicInfo" in json_data or "AccountInfo" in json_data or "nickname" in json_data:
                    data = json_data
                    break
        except Exception:
            continue

    if data:
        # Extracting details smoothly across different API responses
        basic = data.get("basicInfo") or data.get("AccountInfo") or data
        clan = data.get("clanBasicInfo") or data.get("GuildInfo") or {}

        name = basic.get('nickname') or basic.get('AccountName') or basic.get('Name') or 'N/A'
        level = basic.get('level') or basic.get('AccountLevel') or basic.get('Level') or 'N/A'
        likes = basic.get('liked') or basic.get('AccountLikes') or basic.get('Likes') or 'N/A'
        exp = basic.get('exp') or basic.get('AccountEXP') or 'N/A'
        br_points = basic.get('rankingPoints') or basic.get('BRRankPoint') or 'N/A'
        cs_points = basic.get('csRankingPoints') or basic.get('CSRankPoint') or 'N/A'

        guild_name = clan.get('clanName') or clan.get('GuildName') or 'No Guild'
        guild_leader = clan.get('leaderId') or clan.get('GuildLeaderID') or 'N/A'

        message = (
            f"🎮 **FREE FIRE PLAYER PROFILE**\n"
            f"───────────────\n"
            f"👤 **Name:** {name}\n"
            f"🆔 **UID:** `{uid}`\n"
            f"🌍 **Server:** {region_name}\n"
            f"⭐ **Level:** {level} (EXP: {exp})\n"
            f"👍 **Likes:** {likes}\n"
            f"🏆 **BR Rank Points:** {br_points}\n"
            f"💥 **CS Rank Points:** {cs_points}\n\n"
            f"🛡️ **GUILD DETAILS**\n"
            f"🏰 **Guild Name:** {guild_name}\n"
            f"👑 **Leader UID:** `{guild_leader}`\n"
            f"───────────────"
        )
        await update.message.reply_text(message, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ UID `{uid}` ki details nahi mili. Kripya check karein ki UID sahi hai ya thodi der baad try karein.", parse_mode="Markdown")

def main():
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN Environment Variable nahi mila!")
        return

    threading.Thread(target=run_web_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", id_info))
    
    print("🤖 Bot running on Render Web Service...")
    app.run_polling()

if __name__ == '__main__':
    main()
