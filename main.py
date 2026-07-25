import os
import json
import logging
import re
import time
import asyncio
import threading
from datetime import datetime
from typing import Optional

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ============================================================
# CONFIG - ENVIRONMENT VARIABLES USE KARO!
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS_STR = os.environ.get("ADMIN_IDS", "123456789")  # comma separated
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_STR.split(",") if x.strip().isdigit()]
PORT = int(os.environ.get("PORT", 8080))

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ============================================================
# DATABASE - Render pe SQLite file-based chalta hai (lekin
#            har deploy pe data loss hoga. Production ke liye
#            PostgreSQL use karo.)
# ============================================================
DB_PATH = "ff_bot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Tournaments
    c.execute("""
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            max_teams INTEGER DEFAULT 16,
            status TEXT DEFAULT 'open'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tournament_teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER,
            team_name TEXT,
            player1_name TEXT,
            player1_uid TEXT,
            player2_name TEXT,
            player2_uid TEXT,
            player3_name TEXT,
            player3_uid TEXT,
            player4_name TEXT,
            player4_uid TEXT,
            registered_by INTEGER,
            registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tournament_id) REFERENCES tournaments(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tournament_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER,
            round INTEGER,
            match_index INTEGER,
            team1_id INTEGER,
            team2_id INTEGER,
            winner_id INTEGER,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY(tournament_id) REFERENCES tournaments(id)
        )
    """)
    # News
    c.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            category TEXT DEFAULT 'news',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

import sqlite3  # ye import upar bhi ho sakta hai
init_db()

# ============================================================
# DATABASE HELPERS
# ============================================================
def db_execute(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    last_id = c.lastrowid
    conn.close()
    return last_id

def db_fetch_all(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def db_fetch_one(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(query, params)
    row = c.fetchone()
    conn.close()
    return row

# ============================================================
# FREE FIRE API HELPERS
# ============================================================
FF_API_INFO = "https://freefireapi.me/info"
FF_API_BAN = "https://freefireapi.me/api/ban"
FF_API_STATS = "https://freefireinfo-zy9l.onrender.com/api/v1/player-stats"
FF_API_ACCOUNT = "https://free-ff-api-src-5plp.onrender.com/api/v1/account"
FF_API_ACCOUNT2 = "https://info-ob49.vercel.app/api/account/"

def fetch_player_info(uid):
    apis = [
        f"{FF_API_INFO}?uid={uid}",
        f"{FF_API_ACCOUNT}?region=IND&uid={uid}",
        f"{FF_API_ACCOUNT2}?uid={uid}&region=ind",
    ]
    for url in apis:
        try:
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if data and data.get("basicInfo"):
                    return data
        except:
            continue
    return None

def fetch_player_stats(uid, server="IND"):
    try:
        resp = requests.get(
            f"{FF_API_STATS}?uid={uid}&server={server}&gamemode=br&matchmode=CAREER",
            timeout=8,
        )
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return None

def fetch_ban_status(uid):
    try:
        resp = requests.get(f"{FF_API_BAN}?uid={uid}", timeout=8)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return None

# ============================================================
# PRICE CALCULATOR
# ============================================================
def calculate_account_price(level, diamonds=0, rare_skins=0, legendary_skins=0,
                            elite_pass=False, emotes=0, pets=0, guild_level=0, badges=0):
    base = 0
    if level >= 70: base += 500
    elif level >= 60: base += 300
    elif level >= 50: base += 200
    elif level >= 40: base += 100
    elif level >= 30: base += 50
    else: base += 20
    base += diamonds * 0.5
    base += rare_skins * 50
    base += legendary_skins * 200
    if elite_pass: base += 150
    base += emotes * 30
    base += pets * 100
    base += guild_level * 20
    base += badges * 10
    return {
        "estimated_price_inr": round(base, 2),
        "estimated_price_usd": round(base / 83, 2),
    }

# ============================================================
# TOURNAMENT BRACKETS
# ============================================================
def generate_brackets(tournament_id):
    teams = db_fetch_all(
        "SELECT id, team_name FROM tournament_teams WHERE tournament_id = ?",
        (tournament_id,),
    )
    if len(teams) < 2:
        return False
    import math
    n = len(teams)
    next_pow2 = 2 ** math.ceil(math.log2(n))
    team_ids = [t[0] for t in teams]
    while len(team_ids) < next_pow2:
        team_ids.append(None)
    for i in range(0, len(team_ids), 2):
        t1 = team_ids[i]
        t2 = team_ids[i + 1]
        db_execute(
            "INSERT INTO tournament_matches (tournament_id, round, match_index, team1_id, team2_id) VALUES (?, 1, ?, ?, ?)",
            (tournament_id, i // 2, t1, t2),
        )
    return True

# ============================================================
# KEYBOARDS
# ============================================================
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Stats Checker", callback_data="tool_stats"),
         InlineKeyboardButton("✅ ID Validator", callback_data="tool_validator")],
        [InlineKeyboardButton("🏆 Tournament", callback_data="tool_tournament"),
         InlineKeyboardButton("💰 Price Calculator", callback_data="tool_price")],
        [InlineKeyboardButton("📰 News & Guides", callback_data="tool_news"),
         InlineKeyboardButton("ℹ️ About", callback_data="tool_about")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]])

# ============================================================
# COMMAND HANDLERS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🎮 **Welcome to FF Ultimate Bot, {user.first_name}!**\n\n"
        f"5 powerful Free Fire tools:\n"
        f"📊 Stats Checker | ✅ ID Validator | 🏆 Tournament\n"
        f"💰 Price Calculator | 📰 News & Guides\n\n"
        f"👇 **Choose a tool below:**",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎮 **FF Ultimate Bot Menu**", reply_markup=main_menu_keyboard(), parse_mode="Markdown")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting"] = None
    await update.message.reply_text("❌ Cancelled. Use /menu", reply_markup=main_menu_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 **FF Ultimate Bot - Help**\n\n"
        "/start - Start bot\n/menu - Main menu\n/admin - Admin panel\n/cancel - Cancel\n/help - This help\n\n"
        "📊 Stats: Send UID\n✅ Validator: Send UID\n🏆 Tournament: Register team\n💰 Price: Send details\n📰 News: Browse",
        reply_markup=main_menu_keyboard(), parse_mode="Markdown"
    )

