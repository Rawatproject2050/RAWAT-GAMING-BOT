import os
import requests
import logging
from datetime import datetime
from flask import Flask, request
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===================== CONFIGURATION =====================
# ⚠️ YAHAN APNA NAYA BOT TOKEN DAALO (purana revoke karke naya banao)
BOT_TOKEN = "8823466338:AAHlfgOB4xxwpVpPCSYeUnjX6uzOSwoYR-U"

# Teri personal Telegram ID
OWNER_ID = 6665529050

# API Configuration - Free FF API (Render)
API_BASE = "https://free-ff-api-src-5plp.onrender.com/api/v1"
# =========================================================

# Flask app for Render health check
app = Flask(__name__)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global bot application instance
bot_app = None

# ===================== FREE FIRE API FUNCTIONS =====================

def get_player_info(uid):
    """Fetch player info from Free Fire API with region fallback"""
    regions = ["IND", "SG", "BR", "BD", "PK"]
    
    for region in regions:
        try:
            url = f"{API_BASE}/account?region={region}&uid={uid}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            
            if "error" not in data and "basicInfo" in data:
                data["region"] = region  # Store which region worked
                return data
        except:
            continue
    
    return None

def format_player_info(data, uid):
    """Format JSON data into the styled message template"""
    basic = data.get("basicInfo", {})
    social = data.get("socialInfo", {})
    clan = data.get("clanBasicInfo", {})
    captain = data.get("captainBasicInfo", {})
    pet = data.get("petInfo", {})
    credit = data.get("creditScore", {})
    
    region = data.get("region", basic.get("region", "IND"))
    
    # Account creation
    create_time = ""
    if "accountCreateTime" in data:
        try:
            ts = int(data["accountCreateTime"])
            create_time = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
        except:
            create_time = str(data.get("accountCreateTime", "Unknown"))
    
    # Last login
    last_login = ""
    if "lastLoginTime" in data:
        try:
            ts = int(data["lastLoginTime"])
            last_login = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        except:
            last_login = str(data.get("lastLoginTime", "Unknown"))
    
    nickname     = basic.get("nickname", "Unknown")
    level        = basic.get("level", "?")
    likes        = basic.get("liked", basic.get("likeCount", "?"))
    exp          = basic.get("exp", basic.get("experience", "?"))
    badges       = data.get("badgeCount", data.get("badges", "?"))
    ob_version   = data.get("obVersion", "OB54")
    rank_br      = basic.get("rank", "?")
    rank_br_high = data.get("highestRank", basic.get("highestRank", rank_br))
    br_points    = basic.get("rankPoint", data.get("brPoints", "?"))
    cs_rank      = data.get("csRank", "?")
    cs_rank_high = data.get("csHighestRank", "?")
    cs_points    = data.get("csPoints", "?")
    bio          = data.get("signature", social.get("signature", "No Bio"))
    language     = social.get("language", data.get("language", "Language_EN"))
    pref_mode    = social.get("preferredMode", data.get("preferredMode", "ModePrefer_BR"))
    
    guild_name       = clan.get("clanName", "None")
    guild_id         = clan.get("clanId", "?")
    guild_level      = clan.get("clanLevel", "?")
    guild_members    = f"{clan.get('memberNum', '?')}/{clan.get('capacity', '?')}"
    guild_captain    = captain.get("nickname", "Unknown")
    guild_captain_uid = captain.get("accountId", "?")
    
    pet_name  = pet.get("name", "None")
    pet_level = pet.get("level", "?")
    pet_exp   = pet.get("exp", pet.get("experience", "?"))
    
    credit_score = credit.get("score", "?")
    credit_reward = credit.get("rewardState", credit.get("reward", "?"))
    diamond_cost = data.get("diamondCost", "?")
    
    msg = f"""╭━━━━━━━━━━━━━━━━━━━━✪
│  🎮 Fʀᴇᴇ Fɪʀᴇ Pʟᴀʏᴇʀ Iɴꜰᴏ
╰━━━━━━━━━━━━━━━━━━━━✪

╭━⟮ 👤 Bᴀꜱɪᴄ Iɴꜰᴏ ⟯
│ 😺 Nᴀᴍᴇ: {nickname}
│ 🆔 Uɪᴅ: {uid}
│ 🌍 Rᴇɢɪᴏɴ: {region}
│ 🏆 Lᴇᴠᴇʟ: {level}
│ ⭐ Exᴘ: {exp}
│ ❤️ Lɪᴋᴇꜱ: {likes}
│ 🎖️ Bᴀᴅɢᴇꜱ: {badges}
│ 🔖 Oʙ Vᴇʀꜱɪᴏɴ: {ob_version}
│ 📅 Aᴄᴄᴏᴜɴᴛ Cʀᴇᴀᴛᴇᴅ: {create_time}
│ 🕐 Lᴀꜱᴛ Lᴏɢɪɴ: {last_login}
│ 💎 Dɪᴀᴍᴏɴᴅ Cᴏꜱᴛ: {diamond_cost}
╰━━━━━━━━━━━━━━━✪

╭━⟮ 🏅 Rᴀɴᴋ Iɴꜰᴏ ⟯
│ 🎯 Bʀ Rᴀɴᴋ: {rank_br}
│ 🏆 Bʀ Hɪɢʜᴇꜱᴛ Rᴀɴᴋ: {rank_br_high}
│ 🎯 Bʀ Pᴏɪɴᴛꜱ: {br_points}
│ ⚔️ Cꜱ Rᴀɴᴋ: {cs_rank}
│ 🏆 Cꜱ Hɪɢʜᴇꜱᴛ Rᴀɴᴋ: {cs_rank_high}
│ ⚔️ Cꜱ Pᴏɪɴᴛꜱ: {cs_points}
╰━━━━━━━━━━━━━━━✪

╭━⟮ 💬 Sᴏᴄɪᴀʟ Iɴꜰᴏ ⟯
│ 📝 Bɪᴏ: {bio}
│ 🌐 Lᴀɴɢᴜᴀɢᴇ: {language}
│ 🎮 Pʀᴇꜰᴇʀʀᴇᴅ Mᴏᴅᴇ: {pref_mode}
╰━━━━━━━━━━━━━━━✪

╭━⟮ 🏰 Gᴜɪʟᴅ Iɴꜰᴏ ⟯
│ 🏯 Nᴀᴍᴇ: {guild_name}
│ 🆔 Gᴜɪʟᴅ Iᴅ: {guild_id}
│ 📶 Lᴇᴠᴇʟ: {guild_level}
│ 👥 Mᴇᴍʙᴇʀꜱ: {guild_members}
│ 👑 Cᴀᴘᴛᴀɪɴ: {guild_captain} ({guild_captain_uid})
╰━━━━━━━━━━━━━━━✪

╭━⟮ 🐾 Pᴇᴛ Iɴꜰᴏ ⟯
│ 🐶 Nᴀᴍᴇ: {pet_name}
│ 📶 Lᴇᴠᴇʟ: {pet_level}
│ ⭐ Exᴘ: {pet_exp}
╰━━━━━━━━━━━━━━━✪

╭━⟮ 🛡️ Cʀᴇᴅɪᴛ Sᴄᴏʀᴇ ⟯
│ 📊 Sᴄᴏʀᴇ: {credit_score}
│ 🎁 Rᴇᴡᴀʀᴅ Sᴛᴀᴛᴇ: {credit_reward}
╰━━━━━━━━━━━━━━━✪"""
    
    return msg

