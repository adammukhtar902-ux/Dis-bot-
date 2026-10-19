import os
import threading
from flask import Flask
import discord
from discord import app_commands
from discord.ext import commands

# --- خادم الويب لإبقاء البوت شغال 24/7 ---
app = Flask("")


@app.route("/")
def home():
  return "Bot is active!"


def run_flask():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


threading.Thread(target=run_flask).start()

# --- إعدادات البوت ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
  try:
    synced = await bot.tree.sync()
    print(f"تم تسجيل الدخول باسم: {bot.user}")
    print(f"تمت مزامنة {len(synced)} أمر بنجاح!")
  except Exception as e:
    print(f"خطأ أثناء المزامنة: {e}")


# --- نظام التكت (Tickets View & Button) ---
class TicketButton(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(
      label="فتح تكت 🎫",
      style=discord.ButtonStyle.green,
      custom_id="open_ticket_button",
  )
  async def open_ticket(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    guild = interaction.guild
    # البحث عن رتبة الأدمين أو صلاحية الإدارة، أو السماح للشخص نفسه والمشرفين
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True
        ),
    }

    # إنشاء روم جديد للتكت
    category = interaction.channel.category
    ticket_channel = await guild.create_text_channel(
        name=f"ticket-{interaction.user.name}",
        category=category,
        overwrites=overwrites,
    )

    # إرسال رسالة ترحيب داخل التكت مع زر الإغلاق
    close_view = CloseTicketView()
    await ticket_channel.send(
        f"مرحباً بك {interaction.user.mention}! هذا هو تكت الخاص بك.\nيرجى كتابة مشكلتك أو طلبك هنا وسيتم الرد عليك قريباً.",
        view=close_view,
    )
    await interaction.response.send_message(
        f"تم إنشاء التكت الخاص بك بنجاح: {ticket_channel.mention}", ephemeral=True
    )


class CloseTicketView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(
      label="إغلاق التكت 🔒",
      style=discord.ButtonStyle.red,
      custom_id="close_ticket_button",
  )
  async def close_ticket(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    await interaction.response.send_message("جاري إغلاق وحذف التكت... ⏱️")
    await interaction.channel.delete()


# أمر إنشاء رسالة التكت (/ticket)
@bot.tree.command(name="ticket", description="إرسال لوحة إنشاء التكتات للسيرفر")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_panel(interaction: discord.Interaction):
  embed = discord.Embed(
      title="🎫 نظام التذاكر (Support Tickets)",
      description=(
          "هل لديك استفسار أو مشكلة؟\nاضغط على الزر أدناه لفتح تكت خاص بك وسيقوم"
          " فريق العمل بمساعدتك في أقرب وقت!"
      ),
      color=discord.Color.gold(),
  )
  view = TicketButton()
  await interaction.channel.send(embed=embed, view=view)
  await interaction.response.send_message(
      "تم إرسال لوحة التكتات بنجاح في هذه الروم! ✅", ephemeral=True
  )


# --- أمر Ping السريع للتأكد ---
@bot.tree.command(name="ping", description="فحص سرعة استجابة البوت")
async def ping(interaction: discord.Interaction):
  latency = round(bot.latency * 1000)
  await interaction.response.send_message(
      f"Pong! 🏓 سرعة الاستجابة: {latency}ms"
  )


token = os.getenv("TOKEN")
bot.run(token)
