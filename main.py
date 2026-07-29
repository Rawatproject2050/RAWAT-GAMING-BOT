import os
import threading
import requests
import logging
import html
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===================== CONFIG =====================
# Render Environment Variables se Token aur Key uthayega
BOT_TOKEN = os.getenv("BOT_TOKEN") 
API_KEY = os.getenv("API_KEY", "FFINFO-Free")
# =================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for Render health check
app = Flask(__name__)

# Helper function to format numbers
def fmt_num(val):
    if val is None or val == "?" or val == "":
        return "?"
    try:
        return f"{int(val):,}"
    except (ValueError, TypeError):
        return str(val)

# Helper function to escape HTML special characters to prevent Telegram Parse Error
def safe_str(text):
    if text is None:
        return "?"
    return html.escape(str(text))

# ===================== FREE FIRE API (SiamBhau Direct) =====================

def get_player_info(uid):
    regions = ["IND", "BD", "SG", "BR", "PK"]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for region in regions:
        try:
            url = f"https://siambhau69.eu.cc/freefireinfo/bhau?uid={uid}&region={region}&key={API_KEY}"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "basicInfo" in data or "nickname" in data or "Name" in data:
                    data["region"] = region
                    return data
        except Exception as e:
            logger.error(f"Error fetching for region {region}: {e}")
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

    create_time = "Unknown"
    if "accountCreateTime" in data or "accountCreateTime" in basic:
        try:
            ts = int(data.get("accountCreateTime") or basic.get("accountCreateTime"))
            create_time = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
        except Exception:
            create_time = str(data.get("accountCreateTime", "Unknown"))

    last_login = "Unknown"
    if "lastLoginTime" in data or "lastLoginTime" in basic:
        try:
            ts = int(data.get("lastLoginTime") or basic.get("lastLoginTime"))
            last_login = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        except Exception:
            last_login = str(data.get("lastLoginTime", "Unknown"))

    nickname       = safe_str(basic.get("nickname") or data.get("nickname") or data.get("Name") or "Unknown")
    level          = safe_str(basic.get("level") or data.get("level") or "?")
    likes          = safe_str(fmt_num(basic.get("liked") or basic.get("likeCount") or data.get("likes") or "?"))
    exp            = safe_str(fmt_num(basic.get("exp") or basic.get("experience") or data.get("exp") or "?"))
    badges         = safe_str(fmt_num(data.get("badgeCount") or data.get("badges") or "?"))
    ob_version     = safe_str(data.get("obVersion") or "OB54")
    rank_br        = safe_str(fmt_num(basic.get("rank") or data.get("rank") or "?"))
    rank_br_high   = safe_str(fmt_num(data.get("highestRank") or basic.get("highestRank") or rank_br))
    br_points      = safe_str(fmt_num(basic.get("rankPoint") or data.get("brPoints") or "?"))
    cs_rank        = safe_str(fmt_num(data.get("csRank") or "?"))
    cs_rank_high   = safe_str(fmt_num(data.get("csHighestRank") or "?"))
    cs_points      = safe_str(fmt_num(data.get("csPoints") or "?"))
    bio            = safe_str(data.get("signature") or social.get("signature") or "No Bio")
    language       = safe_str(social.get("language") or data.get("language") or "Language_EN")
    pref_mode      = safe_str(social.get("preferredMode") or data.get("preferredMode") or "ModePrefer_BR")
    guild_name     = safe_str(clan.get("clanName") or "None")
    guild_id       = safe_str(clan.get("clanId") or "?")
    guild_level    = safe_str(clan.get("clanLevel") or "?")
    guild_members  = safe_str(f"{clan.get('memberNum', '?')}/{clan.get('capacity', '?')}")
    guild_captain  = safe_str(captain.get("nickname") or "Unknown")
    gc_uid         = safe_str(captain.get("accountId") or "?")
    pet_name       = safe_str(pet.get("name") or "None")
    pet_level      = safe_str(pet.get("level") or "?")
    pet_exp        = safe_str(fmt_num(pet.get("exp") or pet.get("experience") or "?"))
    credit_score   = safe_str(fmt_num(credit.get("score") or "?"))
    credit_reward  = safe_str(credit.get("rewardState") or credit.get("reward") or "?")
    diamond_cost   = safe_str(fmt_num(data.get("diamondCost") or "?"))

    return f"""╭━━━━━━━━━━━━━━━━━━━━✪
│  🎮 <b>Fʀᴇᴇ Fɪʀᴇ Pʟᴀʏᴇʀ Iɴꜰᴏ</b>
╰━━━━━━━━━━━━━━━━━━━━✪

╭━⟮ 👤 <b>Bᴀꜱɪᴄ Iɴꜰᴏ</b> ⟯
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

╭━⟮ 🏅 <b>Rᴀɴᴋ Iɴꜰᴏ</b> ⟯
│ 🎯 Bʀ Rᴀɴᴋ: {rank_br}
│ 🏆 Bʀ Hɪɢʜᴇꜱᴛ Rᴀɴᴋ: {rank_br_high}
│ 🎯 Bʀ Pᴏɪɴᴛꜱ: {br_points}
│ ⚔️ Cꜱ Rᴀɴᴋ: {cs_rank}
│ 🏆 Cꜱ Hɪɢʜᴇꜱᴛ Rᴀɴᴋ: {cs_rank_high}
│ ⚔️ Cꜱ Pᴏɪɴᴛꜱ: {cs_points}
╰━━━━━━━━━━━━━━━✪

╭━⟮ 💬 <b>Sᴏᴄɪᴀʟ Iɴꜰᴏ</b> ⟯
│ 📝 Bɪᴏ: {bio}
│ 🌐 Lᴀɴɢᴜᴀɢᴇ: {language}
│ 🎮 Pʀᴇꜰᴇʀʀᴇᴅ Mᴏᴅᴇ: {pref_mode}
╰━━━━━━━━━━━━━━━✪

╭━⟮ 🏰 <b>Gᴜɪʟᴅ Iɴꜰᴏ</b> ⟯
│ 🏯 Nᴀᴍᴇ: {guild_name}
│ 🆔 Gᴜɪʟᴅ Iᴅ: {guild_id}
│ 📶 Lᴇᴠᴇʟ: {guild_level}
│ 👥 Mᴇᴍʙᴇʀꜱ: {guild_members}
│ 👑 Cᴀᴘᴛᴀɪɴ: {guild_captain} ({gc_uid})
╰━━━━━━━━━━━━━━━✪

╭━⟮ 🐾 <b>Pᴇᴛ Iɴꜰᴏ</b> ⟯
│ 🐶 Nᴀᴍᴇ: {pet_name}
│ 📶 Lᴇᴠᴇʟ: {pet_level}
│ ⭐ Exᴘ: {pet_exp}
╰━━━━━━━━━━━━━━━✪

╭━⟮ 🛡️ <b>Cʀᴇᴅɪᴛ Sᴄᴏʀᴇ</b> ⟯
│ 📊 Sᴄᴏʀᴇ: {credit_score}
│ 🎁 Rᴇᴡᴀʀᴅ Sᴛᴀᴛᴇ: {credit_reward}
╰━━━━━━━━━━━━━━━✪"""

