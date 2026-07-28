import os
import threading
import requests
import logging
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===================== CONFIG =====================
# Render Environment Variables se Token uthayega
BOT_TOKEN = os.getenv("BOT_TOKEN") 
API_BASE = "https://free-ff-api-src-5plp.onrender.com/api/v1"
# =================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for Render health check
app = Flask(__name__)

# Helper function to format numbers with commas (e.g., 14314 -> 14,314)
def fmt_num(val):
    if val is None or val == "?" or val == "":
        return "?"
    try:
        return f"{int(val):,}"
    except (ValueError, TypeError):
        return str(val)

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
        except Exception:
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
    if "accountCreateTime" in data:
        try:
            ts = int(data["accountCreateTime"])
            create_time = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
        except Exception:
            create_time = str(data.get("accountCreateTime", "Unknown"))

    last_login = "Unknown"
    if "lastLoginTime" in data:
        try:
            ts = int(data["lastLoginTime"])
            last_login = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        except Exception:
            last_login = str(data.get("lastLoginTime", "Unknown"))

    nickname       = basic.get("nickname", "Unknown")
    level          = basic.get("level", "?")
    likes          = fmt_num(basic.get("liked", basic.get("likeCount", "?")))
    exp            = fmt_num(basic.get("exp", basic.get("experience", "?")))
    badges         = fmt_num(data.get("badgeCount", data.get("badges", "?")))
    ob_version     = data.get("obVersion", "OB54")
    rank_br        = fmt_num(basic.get("rank", "?"))
    rank_br_high   = fmt_num(data.get("highestRank", basic.get("highestRank", rank_br)))
    br_points      = fmt_num(basic.get("rankPoint", data.get("brPoints", "?")))
    cs_rank        = fmt_num(data.get("csRank", "?"))
    cs_rank_high   = fmt_num(data.get("csHighestRank", "?"))
    cs_points      = fmt_num(data.get("csPoints", "?"))
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
    pet_exp        = fmt_num(pet.get("exp", pet.get("experience", "?")))
    credit_score   = fmt_num(credit.get("score", "?"))
    credit_reward  = credit.get("rewardState", credit.get("reward", "?"))
    diamond_cost   = fmt_num(data.get("diamondCost", "?"))

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
        "You can send a Free Fire UID directly OR use the command:\n"
        "`/info 2722004155`\n\n"
        "Example: `2722004155`",
        parse_mode="Markdown"
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ *Please provide a UID!*\nExample: `/info 2722004155`", parse_mode="Markdown")
        return
    
    uid = context.args[0].strip()
    await process_uid(update, uid)

async def handle_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.text.strip()
    await process_uid(update, uid)

async def process_uid(update: Update, uid: str):
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
