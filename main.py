import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging setup (Render logs mein errors dekhne ke liye)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Render environment variables se token fetch karega (Safe & Secure)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Free Fire Info API
API_URL = "https://free-fire-virtex-api.vercel.app/info"

# Supported Regions Mapping
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

# /start command
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

# /info command
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

    # Auto-detect Region & UID
    if len(args) == 1:
        region = "ind"  # Default India
        uid = args[0]
    else:
        region = args[0].lower()
        uid = args[1]

    # Region Check
    if region not in SUPPORTED_REGIONS:
        await update.message.reply_text(
            f"❌ Invalid region code `{region}`!\n"
            f"Sahi codes: `ind`, `pk`, `bd`, `sg`, `br`, `na`, `sac`, `id`, `th`, `me`, `cis`", 
            parse_mode="Markdown"
        )
        return

    region_name = SUPPORTED_REGIONS[region]
    await update.message.reply_text(f"🔍 Fetching details for UID: `{uid}` ({region_name})...", parse_mode="Markdown")

    try:
        response = requests.get(f"{API_URL}?uid={uid}&region={region}", timeout=10)
        data = response.json()

        if response.status_code == 200 and "basicInfo" in data:
            basic = data.get("basicInfo", {})
            clan = data.get("clanBasicInfo", {})

            # Formatting Message
            message = (
                f"🎮 **FREE FIRE PLAYER PROFILE**\n"
                f"───────────────\n"
                f"👤 **Name:** {basic.get('nickname', 'N/A')}\n"
                f"🆔 **UID:** `{uid}`\n"
                f"🌍 **Server:** {region_name}\n"
                f"⭐ **Level:** {basic.get('level', 'N/A')} (EXP: {basic.get('exp', 'N/A')})\n"
                f"👍 **Likes:** {basic.get('liked', 'N/A')}\n"
                f"🏆 **BR Rank Points:** {basic.get('rankingPoints', 'N/A')}\n"
                f"💥 **CS Rank Points:** {basic.get('csRankingPoints', 'N/A')}\n\n"
                f"🛡️ **GUILD DETAILS**\n"
                f"🏰 **Guild Name:** {clan.get('clanName', 'No Guild')}\n"
                f"👑 **Leader UID:** `{clan.get('leaderId', 'N/A')}`\n"
                f"───────────────"
            )
            await update.message.reply_text(message, parse_mode="Markdown")
        else:
            await update.message.reply_text(f"⚠️ UID `{uid}` {region_name} server par nahi mili ya API down hai.", parse_mode="Markdown")

    except Exception:
        await update.message.reply_text("❌ Connection Error! Kripya thodi der baad try karein.")

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
