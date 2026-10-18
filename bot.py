import os
import discord
from discord.ext import commands

# إعداد الصلاحيات (Intents)
intents = discord.Intents.default()
intents.message_content = True  # السماح بقراءة محتوى الرسائل

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'تم تسجيل الدخول بنجاح باسم: {bot.user.name}')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong! 🏓')

# التوكن الخاص بك
TOKEN = os.getenv("TOKEN")


if __name__ == "__main__":
    bot.run(TOKEN)
