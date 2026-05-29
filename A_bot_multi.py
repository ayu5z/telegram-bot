import asyncio
import json
import os
import random
import time
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# ---------------------------
# CONFIG (Saare 7 Active Tokens Ke Sath)
# ---------------------------

TOKENS = [
    "8990009473:AAEQ8uTYFcLdlNT4G6P67dHow5_8Dr4qNns",
    "8753779246:AAE6mtxGsnDi5z9mW0UPNlnU2qn5PQ5tE6I",
    "7974090478:AAFaA_Y2FpqNuwZp48gs_bHOL7tmNRN2gPk",
    "8926186022:AAEJaiAMVaqctKywB8NPiIuhJhSKZTycU9U",
    "8492645820:AAEaH44rdyqYtY3MrYwanfO0Tgdjygn_K1I",
    "8809881215:AAGb8gBWX3h2ppdbsqjfg8L2q_8tEYfxSXI",
    "8572725427:AAFc-a5DKoi5w5Phv3kTxHdU-B1eyr5W3oM"
]

OWNER_ID = 7719675561
SUDO_FILE = "sudo.json"

# AAPKA RENDER APP URL
MY_RENDER_URL = "https://telegram-bot-fsx5.onrender.com"

# ---------------------------
# FLASK APP FOR WEBHOOK & RENDER PORT BINDING
# ---------------------------
app_flask = Flask('')

# ---------------------------
# ALL SPAM & RAID TEXTS
# ---------------------------
RAID_TEXTS = [
    "Try ben ci bhosadi beta 😹😹🔥🔥",
    "Try ma randy 🤣🤣❤️‍🔥❤️‍🔥",
    "Teri mom ko i love u ree 💋💋🤣🤣",
    "Tmkc pe chppl hi chppl marunga !! 🤤🤤🤤🤤",
    "Teri maa randy ⚡⚡⚡⚡",
    "Chl Harmazaadi Ke ladke 💦💦💦💦",
    "hlw hlw mja aarha cudne me? 🫦🗣️🗣️🗣️",
    "bina ruke thukai hogi teri 😈😈😈😈",
    "kr na fyt 😹😹🔥🔥",
    "hlw reply fas 🤣🤣❤️‍🔥❤️‍🔥",
    "sort nhi krunga cud tu bina ruke 💋💋🤣🤣",
    "kaale Doraemon rota reh 🤤🤤🤤🤤",
    "teri bkc me bigboss ⚡⚡⚡⚡",
    "Awaz neeche rndy k bacche 💦💦💦💦",
    "Sawal mt puch tery ma k bosda baap mhu 🫦🗣️🗣️🗣️"
]

NCEMO_EMOJIS = [
    "😭😭😭😭", "🗿🗿🗿🗿", "🎀🎀🎀🎀", "❤️❤️❤️❤️", "🔥🔥🔥🔥",
    "💘💘💘💘", "🤎🤎🤎🤎", "💌💌💌💌", "🤍🤍🤍🤍", "🖤🖤🖤🖤",
    "💜💜💜💜", "💙💙💙💙", "💛💛💛💛", "🧡🧡🧡🧡", "🌷🌷🌷🌷",
    "😈😈😈😈", "🌺🌺🌺🌺"
]

# ---------------------------
# GLOBAL STATE
# ---------------------------
if os.path.exists(SUDO_FILE):
    try:
        with open(SUDO_FILE, "r") as f:
            _loaded = json.load(f)
            SUDO_USERS = set(int(x) for x in _loaded)
    except Exception:
        SUDO_USERS = {OWNER_ID}
else:
    SUDO_USERS = {OWNER_ID}
    with open(SUDO_FILE, "w") as f: 
        json.dump(list(SUDO_USERS), f)

def save_sudo():
    with open(SUDO_FILE, "w") as f: 
        json.dump(list(SUDO_USERS), f)

group_tasks = {}
heavy_spam_tasks = {} 
custom_spam_tasks = {} 
slide_targets = set()
slidespam_targets = set()
swipe_mode = {}
apps, bots = [], []
delay = 1

apps_dict = {}

logging.basicConfig(level=logging.INFO)

