import os
import asyncio
import threading
import requests
import logging
from datetime import datetime
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===================== CONFIG =====================
# ⚠️ APNA NAYA TOKEN DAALO (abhi naya banao @BotFather se)
BOT_TOKEN = "8823466338:AAGfBPBglBQHWpRZzxHH7U6_oJWV53MPoj4"

# Render URL
RENDER_URL = "https://rawat-gaming-bot.onrender.com"

# Free FF API (no key needed)
API_BASE = "https://free-ff-api-src-5plp.onrender.com/api/v1"
# =================================================

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Bot application (global)
application = None
bot_loop = None

# ===================== FREE FIRE API =====================

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
    guild_name     = clan.get("clanName", "None")
    guild_id       = clan.get("clanId", "?")
    guild_level    = clan.get("clanLevel", "?")
    guild_members  = f"{clan.get('memberNum', '?')}/{clan.get('capacity', '?')}"
    guild_captain  = captain.get("nickname", "Unknown")
    gc_uid         = captain.get("accountId", "?")
    pet_name       = pet.get("name", "None")
    pet_level      = pet.get("level", "?")
    pet_exp        = pet.get("exp", pet.get("experience", "?"))
    credit_score   = credit.get("score", "?")
    credit_reward  = credit.get("rewardState", credit.get("reward", "?"))
    diamond_cost   = data.get("diamondCost", "?")

    return f"""╭━━━━━━━━━━━━━━━━━━━━✪
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
│ 👑 Cᴀᴘᴛᴀɪɴ: {guild_captain} ({gc_uid})
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
        await update.message.reply_text("❌ *Invalid UID!*", parse_mode="Markdown")
        return

    wait_msg = await update.message.reply_text("⏳ *Fetching player info...*", parse_mode="Markdown")
    try:
        data = get_player_info(uid)
        if not data:
            await wait_msg.edit_text("❌ *Player not found!*", parse_mode="Markdown")
            return
        formatted = format_player_info(data, uid)
        await wait_msg.edit_text(formatted, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error: {e}")
        await wait_msg.edit_text(f"❌ *Error:* `{str(e)}`", parse_mode="Markdown")

# ===================== BOT INITIALIZATION (event loop + thread) =====================

def start_bot_in_background():
    global application, bot_loop

    # Naya event loop banao
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)

    # Application banao — updater None (we use webhook)
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .updater(None)
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_uid))

    # Initialize and start (ab update_queue consume karega)
    bot_loop.run_until_complete(application.initialize())
    bot_loop.run_until_complete(application.start())

    # Webhook set karo
    webhook_url = f"{RENDER_URL}/{BOT_TOKEN}"
    bot_loop.run_until_complete(application.bot.set_webhook(webhook_url))
    print(f"✅ Webhook set to: {webhook_url}")
    print("🤖 Bot is running with webhook mode!")

    # Event loop ko forever chalne do
    bot_loop.run_forever()

# ===================== FLASK ROUTES =====================

@app.route('/')
def home():
    return '✅ Free Fire Info Bot is running!', 200

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Telegram webhook endpoint — updates yahan aate hain"""
    global application, bot_loop
    if application and bot_loop:
        try:
            update = Update.de_json(request.get_json(force=True), application.bot)
            # Update ko bot ke event loop mein daal do
            asyncio.run_coroutine_threadsafe(
                application.update_queue.put(update), bot_loop
            )
        except Exception as e:
            logger.error(f"Webhook error: {e}")
    return 'OK', 200

# ===================== BOT THREAD START =====================

# Bot ko ek alag thread mein start karo taaki Flask + gunicorn saath chale
bot_thread = threading.Thread(target=start_bot_in_background, daemon=True)
bot_thread.start()
