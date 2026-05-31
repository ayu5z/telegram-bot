import asyncio
import json
import os
import random
import time
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import nest_asyncio

# Loop aur async conflicts ko jad se khatam karne ke liye
nest_asyncio.apply()

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
MY_RENDER_URL = "https://telegram-bot-fsx5.onrender.com"

app_flask = Flask('')
logging.basicConfig(level=logging.INFO)

# ---------------------------
# CLEANED SPAM & RAID TEXTS
# ---------------------------
RAID_TEXTS = [
    "Try ben ci bhosadi beta 😹😹🔥🔥", "Try ma randy 🤣🤣❤️‍🔥❤️‍🔥", "Teri mom ko i love u ree 💋💋🤣🤣",
    "Tmkc pe chppl hi chppl marunga !! 🤤🤤🤤🤤", "Teri maa randy ⚡⚡⚡⚡", "Chl Harmazaadi Ke ladke 💦💦💦💦",
    "hlw hlw mja aarha cudne me? 🫦🗣️🗣️", "bina ruke thukai hogi teri 😈😈😈😈", "kr na fyt 😹😹🔥🔥",
    "hlw reply fas 🤣🤣❤️‍🔥❤️‍🔥", "sort nhi krunga cud tu bina ruke 💋💋🤣🤣", "kaale Doraemon rota reh 🤤🤤🤤🤤",
    "teri bkc me bigboss ⚡⚡⚡⚡", "Awaz neeche rndy k bacche 💦💦💦💦", "Sawal mt puch tery ma k bosda"
]

NCEMO_EMOJIS = [
    "😭😭😭😭", "🗿🗿🗿🗿", "🎀🎀🎀🎀", "❤️❤️❤️❤️", "🔥🔥🔥🔥", "💘💘💘💘", "🤎🤎🤎🤎", 
    "💌💌💌💌", "🤍🤍🤍🤍", "🖤🖤🖤🖤", "💜💜💜💜", "💙💙💙💙", "💛💛💛💛", "🧡🧡🧡🧡", 
    "🌷🌷🌷🌷", "😈😈😈😈", "🌺🌺🌺🌺"
]

SPAM_TEXTS = [
    "घिनौनी रण्डी के बच्चे उड़ कबूतर मादार चोद 🗿🖕🏻तू बात बात पर अपनी मां क्यों चूदवाता ह 🤔🤔",
    "𝙏𝙚𝙧𝙞 𝙢𝙖𝙖 𝙠𝙚 𝙗𝙝𝙤𝙨𝙙𝙚 𝙢𝙚 𝙡𝙖𝙩 𝙥𝙙𝙚𝙣𝙜𝙚 𝙗𝙝ото 𝙩𝙚𝙯 ghost 😂👯😂👯😂👯 😂👯😂👯😂👯 😂👯😂👯😂👯",
    "teri ma ko mahadev ke pas bhej dunga mc 😂🔥",
    "हमारा कोई मा बाप नहीं hai hum upar se rocket me baith ke aaye the aapki ma chodne aaye hai beta😁🤙\n😂🔥😂🔥😂🔥😂🔥😂🔥😂🔥😂🔥😂🔥😂👿😂",
    "𝟕 रंग 𝐤 सात 🕊️ सातो खाए दाना \nतेरी मां टांग फेलाए चोदे पूरा हरियाणा\n😂🙏🏿‼️📞🚨💯",
    "मेरे हाथ में लंड hai koi asla to nahi? इसे तेरी माँ चोd दूं ? Koi masla to nahi ? 🤢❤️‍🔥",
    "teri चुट पे itne balle marungi IPL jeet jayegi 😄😄🖕🏿🖕🏿",
    "Tera baap khaye fried rice tri ma chudke bole wow nice😹⚡🔫🔥👑",
    "Chup घिनौनी ma ke पागल ladke teri ma ko gile kambal me dalkr chodunga 🤪😹🤪😹"
]

CUTE_EMOJI_DESIGNS = [
    " 💞🌸💞🌸 ", " 💗🌹💗🌹 ", " 🦋✨🦋✨ ", " 🎀🧸🎀🧸 ", " 💌💮💌💮 ", " ⭐✨⭐✨ ", " 💘🎀💘🎀 ", " 🤍🌷🤍🌷 "
]

# ---------------------------
# GLOBAL STATE & VARIABLES
# ---------------------------
SUDO_USERS = {OWNER_ID}
group_tasks, heavy_spam_tasks, custom_spam_tasks = {}, {}, {}
target_slide_tasks, swipe_tasks = {}, {}
apps, bots, apps_dict = [], [], {}
delay = 2.0  