# ---------------------------
# DECORATORS
# ---------------------------
def only_sudo(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if uid not in SUDO_USERS:
            return await update.message.reply_text("❌ You are not SUDO.")
        return await func(update, context)
    return wrapper

def only_owner(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if uid != OWNER_ID:
            return await update.message.reply_text("❌ Only Owner can do this.")
        return await func(update, context)
    return wrapper

# ---------------------------
# LOOP FUNCTIONS
# ---------------------------
async def bot_loop(bot_obj, chat_id, base, mode):
    i = 0
    while True:
        try:
            if mode == "raid":
                text = f"{base} {RAID_TEXTS[i % len(RAID_TEXTS)]}"
            else:
                text = f"{base} {NCEMO_EMOJIS[i % len(NCEMO_EMOJIS)]}"
            await bot_obj.set_chat_title(chat_id, text)
            i += 1
            await asyncio.sleep(delay)
        except Exception as e:
            print(f"[WARN] Bot error in chat {chat_id}: {e}")
            await asyncio.sleep(2)

# ---------------------------
# COMMANDS
# ---------------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to A Bot!\nUse /help to see all commands.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "A Bot Help Menu\n\n"
        "GC Loops:\n/gcnc <text>\n/ncemo <text>\n/stopgcnc\n/stopall\n/delay <sec>\n/status\n\n"
        "SUDO Management:\n/addsudo (reply)\n/delsudo (reply)\n/listsudo\n\n"
        "Misc:\n/myid\n/ping"
    )

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    msg = await update.message.reply_text("Pinging...")
    end_time = time.time()
    latency = int((end_time - start_time) * 1000)
    await msg.edit_text(f"Pong! {latency} ms")

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your ID: {update.effective_user.id}")

@only_sudo
async def gcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: 
        return await update.message.reply_text("Usage: /gcnc <text>")
    base = " ".join(context.args)
    chat_id = update.message.chat_id
    group_tasks.setdefault(chat_id, {})
    for idx, bot_obj in enumerate(bots):
        if idx not in group_tasks[chat_id]:
            task = asyncio.create_task(bot_loop(bot_obj, chat_id, base, "raid"))
            group_tasks[chat_id][idx] = task
    await update.message.reply_text("GC name loop started.")

@only_sudo
async def ncemo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: 
        return await update.message.reply_text("Usage: /ncemo <text>")
    base = " ".join(context.args)
    chat_id = update.message.chat_id
    group_tasks.setdefault(chat_id, {})
    for idx, bot_obj in enumerate(bots):
        if idx not in group_tasks[chat_id]:
            task = asyncio.create_task(bot_loop(bot_obj, chat_id, base, "emoji"))
            group_tasks[chat_id][idx] = task
    await update.message.reply_text("Emoji loop started.")

@only_sudo
async def stopgcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in group_tasks:
        for task in group_tasks[chat_id].values():
            task.cancel()
        group_tasks[chat_id] = {}
    await update.message.reply_text("Loop stopped in this GC.")

@only_sudo
async def stopall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for chat_id in list(group_tasks.keys()):
        for task in group_tasks[chat_id].values():
            task.cancel()
        group_tasks[chat_id] = {}
    await update.message.reply_text("All active loops stopped.")

@only_sudo
async def delay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global delay
    if not context.args: 
        return await update.message.reply_text(f"Current delay: {delay}s")
    try:
        delay = max(0.5, float(context.args[0]))
        await update.message.reply_text(f"Delay set to {delay}s")
    except: 
        await update.message.reply_text("Invalid number.")

@only_sudo
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "Active Loops:\n"
    for chat_id, tasks in group_tasks.items():
        msg += f"Chat {chat_id}: {len(tasks)} bots running\n"
    await update.message.reply_text(msg)

# ---------------------------
# BUILD APP
# ---------------------------
def build_app(token):
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("gcnc", gcnc))
    app.add_handler(CommandHandler("ncemo", ncemo))
    app.add_handler(CommandHandler("stopgcnc", stopgcnc))
    app.add_handler(CommandHandler("stopall", stopall))
    app.add_handler(CommandHandler("delay", delay_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    return app

# ---------------------------
# FLASK WEBHOOK ENDPOINTS
# ---------------------------
@app_flask.route('/')
def index():
    return "All 7 Bots are live via Webhooks on Render!"

@app_flask.route('/webhook/<int:bot_idx>', methods=['POST'])
def telegram_webhook(bot_idx):
    if bot_idx in apps_dict:
        app = apps_dict[bot_idx]
        try:
            req_json = request.get_json(force=True)
            asyncio.run_coroutine_threadsafe(
                app.update_queue.put(Update.de_json(req_json, app.bot)),
                app.loop if hasattr(app, 'loop') else asyncio.get_event_loop()
            )
        except Exception as e:
            print(f"Error processing update for bot {bot_idx}: {e}")
    return 'OK', 200

# ---------------------------
# STARTUP MAIN FUNCTION
# ---------------------------
async def run_all_bots():
    global apps, bots, apps_dict
    current_loop = asyncio.get_running_loop()
    
    for idx, token in enumerate(TOKENS):
        if token.strip():
            try:
                bot_obj = Bot(token)
                bots.append(bot_obj)
                
                app = build_app(token)
                app.loop = current_loop
                apps.append(app)
                apps_dict[idx] = app
            except Exception as e:
                print("Failed building app:", e)

    # Initialize and Start Webhooks
    for idx, app in apps_dict.items():  
        try:  
            await app.initialize()
            await app.start()
            
            # Webhook url register karne ke liye टेलीग्राम को भेजना
            webhook_url = f"{MY_RENDER_URL}/webhook/{idx}"
            await app.bot.set_webhook(url=webhook_url)
            print(f"Webhook successfully set for Bot {idx}: {webhook_url}")
        except Exception as e:  
            print(f"Failed starting app {idx}: {e}")  

    print("System Online: All 7 Bots initialized successfully on Webhooks.")

def start_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    from threading import Thread
    # 1. Start Flask immediately for Port Binding
    Thread(target=start_flask, daemon=True).start()
    
    # 2. Run Telegram Event Loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_all_bots())
    loop.run_forever()