# ============================================================
# CALLBACK HANDLER
# ============================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await query.edit_message_text("🎮 **FF Ultimate Bot Menu**", reply_markup=main_menu_keyboard(), parse_mode="Markdown")
        return

    elif data == "tool_stats":
        context.user_data["awaiting"] = "stats_uid"
        await query.edit_message_text(
            "📊 **FF Stats Checker**\n\nSend a Free Fire UID (10-12 digits):\n\nExample: `11959685790`\n\nType /cancel to go back.",
            reply_markup=back_button(), parse_mode="Markdown"
        )

    elif data == "tool_validator":
        context.user_data["awaiting"] = "validator_uid"
        await query.edit_message_text(
            "✅ **FF ID Validator**\n\nSend a Free Fire UID:\n\nExample: `11959685790`",
            reply_markup=back_button(), parse_mode="Markdown"
        )

    elif data == "tool_tournament":
        keyboard = [
            [InlineKeyboardButton("📋 Register Team", callback_data="tourn_register"),
             InlineKeyboardButton("👥 My Team", callback_data="tourn_myteam")],
            [InlineKeyboardButton("🏆 Brackets", callback_data="tourn_brackets"),
             InlineKeyboardButton("📊 Status", callback_data="tourn_status")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
        ]
        await query.edit_message_text("🏆 **FF Tournament Organizer**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "tourn_register":
        context.user_data["awaiting"] = "tourn_team_name"
        await query.edit_message_text(
            "🏆 **Register Team**\n\nFormat:\n"
            "`Team Name`\n`P1 Name | P1 UID`\n`P2 Name | P2 UID`\n`P3 Name | P3 UID`\n`P4 Name | P4 UID`\n\n"
            "Example:\n`BOOYAH Squad`\n`Rahul | 1234567890`\n`Amit | 1234567891`\n`Sneha | 1234567892`\n`Priya | 1234567893`",
            reply_markup=back_button(), parse_mode="Markdown"
        )

    elif data == "tourn_myteam":
        user_id = query.from_user.id
        team = db_fetch_one("SELECT * FROM tournament_teams WHERE registered_by = ? ORDER BY id DESC LIMIT 1", (user_id,))
        if team:
            text = f"👥 **Your Team**\n\n🏷️ {team[2]}\n👤 P1: {team[3]} (`{team[4]}`)\n👤 P2: {team[5]} (`{team[6]}`)\n👤 P3: {team[7]} (`{team[8]}`)\n👤 P4: {team[9]} (`{team[10]}`)"
        else:
            text = "❌ No team registered yet."
        await query.edit_message_text(text, reply_markup=back_button(), parse_mode="Markdown")

    elif data == "tourn_brackets":
        tournament = db_fetch_one("SELECT id, name FROM tournaments WHERE status = 'open' OR status = 'active' ORDER BY id DESC LIMIT 1")
        if not tournament:
            await query.edit_message_text("❌ No active tournament.", reply_markup=back_button())
            return
        matches = db_fetch_all(
            "SELECT tm.round, tm.match_index, t1.team_name, t2.team_name, tm.winner_id, tm.status "
            "FROM tournament_matches tm LEFT JOIN tournament_teams t1 ON tm.team1_id = t1.id "
            "LEFT JOIN tournament_teams t2 ON tm.team2_id = t2.id WHERE tm.tournament_id = ? ORDER BY tm.round, tm.match_index",
            (tournament[0],),
        )
        if not matches:
            await query.edit_message_text("❌ Brackets not generated yet.", reply_markup=back_button())
            return
        text = f"🏆 **{tournament[1]} — Brackets**\n\n"
        current_round = 0
        for m in matches:
            if m[0] != current_round:
                current_round = m[0]
                text += f"**── Round {current_round} ──**\n"
            t1 = m[2] or "BYE"
            t2 = m[3] or "BYE"
            if m[5] == "completed" and m[4]:
                text += f"✅ {t1} vs {t2} → **Winner**\n"
            elif m[5] == "in_progress":
                text += f"⚔️ {t1} vs {t2} *(Ongoing)*\n"
            else:
                text += f"⏳ {t1} vs {t2}\n"
        await query.edit_message_text(text, reply_markup=back_button(), parse_mode="Markdown")

    elif data == "tourn_status":
        tournament = db_fetch_one("SELECT id, name, max_teams, status FROM tournaments ORDER BY id DESC LIMIT 1")
        if not tournament:
            await query.edit_message_text("❌ No tournaments.", reply_markup=back_button())
            return
        teams_count = db_fetch_one("SELECT COUNT(*) FROM tournament_teams WHERE tournament_id = ?", (tournament[0],))[0]
        s = "🟢 OPEN" if tournament[3] == "open" else "🔴 CLOSED" if tournament[3] == "closed" else "🟡 ACTIVE"
        await query.edit_message_text(f"🏆 **Tournament Status**\n\n📛 {tournament[1]}\n{s}\n👥 {teams_count}/{tournament[2]} teams", reply_markup=back_button(), parse_mode="Markdown")

    elif data == "tool_price":
        context.user_data["awaiting"] = "price_details"
        await query.edit_message_text(
            "💰 **Price Calculator**\n\nSend: `Level | Diamonds | Rare Skins | Legendary | Elite(y/n) | Emotes | Pets | Guild | Badges`\n\n"
            "Example: `65 | 5000 | 12 | 5 | y | 8 | 3 | 7 | 25`",
            reply_markup=back_button(), parse_mode="Markdown"
        )

    elif data == "tool_news":
        news_list = db_fetch_all("SELECT id, title, category, created_at FROM news ORDER BY id DESC LIMIT 10")
        if not news_list:
            text = "📰 **No news yet!**"
        else:
            text = "📰 **Latest FF News & Guides**\n\n"
            for n in news_list:
                emoji = {"news": "📢", "guide": "📖", "code": "🔑"}.get(n[2], "📌")
                text += f"{emoji} {n[1]} — {n[3]}\n"
        await query.edit_message_text(text, reply_markup=back_button(), parse_mode="Markdown")

    elif data == "tool_about":
        await query.edit_message_text(
            "ℹ️ **FF Ultimate Bot v2.0**\n\n"
            "Bot: @ff_likes_123_bot\n\n"
            "✅ Stats Checker\n✅ ID Validator\n✅ Tournament Organizer\n✅ Price Calculator\n✅ News & Guides",
            reply_markup=back_button(), parse_mode="Markdown"
        )

    else:
        await query.edit_message_text("❓ Unknown option. Use /menu", reply_markup=main_menu_keyboard())

# ============================================================
# MESSAGE HANDLER
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    awaiting = context.user_data.get("awaiting")

    if not awaiting:
        await update.message.reply_text("Use /menu to see options.", reply_markup=main_menu_keyboard())
        return

    # STATS
    if awaiting == "stats_uid":
        if not re.match(r"^\d{10,12}$", text):
            await update.message.reply_text("❌ Invalid UID (10-12 digits)", reply_markup=back_button())
            return
        msg = await update.message.reply_text("🔍 Fetching stats...")
        info = fetch_player_info(text)
        stats = fetch_player_stats(text)
        ban = fetch_ban_status(text)
        if not info:
            await msg.edit_text(f"❌ Player not found for UID: `{text}`", reply_markup=back_button(), parse_mode="Markdown")
            context.user_data["awaiting"] = None
            return
        bi = info.get("basicInfo", {})
        clan = info.get("clanBasicInfo", {})
        ban_text = "🚫 BANNED" if ban and (ban.get("banned") or ban.get("isBanned")) else "✅ Not Banned"
        kd = "N/A"
        if stats:
            kd = stats.get("kd", stats.get("KDR", stats.get("kdr", "N/A")))
        result = (
            f"📊 **Player Stats**\n\n"
            f"👤 {bi.get('nickname','?')} | 🆔 `{text}`\n"
            f"🏅 Level {bi.get('level','?')} | ⭐ Rank {bi.get('rank','?')}\n"
            f"🌍 {bi.get('region','?')} | 🏰 {clan.get('clanName','No Clan')}\n"
            f"❤️ {bi.get('liked',0)} Likes\n"
            f"🎯 K/D: {kd}\n"
            f"🛡️ {ban_text}"
        )
        await msg.edit_text(result, reply_markup=back_button(), parse_mode="Markdown")
        context.user_data["awaiting"] = None

    # VALIDATOR
    elif awaiting == "validator_uid":
        if not re.match(r"^\d{10,12}$", text):
            await update.message.reply_text("❌ Invalid format", reply_markup=back_button())
            return
        msg = await update.message.reply_text("🔍 Validating...")
        info = fetch_player_info(text)
        if info and info.get("basicInfo"):
            bi = info["basicInfo"]
            ban = fetch_ban_status(text)
            ban_text = "🚫 BANNED" if ban and (ban.get("banned") or ban.get("isBanned")) else "✅ Not Banned"
            result = f"✅ **VALID UID** ✅\n\n👤 {bi.get('nickname','?')}\n🆔 `{text}`\n🏅 Level {bi.get('level','?')}\n🌍 {bi.get('region','?')}\n🛡️ {ban_text}"
        else:
            result = f"❌ **INVALID UID** ❌\n\nUID `{text}` not found."
        await msg.edit_text(result, reply_markup=back_button(), parse_mode="Markdown")
        context.user_data["awaiting"] = None

    # TOURNAMENT REGISTRATION
    elif awaiting == "tourn_team_name":
        lines = text.strip().split("\n")
        if len(lines) < 5:
            await update.message.reply_text("❌ Need 5 lines: Team name + 4 players", reply_markup=back_button())
            return
        team_name = lines[0].strip()
        players = []
        for i in range(1, 5):
            parts = lines[i].split("|")
            if len(parts) < 2:
                await update.message.reply_text(f"❌ Line {i+1}: use `Name | UID`", reply_markup=back_button())
                return
            p_name, p_uid = parts[0].strip(), parts[1].strip()
            if not re.match(r"^\d{10,12}$", p_uid):
                await update.message.reply_text(f"❌ Invalid UID: {p_uid}", reply_markup=back_button())
                return
            players.append((p_name, p_uid))
        tournament = db_fetch_one("SELECT id FROM tournaments WHERE status = 'open' ORDER BY id DESC LIMIT 1")
        if not tournament:
            tid = db_execute("INSERT INTO tournaments (name, max_teams, status) VALUES (?, ?, ?)", ("FF Tournament", 16, "open"))
            tournament_id = tid
        else:
            tournament_id = tournament[0]
        existing = db_fetch_one("SELECT id FROM tournament_teams WHERE registered_by = ? AND tournament_id = ?", (user_id, tournament_id))
        if existing:
            await update.message.reply_text("❌ Already registered!", reply_markup=back_button())
            context.user_data["awaiting"] = None
            return
        count = db_fetch_one("SELECT COUNT(*) FROM tournament_teams WHERE tournament_id = ?", (tournament_id,))[0]
        max_teams = db_fetch_one("SELECT max_teams FROM tournaments WHERE id = ?", (tournament_id,))[0]
        if count >= max_teams:
            await update.message.reply_text(f"❌ Tournament full ({max_teams} teams)!", reply_markup=back_button())
            context.user_data["awaiting"] = None
            return
        db_execute(
            "INSERT INTO tournament_teams (tournament_id, team_name, player1_name, player1_uid, player2_name, player2_uid, player3_name, player3_uid, player4_name, player4_uid, registered_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (tournament_id, team_name, players[0][0], players[0][1], players[1][0], players[1][1], players[2][0], players[2][1], players[3][0], players[3][1], user_id),
        )
        await update.message.reply_text(f"✅ **{team_name} Registered!**", reply_markup=main_menu_keyboard(), parse_mode="Markdown")
        context.user_data["awaiting"] = None

    # PRICE CALCULATOR
    elif awaiting == "price_details":
        parts = text.replace(",", "").split("|")
        if len(parts) < 5:
            await update.message.reply_text("❌ Format: Level | Diamonds | Rare | Legendary | Elite(y/n) | ...", reply_markup=back_button())
            return
        try:
            level = int(parts[0].strip())
            diamonds = int(parts[1].strip()) if parts[1].strip() else 0
            rare = int(parts[2].strip()) if parts[2].strip() else 0
            legendary = int(parts[3].strip()) if parts[3].strip() else 0
            elite = parts[4].strip().lower() in ("y", "yes", "1")
            emotes = int(parts[5].strip()) if len(parts) > 5 and parts[5].strip() else 0
            pets = int(parts[6].strip()) if len(parts) > 6 and parts[6].strip() else 0
            guild = int(parts[7].strip()) if len(parts) > 7 and parts[7].strip() else 0
            badges = int(parts[8].strip()) if len(parts) > 8 and parts[8].strip() else 0
        except:
            await update.message.reply_text("❌ Invalid numbers", reply_markup=back_button())
            return
        price = calculate_account_price(level, diamonds, rare, legendary, elite, emotes, pets, guild, badges)
        await update.message.reply_text(
            f"💰 **Account Estimate**\n\n"
            f"🏅 Level {level} | 💎 {diamonds:,}\n🔵 Rare {rare} | 🟡 Legendary {legendary}\n"
            f"━━━━━━━━\n"
            f"🇮🇳 ₹{price['estimated_price_inr']:,.2f}\n"
            f"🇺🇸 ${price['estimated_price_usd']:,.2f}",
            reply_markup=back_button(), parse_mode="Markdown"
        )
        context.user_data["awaiting"] = None

    else:
        await update.message.reply_text("❓ Type /menu", reply_markup=main_menu_keyboard())

# ============================================================
# ADMIN
# ============================================================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized")
        return
    keyboard = [
        [InlineKeyboardButton("📝 Add News", callback_data="admin_add_news")],
        [InlineKeyboardButton("🏆 Start Tournament", callback_data="admin_start_tourn")],
        [InlineKeyboardButton("⚔️ Generate Brackets", callback_data="admin_gen_brackets")],
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ]
    await update.message.reply_text("⚙️ **Admin Panel**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("❌ Unauthorized!")
        return
    await query.answer()
    data = query.data

    if data == "admin_add_news":
        context.user_data["awaiting"] = "admin_news_title"
        await query.edit_message_text("📝 Send the **title**:", reply_markup=back_button(), parse_mode="Markdown")

    elif data == "admin_start_tourn":
        db_execute("UPDATE tournaments SET status = 'closed' WHERE status = 'open'")
        tid = db_execute("INSERT INTO tournaments (name, max_teams, status) VALUES (?, ?, ?)", (f"FF #{int(time.time())}", 16, "open"))
        await query.edit_message_text(f"✅ Tournament #{tid} created!", reply_markup=back_button())

    elif data == "admin_gen_brackets":
        tournament = db_fetch_one("SELECT id, name FROM tournaments WHERE status = 'open' ORDER BY id DESC LIMIT 1")
        if not tournament:
            await query.edit_message_text("❌ No open tournament.", reply_markup=back_button())
            return
        db_execute("UPDATE tournaments SET status = 'active' WHERE id = ?", (tournament[0],))
        if generate_brackets(tournament[0]):
            await query.edit_message_text(f"✅ Brackets generated for {tournament[1]}!", reply_markup=back_button())
        else:
            await query.edit_message_text("❌ Need at least 2 teams.", reply_markup=back_button())

    elif data == "admin_stats":
        users = db_fetch_one("SELECT COUNT(DISTINCT registered_by) FROM tournament_teams")[0] or 0
        teams = db_fetch_one("SELECT COUNT(*) FROM tournament_teams")[0] or 0
        tours = db_fetch_one("SELECT COUNT(*) FROM tournaments")[0] or 0
        news = db_fetch_one("SELECT COUNT(*) FROM news")[0] or 0
        await query.edit_message_text(f"📊 **Bot Stats**\n\n👥 Players: {users}\n👥 Teams: {teams}\n🏆 Tournaments: {tours}\n📰 News: {news}", reply_markup=back_button(), parse_mode="Markdown")

# ============================================================
# WEB SERVER (Render health check ke liye)
# ============================================================
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"FF Bot is running!")

    def log_message(self, format, *args):
        pass  # Don't log health check pings

def run_http_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    logger.info(f"Health check server running on port {PORT}")
    server.serve_forever()

# ============================================================
# RUN BOT
# ============================================================
def run_bot():
    """Run the Telegram bot with polling."""
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Bot started polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    import threading
    
    # Health check server thread (Render ko port chahiye)
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Bot main thread
    run_bot()