def only_sudo(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in SUDO_USERS: 
            return
        return await func(update, context)
    return wrapper

# ---------------------------
# SAFE BACKGROUND LOOPS (Anti-Crash & Rate Limit Protected)
# ---------------------------
async def bot_loop(bot_obj, chat_id, base, mode):
    i = 0
    while True:
        try:
            text_part = RAID_TEXTS[i % len(RAID_TEXTS)] if mode == "raid" else NCEMO_EMOJIS[i % len(NCEMO_EMOJIS)]
            full_title = f"{base} {text_part}"
            await bot_obj.set_chat_title(chat_id=chat_id, title=full_title[:100])
            i += 1
            # GC name change loop ko thoda space dena zaroori hai anti-flood ke liye
            await asyncio.sleep(max(4.0, delay + 1.0))
        except Exception as e:
            # Server error aaye toh bot marega nahi, wait karke automatic restart hoga
            await asyncio.sleep(5)

async def heavy_spam_loop(bot_obj, chat_id, prefix_text):
    i = 0
    while True:
        try:
            text = f"{prefix_text} {SPAM_TEXTS[i % len(SPAM_TEXTS)]}" if prefix_text else SPAM_TEXTS[i % len(SPAM_TEXTS)]
            await bot_obj.send_message(chat_id=chat_id, text=text)
            i += 1
            await asyncio.sleep(delay)
        except Exception:
            await asyncio.sleep(3)

async def dynamic_spam_loop(bot_obj, chat_id, user_text):
    i = 0
    while True:
        try:
            lines = [f"{user_text}{CUTE_EMOJI_DESIGNS[(i + j) % len(CUTE_EMOJI_DESIGNS)]}{user_text}" for j in range(5)]
            await bot_obj.send_message(chat_id=chat_id, text="\n".join(lines))
            i += 1
            await asyncio.sleep(delay)
        except Exception:
            await asyncio.sleep(3)

async def target_slide_loop(bot_obj, chat_id, reply_to_msg_id):
    i = 0
    while True:
        try:
            text = f"Target Locked 🎯 {RAID_TEXTS[i % len(RAID_TEXTS)]}"
            await bot_obj.send_message(chat_id=chat_id, text=text, reply_to_message_id=reply_to_msg_id)
            i += 1
            await asyncio.sleep(delay)
        except Exception:
            await asyncio.sleep(3)

async def swipe_loop(bot_obj, chat_id, target_name):
    i = 0
    while True:
        try:
            text = f"⚡ Swipe Attack on {target_name} ⚡\n{SPAM_TEXTS[i % len(SPAM_TEXTS)]}"
            await bot_obj.send_message(chat_id=chat_id, text=text)
            i += 1
            await asyncio.sleep(delay)
        except Exception:
            await asyncio.sleep(3)

# ---------------------------
# COMMAND HANDLERS & HELP MENU
# ---------------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Multi-bot system is online 24/7.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    old_help_menu = (
        "**A Bot Help Menu**\n\n"
        "**GC Loops:**\n"
        "/gcnc `<text>`\n"
        "/ncemo `<text>`\n"
        "/stopgcnc\n"
        "/stopall\n"
        "/delay `<sec>`\n"
        "/status\n\n"
        "**Traditional Heavy Spam:**\n"
        "/spam\n"
        "/spam `<text>`\n"
        "/stopspam\n\n"
        "**Custom Paragraph Loops:**\n"
        "/spamloop `<your text>`\n"
        "/endspamloop\n\n"
        "**Target Slide & Spam:**\n"
        "/targetslide (reply)\n"
        "/stopslide (reply)\n"
        "/slidespam (reply)\n"
        "/stopslidespam (reply)\n\n"
        "**Swipe Mode:**\n"
        "/swipe `<name>`\n"
        "/stopswipe\n\n"
        "**SUDO Management:**\n"
        "/addsudo (reply)\n"
        "/delsudo (reply)\n"
        "/listsudo\n\n"
        "**Misc:**\n"
        "/ping"
    )
    await update.message.reply_text(old_help_menu, parse_mode="Markdown")

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t1 = time.time()
    msg = await update.message.reply_text("💥 Checking Ping...")
    await msg.edit_text(f"🚀 Speed Pong: {int((time.time() - t1) * 1000)} ms")

