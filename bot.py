import os
import requests
import logging
from datetime import datetime
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===================== CONFIG =====================
# ⚠️ APNA NAYA BOT TOKEN DAALO
BOT_TOKEN = "8823466338:AAGfBPBglBQHWpRZzxHH7U6_oJWV53MPoj4"

# Render ka URL (https://rawat-gaming-bot.onrender.com)
RENDER_URL = "https://rawat-gaming-bot.onrender.com"

# API Configuration
API_BASE = "https://free-ff-api-src-5plp.onrender.com/api/v1"
# =================================================

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Global bot application
bot_app = None

# ===================== API FUNCTIONS =====================

def get_player_info(uid):
    regions = ["IND", "SG", "BR", "BD", "PK"]
    
    for region in regions:
        try:
            url = f"{API_BASE}/account?region={region}&uid={uid}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            
            if "error" not in data and "basicInfo" in data:
                data["region"] = region
                return data
        except:
            continue
    
    return None

def format_player_info(data, uid):
    basic = data.get("basicInfo", {})
    social = data.get("socialInfo", {})
    clan = data.get("clanBasicInfo", {})
    captain = data.get("captainBasicInfo", {})
    pet = data.get("petInfo", {})
    credit = data.get("creditScore", {})
    
    region = data.get("region", basic.get("region", "IND"))
    
    create_time = ""
    if "accountCreateTime" in data:
        try:
            ts = int(data["accountCreateTime"])
            create_time = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
        except:
            create_time = str(data.get("accountCreateTime", "Unknown"))
    
    last_login = ""
    if "lastLoginTime" in data:
        try:
            ts = int(data["lastLoginTime"])
            last_login = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        except:
            last_login = str(data.get("lastLoginTime", "Unknown"))
    
    nickname       = basic.get("nickname", "Unknown")
    level          = basic.get("level", "?")
    likes          = basic.get("liked", basic.get("likeCount", "?"))
    exp            = basic.get("exp", basic.get("experience", "?"))
    badges         = data.get("badgeCount", data.get("badges", "?"))
    ob_version     = data.get("obVersion", "OB54")
    rank_br        = basic.get("rank", "?")
    rank_br_high   = data.get("highestRank", basic.get("highestRank", rank_br))
    br_points      = basic.get("rankPoint", data.get("brPoints", "?"))
    cs_rank        = data.get("csRank", "?")
    cs_rank_high   = data.get("csHighestRank", "?")
    cs_points      = data.get("csPoints", "?")
    bio            = data.get("signature", social.get("signature", "No Bio"))
    language       = social.get("language", data.get("language", "Language_EN"))
    pref_mode      = social.get("preferredMode", data.get("preferredMode", "ModePrefer_BR"))
    
    guild_name        = clan.get("clanName", "None")
    guild_id          = clan.get("clanId", "?")
    guild_level       = clan.get("clanLevel", "?")
    guild_members     = f"{clan.get('memberNum', '?')}/{clan.get('capacity', '?')}"
    guild_captain     = captain.get("nickname", "Unknown")
    guild_captain_uid = captain.get("accountId", "?")
    
    pet_name  = pet.get("name", "None")
    pet_level = pet.get("level", "?")
    pet_exp   = pet.get("exp", pet.get("experience", "?"))
    
    credit_score  = credit.get("score", "?")
    credit_reward = credit.get("rewardState", credit.get("reward", "?"))
    diamond_cost  = data.get("diamondCost", "?")
    
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

# ===================== BOT HANDLERS =====================

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

# ===================== FLASK WEBHOOK =====================

@app.route('/')
def home():
    return '✅ Free Fire Info Bot is running!', 200

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    if bot_app:
        try:
            update = Update.de_json(request.get_json(force=True), bot_app.bot)
            bot_app.update_queue.put_nowait(update)
        except Exception as e:
            logger.error(f"Webhook error: {e}")
    return 'OK', 200

# ===================== SET WEBHOOK FUNCTION =====================

def set_webhook():
    """Set Telegram webhook to Render URL"""
    webhook_url = f"{RENDER_URL}/{BOT_TOKEN}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    params = {"url": webhook_url}
    
    try:
        resp = requests.get(url, params=params)
        data = resp.json()
        logger.info(f"Webhook setup response: {data}")
        if data.get("ok"):
            print(f"✅ Webhook set to: {webhook_url}")
        else:
            print(f"❌ Webhook error: {data}")
    except Exception as e:
        logger.error(f"Webhook setup failed: {e}")

# ===================== BOT + FLASK STARTUP =====================

def start_bot():
    """Initialize bot and set webhook"""
    global bot_app
    
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_uid))
    
    # Initialize bot (creates update queue etc.)
    bot_app.initialize()
    
    # Set webhook
    set_webhook()
    
    print("🤖 Bot initialized with webhook mode!")
    return bot_app

# Flask pehle start hota hai, phir webhook set hota hai
with app.app_context():
    start_bot()
