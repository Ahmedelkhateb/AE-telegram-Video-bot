# 🤖 AE Telegram Video Downloader Bot

AE Telegram Bot is a powerful and fully automated video downloader that allows users to download videos or audio from various websites **directly through Telegram** — clean, fast, and user-friendly.

---

## 🚀 Features

- 🔗 Accepts video links from multiple websites (YouTube, Facebook, Twitter, TikToke, etc.)
- 🎧 Converts to high-quality MP3 audio
- 🎥 Downloads full videos (MP4 format)
- 📦 Direct download link for large files
- 📊 Personal and admin statistics tracking
- 🔐 User ban / unban functionality
- 💾 File auto-cleanup every 24 hours
- 🌍 Fully hosted on Flask with background threading
- 🔒 Token stored securely in `.env` file

---

## 📦 Requirements

To run the bot, install the following dependencies:

```bash
pip install -r requirements.txt
Python 3.9+ is recommended.

🛠️ Project Structure
bash
نسخ
تحرير
├── bot.py              # Main Telegram bot logic
├── requirements.txt    # Python dependencies
├── .env                # Token and secret configs (not uploaded)
├── users.json          # Tracks usernames
├── user_stats.json     # User download stats
├── banned_users.json   # Banned users list
├── downloads/          # Temporary download directory
🔧 Setup Instructions
Clone the repo:

bash
نسخ
تحرير
git clone https://github.com/Ahmedelkhateb/AE-telegram-Video-bot.git
cd AE-telegram-Video-bot
Install requirements:

bash
نسخ
تحرير
pip install -r requirements.txt
Create a .env file in the same directory and add your Telegram Bot Token:

ini
نسخ
تحرير
BOT_TOKEN=your_token_here
Run the bot:

bash
نسخ
تحرير
python bot.py

🧠 Bot Commands
For all users:
/start – Welcome message

/help – Show usage instructions

/stats – Show user stats

For admin (ID: Your Admin ID):
/admin_stats – All users' stats

/ban <id> – Ban a user

/unban <id> – Unban a user

/banned – List all banned users

/find <name or id> – Search user

🔒 Security Note
This bot uses a .env file to store your sensitive BOT_TOKEN.
Make sure you do not upload this file to GitHub.

If you accidentally uploaded it:

Immediately regenerate the token from @BotFather

Use BFG Repo Cleaner or git filter-branch to remove it from history.

📣 Promotion Integration
When a download completes, the bot sends a custom promotional message related to your store or product.

You can update this section in the bot.send_message(...) part of the bot.py.

📬 Contact
Created by Ahmed Elkhateb

📜 الترخيص
هذا المشروع مجاني للاستخدام غير التجاري. يرجى عدم إزالة اسم المطور.

🌟 Star the repo if you find it useful!