@only_sudo
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📊 **System Status:**\n- Active Bots: {len(bots)}\n- Current Delay: {delay}s\n- Server: Live 24/7", parse_mode="Markdown")

@only_sudo
async def delay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global delay
    if context.args:
        try:
            delay = float(context.args[0])
            await update.message.reply_text(f"⚙️ Delay updated to {delay} seconds.")
        except ValueError:
            await update.message.reply_text("Provide a valid number.")

@only_sudo
async def spam_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prefix = " ".join(context.args) if context.args else ""
    chat_id = update.message.chat_id
    heavy_spam_tasks.setdefault(chat_id, {})
    for idx, bot_obj in enumerate(bots):
        if idx not in heavy_spam_tasks[chat_id]:
            heavy_spam_tasks[chat_id][idx] = asyncio.create_task(heavy_spam_loop(bot_obj, chat_id, prefix))
    await update.message.reply_text("🔥 7 Bots Heavy Spam Started Non-Stop!")

@only_sudo
async def stopspam_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in heavy_spam_tasks:
        for t in heavy_spam_tasks[chat_id].values(): t.cancel()
        heavy_spam_tasks[chat_id] = {}
    await update.message.reply_text("🛑 Heavy spam stopped.")

@only_sudo
async def spamloop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /spamloop <text>")
    user_text = " ".join(context.args)
    chat_id = update.message.chat_id
    custom_spam_tasks.setdefault(chat_id, {})
    for idx, bot_obj in enumerate(bots):
        if idx not in custom_spam_tasks[chat_id]:
            custom_spam_tasks[chat_id][idx] = asyncio.create_task(dynamic_spam_loop(bot_obj, chat_id, user_text))
    await update.message.reply_text("✨ 7 Bots Paragraph Loop Started!")

@only_sudo
async def endspamloop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in custom_spam_tasks:
        for t in custom_spam_tasks[chat_id].values(): t.cancel()
        custom_spam_tasks[chat_id] = {}
    await update.message.reply_text("🛑 Custom loop stopped.")

@only_sudo
async def targetslide_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("Bhai reply karke command do!")
    reply_id = update.message.reply_to_message.message_id
    chat_id = update.message.chat_id
    target_slide_tasks.setdefault(chat_id, {})
    for idx, bot_obj in enumerate(bots):
        if idx not in target_slide_tasks[chat_id]:
            target_slide_tasks[chat_id][idx] = asyncio.create_task(target_slide_loop(bot_obj, chat_id, reply_id))
    await update.message.reply_text("🎯 Target Locked! Slide attack activated.")

@only_sudo
async def stopslide_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in target_slide_tasks:
        for t in target_slide_tasks[chat_id].values(): t.cancel()
        target_slide_tasks[chat_id] = {}
    await update.message.reply_text("🛑 Target Slide stopped.")

@only_sudo
async def swipe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /swipe <name>")
    target_name = " ".join(context.args)
    chat_id = update.message.chat_id
    swipe_tasks.setdefault(chat_id, {})
    for idx, bot_obj in enumerate(bots):
        if idx not in swipe_tasks[chat_id]:
            swipe_tasks[chat_id][idx] = asyncio.create_task(swipe_loop(bot_obj, chat_id, target_name))
    await update.message.reply_text(f"⚡ Swipe mode activated on {target_name}!")

@only_sudo
async def stopswipe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in swipe_tasks:
        for t in swipe_tasks[chat_id].values(): t.cancel()
        swipe_tasks[chat_id] = {}
    await update.message.reply_text("🛑 Swipe mode stopped.")

@only_sudo
async def gcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /gcnc <text>")
    base = " ".join(context.args)
    chat_id = update.message.chat_id
    group_tasks.setdefault(chat_id, {})
    for idx, bot_obj in enumerate(bots):
        if idx not in group_tasks[chat_id]:
            group_tasks[chat_id][idx] = asyncio.create_task(bot_loop(bot_obj, chat_id, base, "raid"))
    await update.message.reply_text("GC name loop started.")

@only_sudo
async def ncemo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("Usage: /ncemo <text>")
    base = " ".join(context.args)
    chat_id = update.message.chat_id
    group_tasks.setdefault(chat_id, {})
    for idx, bot_obj in enumerate(bots):
        if idx not in group_tasks[chat_id]:
            group_tasks[chat_id][idx] = asyncio.create_task(bot_loop(bot_obj, chat_id, base, "emoji"))
    await update.message.reply_text("Emoji loop started.")

