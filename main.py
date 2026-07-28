import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Working Free Fire API Endpoints
API_ENDPOINTS = [
    "https://glob-info2.vercel.app/info",
    "https://free-fire-virtex-api.vercel.app/info"
]

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
        "👋 **Welcome to Free Fire Info Bot!**\n\n"
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

    data = None
    # Try endpoints sequentially if one fails
    for api_url in API_ENDPOINTS:
        try:
            response = requests.get(f"{api_url}?uid={uid}&region={region}", timeout=8)
            if response.status_code == 200:
                json_res = response.json()
                if "basicInfo" in json_res or "AccountInfo" in json_res:
                    data = json_res
                    break
        except Exception:
            continue

    if data:
        basic = data.get("basicInfo") or data.get("AccountInfo") or {}
        clan = data.get("clanBasicInfo") or data.get("GuildInfo") or {}

        message = (
            f"🎮 **FREE FIRE PLAYER PROFILE**\n"
            f"───────────────\n"
            f"👤 **Name:** {basic.get('nickname', basic.get('AccountName', 'N/A'))}\n"
            f"🆔 **UID:** `{uid}`\n"
            f"🌍 **Server:** {region_name}\n"
            f"⭐ **Level:** {basic.get('level', basic.get('AccountLevel', 'N/A'))}\n"
            f"👍 **Likes:** {basic.get('liked', basic.get('AccountLikes', 'N/A'))}\n"
            f"🏆 **BR Rank Points:** {basic.get('rankingPoints', 'N/A')}\n"
            f"💥 **CS Rank Points:** {basic.get('csRankingPoints', 'N/A')}\n\n"
            f"🛡️ **GUILD DETAILS**\n"
            f"🏰 **Guild Name:** {clan.get('clanName', clan.get('GuildName', 'No Guild'))}\n"
            f"👑 **Leader UID:** `{clan.get('leaderId', clan.get('GuildLeaderID', 'N/A'))}`\n"
            f"───────────────"
        )
        await update.message.reply_text(message, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ UID `{uid}` ki details nahi mil payi. Server API response nahi de raha hai.", parse_mode="Markdown")

def main():
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN Environment Variable nahi mila!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", id_info))
    
    print("🤖 Bot started successfully...")
    app.run_polling()

if __name__ == '__main__':
    main()
