#!/usr/bin/env python3
"""
Premium Telegram bot for Render Web Service with JSON file storage:
- Enhanced premium UI for all messages
- Flask keep-alive routes (/) and (/ping-test)
- Uses JSON file storage for persistence across restarts
- Features: join-check, referral, balance, bonus, stock withdraw, admin broadcast
- Premium support and buy interfaces
"""

import os
import time
import threading
import traceback
import json
from collections import defaultdict

# Import with error handling
try:
    import telebot
    from telebot import types
    from flask import Flask
except ImportError as e:
    print(f"Import error: {e}")
    print("Please make sure all required packages are installed")
    # Exit gracefully
    import sys
    sys.exit(1)

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN is not set. Set it via environment variable.")
    # Exit if no token
    import sys
    sys.exit(1)
    
OWNER_ID = 8048054789
ADMINS = [2115677414]  # Other admins (without owner)
ALL_ADMINS = [OWNER_ID] + ADMINS  # All admins including owner for notifications
CHANNELS = [
    {"id": "@jak_paradise", "url": "https://t.me/jak_paradise"},
    {"id": "-1002408750694", "url": "https://t.me/+tU7esamIk45jZTg0"},
    {"id": "-1002964116333", "url": "https://t.me/+yOTZqVq194s0OTk0"},
    {"id": "-1002793343378", "url": "https://t.me/+frT0WdQQPwQ1YzY0"}
]
CHANNEL_ID_FOR_REF = -1002964116333
SEND_DELAY = float(os.getenv("SEND_DELAY", "0.1"))  # Increased delay for safety

# ---------------- Bot & Flask ----------------
bot = telebot.TeleBot(BOT_TOKEN)
# ... rest of your code ...

if __name__ == "__main__":
    print("Starting Instagram Old Age bot in background thread...")
    t = threading.Thread(target=run_bot_loop)
    t.daemon = True
    t.start()
    port = int(os.getenv("PORT", "10000"))
    print(f"Starting Flask server on port {port}")

    app.run(host="0.0.0.0", port=port)
# ---------------- JSON File Storage ----------------
DATA_FILE = "bot_data.json"

def load_data():
    """Load data from JSON file"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading data: {e}")
    return {"users": {}, "stock": []}

def save_data():
    """Save data to JSON file"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({
                "users": users_dict,
                "stock": stock_list
            }, f)
    except Exception as e:
        print(f"Error saving data: {e}")

# Load initial data
data = load_data()
users_dict = data.get("users", {})
stock_list = data.get("stock", [])

# ---------------- Helpers ----------------
def is_owner(uid: int) -> bool:
    return uid == OWNER_ID

def is_admin(uid: int) -> bool:
    return uid in ALL_ADMINS

def send_to_admins(text: str, parse_mode=None):
    for a in ALL_ADMINS:
        try:
            bot.send_message(a, text, parse_mode=parse_mode)
        except Exception as e:
            print(f"Failed notify admin {a}: {e}")

def format_user_info(user):
    name = getattr(user, "first_name", "") or ""
    uname = f"@{user.username}" if getattr(user, "username", None) else "❌ No Username"
    return f"•🥂 Name:- {name} • 🎀\nUsername :- {uname} 💎\nID: {user.id} ☠"

def add_user(user_id, username, ref_id=None, user=None):
    user_id_str = str(user_id)
    is_new_user = False
    
    # Initialize user if not exists
    if user_id_str not in users_dict:
        users_dict[user_id_str] = {
            "username": username,
            "balance": 0,
            "referred_by": ref_id,
            "last_bonus": 0
        }
        is_new_user = True
        save_data()  # Save after adding new user
    
    # Notify admins only for new users
    if is_new_user and user:
        total_users = len(users_dict)
        send_to_admins(f"🔔 New user started the bot:\nTotal :- {total_users}\n{format_user_info(user)}")

    # Handle referral (only for new users to prevent duplicate referrals)
    if is_new_user and ref_id and str(ref_id) in users_dict:
        users_dict[str(ref_id)]["balance"] += 3
        save_data()  # Save after updating referral balance
        try:
            # Referral notification
            referral_text = (
                "🎊 <b>REFERRAL BONUS UNLOCKED!</b> 🎊\n\n"
                "⭐ <b>+3 DIAMONDS</b> added to your account!\n"
                "💎 Your friend joined using your referral link!\n\n"
                "🔥 <b>Keep inviting to earn more rewards!</b>"
            )
            bot.send_message(ref_id, referral_text, parse_mode="HTML")
        except Exception as e:
            print(f"Could not notify referrer {ref_id}: {e}")
    
    return is_new_user

