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
BOT_TOKEN = os.getenv("BOT_TOKEN") 
API_KEY = os.getenv("API_KEY", "FFINFO-Free")
# =============================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fmt_num(val):
    if val is None or val == "?" or val == "" or val == "0":
        return "?"
    try:
        return f"{int(val):,}"
    except (ValueError, TypeError):
        return str(val)

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
    
    # Badges extraction
    badges_val     = data.get("badgeCount") or data.get("badges") or basic.get("badgeCount") or data.get("badge")
    badges         = safe_str(fmt_num(badges_val))

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

    return f"""━⟮ 🌟 <b>FREE FIRE PLAYER INFO</b> 🌟 ⟯━

<blockquote>╭━⟮ 👤 <b>Basic Info</b> ⟯
│ 😺 <b>Name:</b> {nickname}
│ 🆔 <b>Uid:</b> {uid}
│ 🌍 <b>Region:</b> {region}
│ 🏆 <b>Level:</b> {level}
│ ⭐ <b>Exp:</b> {exp}
│ ❤️ <b>Likes:</b> {likes}
│ 🎖️ <b>Badges:</b> {badges}
│ 🔖 <b>Ob Version:</b> {ob_version}
│ 📅 <b>Account Created:</b>
│ {create_time}
│ 🕐 <b>Last Login:</b>
│ {last_login}
│ 💎 <b>Diamond Cost:</b> {diamond_cost}
╰━━━━━━━━━━━━━━━✪</blockquote>

<blockquote>╭━⟮ 🏅 <b>Rank Info</b> ⟯
│ 🎯 <b>Br Rank:</b> {rank_br}
│ 🏆 <b>Br Highest Rank:</b> {rank_br_high}
│ 🎯 <b>Br Points:</b> {br_points}
│ ⚔️ <b>Cs Rank:</b> {cs_rank}
│ 🏆 <b>Cs Highest Rank:</b> {cs_rank_high}
│ ⚔️ <b>Cs Points:</b> {cs_points}
╰━━━━━━━━━━━━━━━✪</blockquote>

<blockquote>╭━⟮ 💬 <b>Social Info</b> ⟯
│ 📝 <b>Bio:</b> {bio}
│ 🌐 <b>Language:</b> {language}
│ 🎮 <b>Preferred Mode:</b> {pref_mode}
╰━━━━━━━━━━━━━━━✪</blockquote>

<blockquote>╭━⟮ 🏰 <b>Guild Info</b> ⟯
│ 🏯 <b>Name:</b> {guild_name}
│ 🆔 <b>Guild Id:</b> {guild_id}
│ 📶 <b>Level:</b> {guild_level}
│ 👥 <b>Members:</b> {guild_members}
│ 👑 <b>Captain:</b> {guild_captain} ({gc_uid})
╰━━━━━━━━━━━━━━━✪</blockquote>

<blockquote>╭━⟮ 🐾 <b>Pet Info</b> ⟯
│ 🐶 <b>Name:</b> {pet_name}
│ 📶 <b>Level:</b> {pet_level}
│ ⭐ <b>Exp:</b> {pet_exp}
╰━━━━━━━━━━━━━━━✪</blockquote>

<blockquote>╭━⟮ 🛡️ <b>Credit Score</b> ⟯
│ 📊 <b>Score:</b> {credit_score}
│ 🎁 <b>Reward State:</b> {credit_reward}
╰━━━━━━━━━━━━━━━✪</blockquote>"""

# ===================== BOT HANDLERS & ANALYTICS =====================

# Admin Configuration
ADMIN_ID = 6665529050  # 👈 Yaha apna Numeric Telegram ID daalein (e.g. 583920194)
ADMIN_USERNAME = "@the_rawat_boy_official"

# Memory Storage for Bot Statistics
user_data_store = {}
connected_groups = set()

# Helper function to track active users
def track_user(user, chat_type):
    user_id = user.id
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = f"@{user.username}" if user.username else "No Username"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if user_id not in user_data_store:
        user_data_store[user_id] = {
            "name": full_name,
            "username": username,
            "joined_at": current_time,
            "last_active": current_time,
            "chat_type": chat_type
        }
    else:
        user_data_store[user_id]["last_active"] = current_time
        user_data_store[user_id]["name"] = full_name
        user_data_store[user_id]["username"] = username

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_type = update.effective_chat.type
    track_user(user, chat_type)

    if chat_type in ['group', 'supergroup']:
        connected_groups.add(update.effective_chat.title or str(update.effective_chat.id))

    welcome_text = (
        "<b>❤ ── [ RAWAT FF INFO BOT ] ── ❤</b>\n\n"
        f"<b>👋 Welcome {html.escape(user.first_name)}!</b>\n"
        "<i>Your Ultimate Free Fire Player Analytics Partner.</i>\n\n"
        "<blockquote>⚡ <b>HOW TO USE THE BOT</b>\n\n"
        "1️⃣ <b>Direct Search:</b> Direct kisi ki FF UID bhejo.\n"
        "2️⃣ <b>Command Search:</b> Type karein: <code>/info 2722004155</code>\n"
        "3️⃣ <b>Admin Contact:</b> Owner se baat karne ke liye type karein: <code>/bot_admin</code></blockquote>\n\n"
        "📌 <i>Type box me '/' dabayein sabhi commands dekhne ke liye!</i>"
    )
    await update.message.reply_text(welcome_text, parse_mode="HTML")

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    track_user(user, update.effective_chat.type)

    if not context.args:
        await update.message.reply_text("❌ <b>Please provide a UID!</b>\nExample: <code>/info 2722004155</code>", parse_mode="HTML")
        return
    
    uid = context.args[0].strip()
    await process_uid(update, uid)

