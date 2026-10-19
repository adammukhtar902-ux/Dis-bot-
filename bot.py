import os
import threading
from flask import Flask
import discord
from discord import app_commands
from discord.ext import commands

# --- إنشاء خادم ويب وهمي لإرضاء Render ---
app = Flask("")


@app.route("/")
def home():
  return "Bot is alive!"


def run_flask():
  # Render يوفر المنفذ عبر PORT تلقائياً
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


# تشغيل خادم الويب في المسار الخلفي (Thread)
threading.Thread(target=run_flask).start()

# --- إعدادات بوت ديسكورد ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
  try:
    synced = await bot.tree.sync()
    print(f"تم تسجيل الدخول بنجاح باسم: {bot.user}")
    print(f"تمت مزامنة {len(synced)} أمر سلاش!")
  except Exception as e:
    print(f"خطأ أثناء المزامنة: {e}")


# أمر سلاش تجريبي /ping
@bot.tree.command(name="ping", description="فحص استجابة البوت")
async def ping(interaction: discord.Interaction):
  await interaction.response.send_message("Pong! 🏓 البوت شغال وسريع جداً!")


# تشغيل البوت باستخدام التوكن
token = os.getenv("TOKEN")
bot.run(token)