# ===================== TELEGRAM BOT HANDLERS =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome to Free Fire Info Bot!*\n\n"
        "Simply send me a Free Fire UID to get full player details.\n\n"
        "Example: `2722004155`",
        parse_mode="Markdown"
    )

async def handle_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.text.strip()
    
    if not uid.isdigit() or len(uid) < 5 or len(uid) > 15:
        await update.message.reply_text(
            "❌ *Invalid UID!*\nPlease enter a valid Free Fire UID (5-15 digits).",
            parse_mode="Markdown"
        )
        return
    
    wait_msg = await update.message.reply_text("⏳ *Fetching player info...*", parse_mode="Markdown")
    
    try:
        data = get_player_info(uid)
        
        if not data:
            await wait_msg.edit_text(
                "❌ *Player not found!*\nCheck the UID and try again.",
                parse_mode="Markdown"
            )
            return
        
        formatted = format_player_info(data, uid)
        await wait_msg.edit_text(formatted, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await wait_msg.edit_text(
            f"❌ *Error fetching data!*\n`{str(e)}`\n\nTry again later.",
            parse_mode="Markdown"
        )

# ===================== FLASK WEBHOOK / HEALTH CHECK =====================

@app.route('/')
def home():
    return '✅ Free Fire Info Bot is running!', 200

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Handle Telegram webhook updates"""
    if bot_app:
        update = Update.de_json(request.get_json(force=True), bot_app.bot)
        bot_app.update_queue.put_nowait(update)
    return 'OK', 200

def run_bot():
    """Initialize and start the bot"""
    global bot_app
    
    # Build application
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_uid))
    
    # Set webhook (Render Web Service ka URL yahan daalna hoga)
    # Comment out for polling mode (development)
    # bot_app.bot.set_webhook(f"https://your-app-name.onrender.com/{BOT_TOKEN}")
    
    # Start polling (Render free tier mein polling bhi chal jayega)
    print("🤖 Bot started - polling mode")
    bot_app.run_polling()

# ===================== MAIN ENTRY POINT =====================

if __name__ == "__main__":
    import threading
    
    # Run bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Run Flask server (Render health check ke liye)
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