async def bot_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    track_user(user, update.effective_chat.type)

    admin_msg = (
        "<b>👑 BOT ADMIN & OWNER INFO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Agar aapko koi help, issue ya bot me modification chahiye to contact karein:\n\n"
        f"👤 <b>Owner:</b> {ADMIN_USERNAME}\n"
        f"💬 <b>Direct DM:</b> https://t.me/the_rawat_boy_official"
    )
    await update.message.reply_text(admin_msg, parse_mode="HTML", disable_web_page_preview=True)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Admin Access Control
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ <b>Yeh command sirf Bot Owner ke liye reserved hai!</b>", parse_mode="HTML")
        return

    total_users = len(user_data_store)
    total_groups = len(connected_groups)

    # Top 5 Recent Users List
    recent_users = list(user_data_store.items())[-5:]
    recent_users.reverse()
    
    recent_text = ""
    for idx, (uid, info) in enumerate(recent_users, 1):
        recent_text += f"{idx}. <b>{html.escape(info['name'])}</b> ({info['username']})\n   └ UID: <code>{uid}</code> | Active: <i>{info['last_active']}</i>\n"

    groups_text = "\n".join([f"• {g}" for g in connected_groups]) if connected_groups else "Kisi group me added nahi hai."

    dashboard = (
        "<b>📊 BOT FULL ANALYTICS DASHBOARD</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Total Users Tracked:</b> {total_users}\n"
        f"🏢 <b>Total Active Groups:</b> {total_groups}\n\n"
        f"📋 <b>Recent Active Users:</b>\n{recent_text or 'Koi user data nahi hai.'}\n"
        f"🏰 <b>Connected Groups:</b>\n{groups_text}"
    )
    await update.message.reply_text(dashboard, parse_mode="HTML")

async def handle_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_type = update.effective_chat.type
    track_user(user, chat_type)

    if chat_type in ['group', 'supergroup']:
        connected_groups.add(update.effective_chat.title or str(update.effective_chat.id))

    uid = update.message.text.strip()
    await process_uid(update, uid)

async def process_uid(update: Update, uid: str):
    # Valid UID Check
    if not uid.isdigit() or len(uid) < 5 or len(uid) > 15:
        await update.message.reply_text(
            "❌ <b>Player not found or API Server Busy!</b>", 
            parse_mode="HTML"
        )
        return

    # Original Simple Message
    wait_msg = await update.message.reply_text(
        "⏳ Fetching player info...", 
        parse_mode="HTML"
    )
    
    # API Request Processing
    data = None
    for attempt in range(3):
        try:
            data = get_player_info(uid)
            if data:
                break
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")

    # Success Case
    if data:
        try:
            formatted = format_player_info(data, uid)
            await wait_msg.edit_text(formatted, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Formatting Error: {e}")
            await wait_msg.edit_text("⚠️ <b>Data Formatting Error!</b> Try again later.", parse_mode="HTML")
    
    # Server Busy Case
    else:
        smart_error_msg = (
            "⚠️ <b>Server Traffic Notice</b>\n\n"
            f"🆔 <b>UID:</b> <code>{uid}</code>\n"
            "🌐 <b>Status:</b> Game Server Busy\n\n"
            "Garena Free Fire server heavy traffic par hai. Aapki UID bilkul sahi hai.\n\n"
            f"🔄 <b>10 seconds baad try karein:</b> <code>/info {uid}</code>"
        )
        await wait_msg.edit_text(smart_error_msg, parse_mode="HTML")
        
# Function to Set Telegram Bot Menu Commands (Popup '/' Menu)
async def post_init(application: Application):
    bot_commands = [
        ("start", "Bot ko restart karein"),
        ("info", "Player ID check karein (/info <UID>)"),
        ("bot_admin", "Contact Bot Owner (@the_rawat_boy_official)")
    ]
    await application.bot.set_my_commands(bot_commands)

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN environment variable is missing on Render!")
        exit(1)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
    except Exception:
        pass

    logger.info("✅ Bot is starting in polling mode...")
    
    # Build Bot with post_init to register '/' menu
    app_bot = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Register Handlers
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("info", info_command))
    app_bot.add_handler(CommandHandler("bot_admin", bot_admin_command))
    app_bot.add_handler(CommandHandler("stats", stats_command))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_uid))
    
    app_bot.run_polling()
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
