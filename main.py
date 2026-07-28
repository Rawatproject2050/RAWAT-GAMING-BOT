import os
import logging
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Dummy Flask server to keep Render Free Web Service happy
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "RAWAT GAMING BOT: ONLINE 24/7"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# Region Codes & Names
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

def get_ff_profile_direct(uid: str, region: str):
    """
    Direct Garena API Fetcher using Guest Auth Engine
    """
    try:
        # Garena Guest Gateway Session Endpoints
        auth_url = f"https://clientbp.ggonesvc.com/guest_login?region={region.upper()}"
        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19CI Build/RP1A.200720.011)",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-GA": "v1 1"
        }
        
        # Request Guest Token
        auth_res = requests.get(auth_url, headers=headers, timeout=5)
        
        # Profile Query Endpoint
        profile_url = f"https://freefire-virtex-public-api.vercel.app/api/v2/info?uid={uid}&region={region}"
        
        # AlternativeDirect Public Gateway
        res = requests.get(profile_url, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if "basicInfo" in data or "AccountInfo" in data or "nickname" in data:
                return data

        # Fallback Direct Gateway
        fallback_url = f"https://ff-api-ind.vercel.app/api/info?uid={uid}&region={region}"
        f_res = requests.get(fallback_url, timeout=8)
        if f_res.status_code == 200:
            return f_res.json()

    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        return None
    return None

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

    data = get_ff_profile_direct(uid, region)

    if data:
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
        await update.message.reply_text(f"⚠️ UID `{uid}` ki details nahi mili. Kripya UID aur Server check karein.", parse_mode="Markdown")

def main():
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN Environment Variable nahi mila!")
        return

    # Start Flask Web Server
    threading.Thread(target=run_web_server, daemon=True).start()

    # Telegram Bot Polling
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", id_info))
    
    print("🤖 Bot running successfully...")
    app.run_polling()

if __name__ == '__main__':
    main()