# ===================== BOT HANDLERS =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Welcome to Free Fire Info Bot!</b>\n\n"
        "You can send a Free Fire UID directly OR use the command:\n"
        "<code>/info 2722004155</code>\n\n"
        "Example: <code>2722004155</code>",
        parse_mode="HTML"
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ <b>Please provide a UID!</b>\nExample: <code>/info 2722004155</code>", parse_mode="HTML")
        return
    
    uid = context.args[0].strip()
    await process_uid(update, uid)

async def handle_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.text.strip()
    await process_uid(update, uid)

async def process_uid(update: Update, uid: str):
    if not uid.isdigit() or len(uid) < 5 or len(uid) > 15:
        await update.message.reply_text("❌ <b>Invalid UID!</b>", parse_mode="HTML")
        return

    wait_msg = await update.message.reply_text("⏳ <b>Fetching player info...</b>", parse_mode="HTML")
    try:
        data = get_player_info(uid)
        if not data:
            await wait_msg.edit_text("❌ <b>Player not found or API Server Busy!</b>", parse_mode="HTML")
            return
        formatted = format_player_info(data, uid)
        
        # HTML Parse Mode is bulletproof against fancy player names & symbols
        await wait_msg.edit_text(formatted, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error: {e}")
        await wait_msg.edit_text(f"❌ <b>Error:</b> <code>{html.escape(str(e))}</code>", parse_mode="HTML")

# ===================== FLASK HEALTH CHECK =====================

@app.route('/')
def home():
    return '✅ Free Fire Info Bot is running!', 200

# ===================== RUN FLASK IN BACKGROUND =====================

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ===================== MAIN =====================

if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN is missing!")
        exit(1)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
    except Exception:
        pass

    logger.info("✅ Bot is starting in polling mode...")
    app_bot = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("info", info_command))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_uid))
    
    app_bot.run_polling()