def get_balance(user_id):
    user_id_str = str(user_id)
    if user_id_str in users_dict:
        return users_dict[user_id_str]["balance"]
    return 0

def update_balance(user_id, amount):
    user_id_str = str(user_id)
    if user_id_str in users_dict:
        users_dict[user_id_str]["balance"] += amount
        save_data()  # Save after updating balance

def _normalize_chat_id(chat_id_field):
    if isinstance(chat_id_field, int):
        return chat_id_field
    if isinstance(chat_id_field, str):
        if chat_id_field.startswith("@"):
            return chat_id_field
        try:
            return int(chat_id_field)
        except:
            return chat_id_field
    return chat_id_field

def check_subscription(user_id):
    for ch in CHANNELS:
        chat_id = _normalize_chat_id(ch["id"])
        try:
            member = bot.get_chat_member(chat_id, user_id)
            if getattr(member, "status", "") in ["left", "kicked"]:
                return False
        except Exception as e:
            print(f"Subscription check failed for {ch['id']}: {e}")
            return False
    return True

def send_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💎 Balance", "👥 Referral Link")
    markup.add("🎁 Bonus", "⚡ Withdraw")
    markup.add("🆘 Support", "🛒 Buy")
    
    welcome_text = (
        "🌟 <b>DIAMOND BOT</b> 🌟\n\n"
        "✨ Welcome to the ultimate earning experience!\n"
        "💎 Collect diamonds and redeem amazing rewards!\n\n"
        "👇 <b>Choose an option from the menu below:</b>"
    )
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode="HTML")

def send_join_prompt(user_id):
    markup = types.InlineKeyboardMarkup()
    for ch in CHANNELS:
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=ch["url"]))
    markup.add(types.InlineKeyboardButton("✅ I Joined", callback_data="check_subs"))
    text = (
        "🚀 <b>Welcome to Premium Diamond Bot</b> 🚀\n\n"
        "🔒 To accessa our bot features, please <b>join all our channels</b> below:\n\n"
        "⭐ Instagram Old Age\n"
        "💎 Daily bonuses\n"
        "🎁 Special rewards\n\n"
        "👉 After joining, press the <b>✅ I Joined</b> button to verify."
    )
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")

# ---------------- Handlers ----------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    args = message.text.split()
    ref = None
    if len(args) > 1:
        try:
            ref = int(args[1])
        except:
            ref = None
    
    # Add user and check if it's a new user
    is_new_user = add_user(user_id, username, ref, message.from_user)
    
    if check_subscription(user_id):
        send_main_menu(user_id)
    else:
        send_join_prompt(user_id)