@only_sudo
async def stopgcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id in group_tasks:
        for t in group_tasks[chat_id].values(): t.cancel()
        group_tasks[chat_id] = {}
    await update.message.reply_text("Loop stopped in this GC.")

@only_sudo
async def addsudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        SUDO_USERS.add(user_id)
        await update.message.reply_text(f"✅ User {user_id} added to Sudo.")

@only_sudo
async def delsudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        if user_id != OWNER_ID:
            SUDO_USERS.discard(user_id)
            await update.message.reply_text(f"❌ User {user_id} removed from Sudo.")

@only_sudo
async def listsudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"👑 **Sudo Users List:**\n" + "\n".join([f"- `{u}`" for u in SUDO_USERS]), parse_mode="Markdown")

@only_sudo
async def stopall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for d in [group_tasks, heavy_spam_tasks, custom_spam_tasks, target_slide_tasks, swipe_tasks]:
        for cid in list(d.keys()):
            for t in d[cid].values(): t.cancel()
            d[cid] = {}
    await update.message.reply_text("All active loops stopped globally.")

def build_app(token):
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("delay", delay_cmd))
    app.add_handler(CommandHandler("gcnc", gcnc))
    app.add_handler(CommandHandler("ncemo", ncemo))
    app.add_handler(CommandHandler("stopgcnc", stopgcnc))
    app.add_handler(CommandHandler("spam", spam_cmd))        
    app.add_handler(CommandHandler("stopspam", stopspam_cmd))
    app.add_handler(CommandHandler("spamloop", spamloop_cmd))        
    app.add_handler(CommandHandler("endspamloop", endspamloop_cmd))  
    app.add_handler(CommandHandler("targetslide", targetslide_cmd))
    app.add_handler(CommandHandler("slidespam", targetslide_cmd))
    app.add_handler(CommandHandler("stopslide", stopslide_cmd))
    app.add_handler(CommandHandler("stopslidespam", stopslide_cmd))
    app.add_handler(CommandHandler("swipe", swipe_cmd))
    app.add_handler(CommandHandler("stopswipe", stopswipe_cmd))
    app.add_handler(CommandHandler("addsudo", addsudo_cmd))
    app.add_handler(CommandHandler("delsudo", delsudo_cmd))
    app.add_handler(CommandHandler("listsudo", listsudo_cmd))
    app.add_handler(CommandHandler("stopall", stopall))
    return app

# ---------------------------
# FLASK WEBHOOK ENDPOINTS
# ---------------------------
@app_flask.route('/')
def index(): 
    return "All 7 Bots are live 24/7 without break!"

@app_flask.route('/webhook/<int:bot_idx>', methods=['POST'])
def telegram_webhook(bot_idx):
    if bot_idx in apps_dict:
        app = apps_dict[bot_idx]
        try:
            req_json = request.get_json(force=True)
            asyncio.run_coroutine_threadsafe(
                app.update_queue.put(Update.de_json(req_json, app.bot)),
                main_loop
            )
        except Exception: pass
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
                bots.append(Bot(token))
                app = build_app(token)
                app.loop = current_loop
                apps.append(app)
                apps_dict[idx] = app
            except Exception: pass

    # Tasks ko ek sath schedule karne ke liye secure gathering use kari hai
    init_tasks = []
    for idx, app in apps_dict.items():  
        async def start_single_bot(b_idx, b_app):
            try:  
                await b_app.initialize()
                await b_app.start()
                await b_app.bot.delete_webhook(drop_pending_updates=True)
                await asyncio.sleep(0.5) # Har bot ke set_webhook ke beech gap taaki rate limit na aaye
                await b_app.bot.set_webhook(url=f"{MY_RENDER_URL}/webhook/{b_idx}")
                print(f"Webhook Bound Successfully: Bot {b_idx}")
            except Exception as e: 
                print(f"Failed starting bot {b_idx}: {e}")
        init_tasks.append(start_single_bot(idx, app))
        
    await asyncio.gather(*init_tasks)
    print("Everything is Setup. Bots are completely live in background!")

def start_flask_server():
    port = int(os.environ.get("PORT", 8080))
    print("Starting Flask Webhook Server...")
    app_flask.run(host='0.0.0.0', port=port, threaded=True, use_reloader=False)

if __name__ == "__main__":
    main_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(main_loop)
    
    from threading import Thread
    Thread(target=start_flask_server, daemon=True).start()
    
    main_loop.run_until_complete(run_all_bots())
    main_loop.run_forever()
