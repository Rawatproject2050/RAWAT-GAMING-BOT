import os
import threading
import requests
import logging
import html
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===================== RENDER ENV CONFIG =====================
# Render Environment Variables:
# 1. BOT_TOKEN = (Aapka Telegram Bot Token)
# 2. API_KEY   = FFINFO-Free
BOT_TOKEN = os.getenv("BOT_TOKEN") 
API_KEY = os.getenv("API_KEY", "FFINFO-Free")
# =============================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for Render health check
app = Flask(__name__)

# Helper function to format numbers with commas
def fmt_num(val):
    if val is None or val == "?" or val == "" or str(val) == "0":
        return "?"
    try:
        return f"{int(val):,}"
    except (ValueError, TypeError):
        return str(val)

# Helper function to escape HTML special characters to prevent Telegram Parse Error
def safe_str(text):
    if text is None or text == "":
        return "?"
    return html.escape(str(text))

# Format timestamp to readable date/time
def parse_time(ts, fmt="%Y-%m-%d"):
    if not ts or str(ts) in ["0", "?", "None"]:
        return "Unknown"
    try:
        ts_int = int(ts)
        # If timestamp is in milliseconds, convert to seconds
        if ts_int > 10000000000:
            ts_int = ts_int // 1000
        return datetime.fromtimestamp(ts_int).strftime(fmt)
    except Exception:
        return str(ts)

# ===================== FREE FIRE API =====================

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
    basic = data.get("basicInfo") or data.get("basic") or {}
    social = data.get("socialInfo") or data.get("social") or {}
    clan = data.get("clanBasicInfo") or data.get("clan") or {}
    captain = data.get("captainBasicInfo") or data.get("captain") or {}
    pet = data.get("petInfo") or data.get("pet") or {}
    credit = data.get("creditScore") or data.get("credit") or {}
    region = data.get("region", basic.get("region", "IND"))

    # Extracting Create Time & Last Login from multiple possible API JSON paths
    create_ts = (
        data.get("accountCreateTime") or basic.get("accountCreateTime") or
        data.get("createTime") or basic.get("createTime") or
        data.get("openAcountTime") or basic.get("openAcountTime")
    )
    create_time = parse_time(create_ts, "%Y-%m-%d")

    last_login_ts = (
        data.get("lastLoginTime") or basic.get("lastLoginTime") or
        data.get("lastLogin") or basic.get("lastLogin")
    )
    last_login = parse_time(last_login_ts, "%Y-%m-%d %H:%M")

    nickname       = safe_str(basic.get("nickname") or data.get("nickname") or data.get("Name") or "Unknown")
    level          = safe_str(basic.get("level") or data.get("level") or "?")
    likes          = safe_str(fmt_num(basic.get("liked") or basic.get("likeCount") or data.get("likes") or "?"))
    exp            = safe_str(fmt_num(basic.get("exp") or basic.get("experience") or data.get("exp") or "?"))
    badges         = safe_str(fmt_num(data.get("badgeCount") or data.get("badges") or basic.get("badgeCount") or data.get("badge")))
    ob_version     = safe_str(data.get("obVersion") or basic.get("obVersion") or "OB54")
    
    rank_br        = safe_str(fmt_num(basic.get("rank") or data.get("rank") or "?"))
    rank_br_high   = safe_str(fmt_num(data.get("highestRank") or basic.get("highestRank") or rank_br))
    br_points      = safe_str(fmt_num(basic.get("rankPoint") or data.get("brPoints") or "?"))
    
    cs_rank        = safe_str(fmt_num(data.get("csRank") or basic.get("csRank") or "?"))
    cs_rank_high   = safe_str(fmt_num(data.get("csHighestRank") or basic.get("csHighestRank") or "?"))
    cs_points      = safe_str(fmt_num(data.get("csPoints") or basic.get("csPoints") or "?"))
    
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

    # Sky Blue Accent Theme Layout
    return f"""<b>🩵 ─── [ FREE FIRE PLAYER INFO ] ─── 🩵</b>

<blockquote expandable>💧 <b>BASIC INFO</b>
🔹 <b>Name:</b> {nickname}
🔹 <b>Uid:</b> {uid}
🌐 <b>Region:</b> {region}
🏆 <b>Level:</b> {level}
⭐ <b>Exp:</b> {exp}
🩵 <b>Likes:</b> {likes}
🎖️ <b>Badges:</b> {badges}
🔖 <b>Ob Version:</b> {ob_version}
📅 <b>Account Created:</b> {create_time}
🕐 <b>Last Login:</b> {last_login}
💎 <b>Diamond Cost:</b> {diamond_cost}</blockquote>

<blockquote expandable>💧 <b>RANK INFO</b>
🎯 <b>Br Rank:</b> {rank_br}
🏆 <b>Br Highest Rank:</b> {rank_br_high}
📊 <b>Br Points:</b> {br_points}
⚔️ <b>Cs Rank:</b> {cs_rank}
🏆 <b>Cs Highest Rank:</b> {cs_rank_high}
📊 <b>Cs Points:</b> {cs_points}</blockquote>

<blockquote expandable>💧 <b>SOCIAL INFO</b>
💬 <b>Bio:</b> {bio}
🌐 <b>Language:</b> {language}
🎮 <b>Preferred Mode:</b> {pref_mode}</blockquote>

<blockquote expandable>💧 <b>GUILD INFO</b>
🏰 <b>Name:</b> {guild_name}
🆔 <b>Guild Id:</b> {guild_id}
📶 <b>Level:</b> {guild_level}
👥 <b>Members:</b> {guild_members}
👑 <b>Captain:</b> {guild_captain} ({gc_uid})</blockquote>

<blockquote expandable>💧 <b>PET INFO</b>
🐾 <b>Name:</b> {pet_name}
📶 <b>Level:</b> {pet_level}
⭐ <b>Exp:</b> {pet_exp}</blockquote>

<blockquote expandable>💧 <b>CREDIT SCORE</b>
🛡️ <b>Score:</b> {credit_score}
🎁 <b>Reward State:</b> {credit_reward}</blockquote>"""

# ===================== BOT HANDLERS =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Welcome to Free Fire Info Bot!</b>\n\n"
        "Send a Free Fire UID directly OR use:\n"
        "<code>/info 2722004155</code>",
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
        await wait_msg.edit_text(formatted, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error: {e}")
        await wait_msg.edit_text(f"❌ <b>Error:</b> <code>{html.escape(str(e))}</code>", parse_mode="HTML")

# ===================== FLASK HEALTH CHECK =====================

@app.route('/')
def home():
    return '✅ Free Fire Info Bot is running!', 200

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ===================== MAIN =====================

if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN environment variable is missing on Render!")
        exit(1)

    logger.info(f"🔑 Using API_KEY: {API_KEY}")

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
    except Exception:
        pass

    logger.info("✅ Bot is starting in polling mode...")
    app_bot = Application.builder().token(BOT_TOKEN).build()
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("info", info_command))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_uid))
    
    app_bot.run_polling()