@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def callback_check(call):
    uid = call.from_user.id
    if check_subscription(uid):
        try:
            bot.edit_message_text(
                "✅ <b>Verification Successful!</b>\n\n"
                "🎉 Welcome to our Instagram Old Age Bot!\n"
                "⭐ You now have access to all features.",
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
        except:
            pass
        send_main_menu(uid)
    else:
        bot.answer_callback_query(call.id, "❌ Please join all required channels first!")

# ========== Admin: Stock ==========
@bot.message_handler(commands=['addstock'])
def add_stock(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Only admins can use this command!")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "⚠ Usage: /addstock Reward Text")
        return
    reward = args[1]
    stock_list.append(reward)
    save_data()  # Save after adding stock
    bot.reply_to(message, f"✅ Stock added:\n{reward}")

@bot.message_handler(commands=['checkstock'])
def check_stock(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Only admins can use this command!")
        return
    bot.reply_to(message, f"📦 Current stock count: {len(stock_list)} item(s)")

@bot.message_handler(commands=['stocklist'])
def stock_list_cmd(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Only owner can use this command!")
        return
    if not stock_list:
        bot.reply_to(message, "📦 Stock is empty.")
        return
    
    text = "📦 Current Stock Items:\n\n"
    for i, reward in enumerate(stock_list, 1):
        text += f"ID: {i} | Reward: {reward}\n"
    bot.reply_to(message, text)

# ========== Owner: Admin Management ==========
@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Only owner can use this command!")
        return
    try:
        new_admin_id = int(message.text.split()[1])
        if new_admin_id not in ADMINS:
            ADMINS.append(new_admin_id)
            ALL_ADMINS.append(new_admin_id)
            bot.reply_to(message, f"✅ User {new_admin_id} added to admins!")
        else:
            bot.reply_to(message, "⚠ User is already an admin!")
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Usage: /addadmin <user_id>")

@bot.message_handler(commands=['delete'])
def delete_user(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Only owner can use this command!")
        return
    try:
        user_id = int(message.text.split()[1])
        user_id_str = str(user_id)
        if user_id_str in users_dict:
            del users_dict[user_id_str]
            save_data()  # Save after deleting user
            bot.reply_to(message, f"✅ User {user_id} deleted!")
        else:
            bot.reply_to(message, f"❌ User {user_id} not found!")
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Usage: /delete <user_id>")

# ========== Admin: Broadcast ==========
@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Only admins can use this command!")
        return
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        send_broadcast_text(message.from_user.id, args[1])
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 Forward Mode", callback_data="broadcast_forward"))
        markup.add(types.InlineKeyboardButton("📝 Resend Mode", callback_data="broadcast_resend"))
        bot.send_message(message.chat.id, "📢 Choose broadcast mode:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["broadcast_forward", "broadcast_resend"])
def choose_broadcast_mode(call):
    if not is_admin(call.from_user.id):
        return
    mode = "forward" if call.data == "broadcast_forward" else "resend"
    m = bot.send_message(call.message.chat.id, "📩 Please send the content (text/photo/video/document/audio/voice/sticker/GIF) you want to broadcast.")
    bot.register_next_step_handler(m, lambda mm: process_broadcast(mm, mode))

def process_broadcast(message, mode):
    if not is_admin(message.from_user.id):
        return
        
    users = list(users_dict.keys())
    total = len(users)
    sent = 0
    failed = 0
    errors = []
    for uid in users:
        try:
            if mode == "forward":
                bot.forward_message(int(uid), message.chat.id, message.message_id)
            else:
                ct = message.content_type
                if ct == "text":
                    bot.send_message(int(uid), f"📢 <b>Admin Message:</b>\n\n{message.text}", parse_mode="HTML")
                elif ct == "photo":
                    bot.send_photo(int(uid), message.photo[-1].file_id, caption=f"📢 <b>Admin Message:</b>\n\n{message.caption or ''}", parse_mode="HTML")
                elif ct == "video":
                    bot.send_video(int(uid), message.video.file_id, caption=f"📢 <b>Admin Message:</b>\n\n{message.caption or ''}", parse_mode="HTML")
                elif ct == "document":
                    bot.send_document(int(uid), message.document.file_id, caption=f"📢 <b>Admin Message:</b>\n\n{message.caption or ''}", parse_mode="HTML")
                elif ct == "voice":
                    bot.send_voice(int(uid), message.voice.file_id)
                elif ct == "audio":
                    bot.send_audio(int(uid), message.audio.file_id)
                elif ct == "sticker":
                    bot.send_sticker(int(uid), message.sticker.file_id)
                elif ct == "animation":
                    bot.send_animation(int(uid), message.animation.file_id, caption=f"{message.caption or ''}")
                else:
                    bot.send_message(int(uid), "📢 Admin sent an update (unsupported media type).")
            sent += 1
        except Exception as e:
            failed += 1
            errors.append(f"User {uid}: {e}")
        finally:
            time.sleep(SEND_DELAY)
    # report
    report = (
        "📢 <b>Broadcast Status</b>\n\n"
        f"👥 Total Users in Bot: <b>{total}</b>\n"
        f"📩 Messages Sent: <b>{sent}</b>\n"
        f"❌ Failed to Send: <b>{failed}</b>\n"
    )
    if errors:
        report += "\n\n⚠ Errors (sample):\n" + "\n".join(errors[:8])
    bot.send_message(message.from_user.id, report, parse_mode="HTML")

def send_broadcast_text(admin_id, text):
    users = list(users_dict.keys())
    total = len(users)
    sent = 0
    failed = 0
    errors = []
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 <b>Admin Message:</b>\n\n{text}", parse_mode="HTML")
            sent += 1
        except Exception as e:
            failed += 1
            errors.append(f"User {uid}: {e}")
        finally:
            time.sleep(SEND_DELAY)
    report = (
        "📢 <b>Broadcast Status</b>\n\n"
        f"👥 Total Users in Bot: <b>{total}</b>\n"
        f"📩 Messages Sent: <b>{sent}</b>\n"
        f"❌ Failed to Send: <b>{failed}</b>\n"
    )
    if errors:
        report += "\n\n⚠ Errors (sample):\n" + "\n".join(errors[:8])
    bot.send_message(admin_id, report, parse_mode="HTML")

# ========== Support & Buy Interfaces ==========
@bot.message_handler(func=lambda m: m.text == "🆘 Support")
def handle_support(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👨‍💻 Contact Support", url="https://t.me/Jakhelper_bot"))
    
    support_text = (
        "👋 <b>Support Center</b> 👑\n\n"
        "⭐ <b>24/7 Dedicated Support</b>\n"
        "🔧 Technical assistance\n"
        "💡 Guidance and help\n\n"
        "• 👨‍💻 <b>Contact Support</b>: Direct line to our expert team\n\n"
        "<i>We're here to help you anytime!</i>"
    )
    bot.send_message(message.chat.id, support_text, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🛒 Buy")
def handle_buy(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👨‍💻 Contact for Purchase", url="https://t.me/Jakhelper_bot"))
    
    buy_text = (
        "🛒 <b>Stock Store</b> 👑\n\n"
        "⭐ <b>Exclusive Collection (2012-2019)</b>\n"
        "💎 Complete archive available\n"
        "🚀 Fast delivery guaranteed\n\n"
        "• 🔍 If you want to buy then DM 👇🏻\n\n"
        
    )
    bot.send_message(message.chat.id, buy_text, reply_markup=markup, parse_mode="HTML")

# ========== User menu and withdraw ==========
@bot.message_handler(func=lambda m: True)
def menu_handler(message):
    uid = message.from_user.id
    uid_str = str(uid)
    txt = (message.text or "").strip()
    # nudge join if not joined
    if not check_subscription(uid):
        send_join_prompt(uid)
        return
        
    if txt == "💎 Balance":
        bal = get_balance(uid)
        # Count referrals
        refs = sum(1 for user_id, user_data in users_dict.items() 
                  if user_data.get("referred_by") == uid)
                  
        balance_text = (
            "💰 <b>ACCOUNT BALANCE</b> 👑\n\n"
            f"💎 <b>Diamonds:</b> {bal}\n"
            f"👥 <b>Total Referrals:</b> {refs}\n\n"
            "⭐ <b>Earn More Diamonds:</b>\n"
            "• Invite friends: +3 diamonds each\n"
            "• Daily bonus: +2 diamonds every 24h\n"            
            "🔥 <b>Keep earning to unlock amazing rewards!</b>"
        )
        bot.send_message(uid, balance_text, parse_mode="HTML")
        
    elif txt == "👥 Referral Link":
        bot_info = bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={uid}"
        # Count referrals
        refs = sum(1 for user_id, user_data in users_dict.items() 
                  if user_data.get("referred_by") == uid)
                  
        referral_text = (
            "👥 <b>REFERRAL PROGRAM</b> 👑\n\n"
            f"🔗 <b>Your Personal Link:</b>\n<code>{link}</code>\n\n"
            f"⭐ <b>Total Referrals:</b> {refs}\n"
            f"💎 <b>Earned from Referrals:</b> {refs * 3} diamonds\n\n"
            "🎯 <b>How it works:</b>\n"
            "• Share your link with friends\n"
            "• Get +3 diamonds for each referral\n"
            "• No limit on how many you can refer\n\n"
            "🔥 <b>Start inviting to maximize your earnings!</b>"
        )
        bot.send_message(uid, referral_text, parse_mode="HTML")
        
    elif txt == "🎁 Bonus":
        if uid_str not in users_dict:
            users_dict[uid_str] = {"username": message.from_user.username or "", "balance": 0, "referred_by": None, "last_bonus": 0}
            
        last = users_dict[uid_str]["last_bonus"]
        now = int(time.time())
        if now - last >= 86400:
            update_balance(uid, 2)
            users_dict[uid_str]["last_bonus"] = now
            save_data()  # Save after claiming bonus
            
            bonus_text = (
                "🎁 <b>DAILY BONUS COLLECTED!</b> 🎉\n\n"
                "⭐ <b>+2 DIAMONDS</b> added to your account!\n\n"
                "💎 <b>Total Balance:</b> {}\n\n"
                "🔥 <b>Come back in 24 hours for more rewards!</b>"
            ).format(get_balance(uid))
            bot.send_message(uid, bonus_text, parse_mode="HTML")
        else:
            rem = 86400 - (now - last)
            hrs = rem // 3600
            mins = (rem % 3600) // 60
            
            bonus_text = (
                "⏳ <b>DAILY BONUS COOLDOWN</b> ⏳\n\n"
                "✨ You've already collected your daily bonus!\n\n"
                "🕒 <b>Time until next bonus:</b>\n"
                f"• {hrs} hours {mins} minutes\n\n"
                "⭐ <b>Check back later for more rewards!</b>"
            )
            bot.send_message(uid, bonus_text, parse_mode="HTML")
            
    elif txt == "⚡ Withdraw":
        bal = get_balance(uid)
        if bal >= 7:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Confirm Withdrawal", callback_data="withdraw_confirm"))
            
            withdraw_text = (
                "⚡ <b>WITHDRAWAL REQUEST</b> 👑\n\n"
                f"💎 <b>Your Balance:</b> {bal} diamonds\n"
                "💰 <b>Withdrawal Cost:</b> 7 diamonds\n\n"
                "🎁 <b>You will receive:</b>\n"
                "• Exclusive reward from our stock\n"
                "• Instant delivery after confirmation\n\n"
                "⚠ <b>Note:</b> This action cannot be undone\n\n"
                "👇 <b>Confirm to proceed with withdrawal</b>"
            )
            bot.send_message(uid, withdraw_text, reply_markup=markup, parse_mode="HTML")
        else:
            withdraw_text = (
                "❌ <b>INSUFFICIENT BALANCE</b> ❌\n\n"
                f"💎 <b>Your Balance:</b> {bal} diamonds\n"
                "💰 <b>Required for Withdrawal:</b> 7 diamonds\n\n"
                "⭐ <b>Ways to earn more diamonds:</b>\n"
                "• Invite friends: +3 diamonds each\n"
                "• Daily bonus: +2 diamonds every 24h\n\n"
                "🔥 <b>Keep earning to unlock amazing rewards!</b>"
            )
            bot.send_message(uid, withdraw_text, parse_mode="HTML")
    else:
        # Support and Buy are handled by separate handlers above
        pass

@bot.callback_query_handler(func=lambda call: call.data == "withdraw_confirm")
def confirm_withdraw(call):
    uid = call.from_user.id
    uid_str = str(uid)
    bal = get_balance(uid)
    if bal >= 7:
        if stock_list:
            reward = stock_list.pop(0)
            update_balance(uid, -7)
            save_data()  # Save after withdrawal
            
            # Withdrawal success message
            success_text = (
                "🎉 <b>WITHDRAWAL SUCCESSFUL!</b> 🎉\n\n"
                "⭐ <b>Your reward is here:</b>\n"
                f"{reward}\n\n"
                "💎 <b>Remaining Balance:</b> {}\n\n"
                "🔥 <b>Keep earning to get more rewards!</b>"
            ).format(get_balance(uid))
            
            try:
                bot.send_message(uid, success_text, parse_mode="HTML")
            except Exception as e:
                print(f"Failed to send reward to {uid}: {e}")
                
            # Admin notification
            withdraw_msg = (
                "📦 <b>NEW WITHDRAWAL PROCESSED</b>\n\n"
                f"👤 <b>User:</b> @{call.from_user.username}\n"
                f"🆔 <b>ID:</b> {uid}\n"
                f"💎 <b>Diamonds Used:</b> 7\n"
                f"📊 <b>Remaining Stock:</b> {len(stock_list)}\n\n"
                f"🤖 <b>Bot:</b> @{bot.get_me().username}"
            )
            try:
                bot.send_message(CHANNEL_ID_FOR_REF, withdraw_msg, parse_mode="HTML")
            except Exception as e:
                print(f"Failed to notify channel: {e}")
            send_to_admins(withdraw_msg, parse_mode="HTML")
        else:
            #Stock empty message
            empty_text = (
                "❌ <b>STOCK TEMPORARILY UNAVAILABLE</b> ❌\n\n"
                "⭐ We're currently out of stock\n"
                "🔄 Our team is working to restock\n\n"
                "💬 <b>Contact support for assistance:</b>\n"
                
            )
            bot.send_message(uid, empty_text, parse_mode="HTML")
    else:
        #Insufficient balance message
        error_text = (
            "❌ <b>INSUFFICIENT BALANCE</b> ❌\n\n"
            "⚡ Withdrawal failed due to low balance\n"
            f"💎 <b>Your Balance:</b> {bal} diamonds\n"
            "💰 <b>Required:</b> 7 diamonds\n\n"
            "⭐ <b>Earn more diamonds by:</b>\n"
            "• Inviting friends\n"
            "• Claiming daily bonuses\n\n"
            "🔥 <b>Keep earning to unlock rewards!</b>"
        )
        bot.send_message(uid, error_text, parse_mode="HTML")

# ---------------- Flask keep-alive endpoints ----------------
@app.route("/")
def home():
    return "🤖 Telegram bot is running!", 200

@app.route("/ping-test")
def ping_test():
    return "Bot is alive 🚀", 200

# ---------------- Bot runner ----------------
def run_bot_loop():
    while True:
        try:
            print("Starting Instagram Old Age bot polling...")
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=15)
        except Exception as e:
            print(f"Bot crashed, restarting in 5s... Error: {e}")
            traceback.print_exc()
            time.sleep(5)

# ... rest of your code ...

def run_bot_loop():
    while True:
        try:
            print("Starting Instagram Old Age bot polling...")
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=15)
        except Exception as e:
            print(f"Bot crashed, restarting in 5s... Error: {e}")
            traceback.print_exc()
            time.sleep(5)

if __name__ == "__main__":
    print("Starting Instagram Old Age bot in background thread...")
    t = threading.Thread(target=run_bot_loop)
    t.daemon = True
    t.start()
    port = int(os.getenv("PORT", "10000"))
    print(f"Starting Flask server on port {port}")

    app.run(host="0.0.0.0", port=port)


