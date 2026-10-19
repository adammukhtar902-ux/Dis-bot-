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


# --- 1. نافذة أسئلة وسيط مضمون (Modal) ---
class MiddlemanModal(discord.ui.Modal, title="أسئلة التذكرة - وسيط مضمون"):
  guarantee = discord.ui.TextInput(
      label="وش ضمانك؟",
      style=discord.TextStyle.short,
      placeholder="اكتب ضمانك هنا...",
      required=True,
  )
  price = discord.ui.TextInput(
      label="وش مقابلك؟",
      style=discord.TextStyle.short,
      placeholder="اكتب المقابل هنا...",
      required=True,
  )
  other_user = discord.ui.TextInput(
      label="يوزر طرف ثاني (منشن أو يوزر)",
      style=discord.TextStyle.short,
      placeholder="اكتب يوزر الطرف الثاني...",
      required=True,
  )
  gift = discord.ui.TextInput(
      label="وش هدية الوسيط (اختياري)",
      style=discord.TextStyle.short,
      placeholder="اختياري...",
      required=False,
  )

  async def on_submit(self, interaction: discord.Interaction):
    await create_ticket_channel(
        interaction,
        "وسيط-مضمون",
        "⚖️",
        [
            ("وش ضمانك", self.guarantee.value),
            ("وش مقابلك", self.price.value),
            ("الطرف الثاني", self.other_user.value),
            ("هدية الوسيط", self.gift.value or "لا يوجد"),
        ],
    )


# --- 2. نافذة أسئلة تطوير المابات (Modal) ---
class DevModal(discord.ui.Modal, title="أسئلة التذكرة - تطوير المابات"):
  details = discord.ui.TextInput(
      label="وش طلبك بالتفصيل؟",
      style=discord.TextStyle.paragraph,
      placeholder="اكتب تفاصيل طلبك للماب (سرقة أو نطة)...",
      required=True,
  )

  async def on_submit(self, interaction: discord.Interaction):
    await create_ticket_channel(
        interaction,
        "تطوير-مابات",
        "📊",
        [("طلب التطوير بالتفصيل", self.details.value)],
    )


# --- 3. نافذة أسئلة الدعم الفني (Modal) ---
class SupportModal(discord.ui.Modal, title="أسئلة التذكرة - التواصل مع الدعم"):
  problem = discord.ui.TextInput(
      label="ما هي مشكلتك؟",
      style=discord.TextStyle.paragraph,
      placeholder="اشرح مشكلتك أو استفسارك هنا...",
      required=True,
  )

  async def on_submit(self, interaction: discord.Interaction):
    await create_ticket_channel(
        interaction, "دعم-فني", "🎧", [("تفاصيل المشكلة", self.problem.value)]
    )


# --- دالة موحدة لإنشاء روم التكت وإرسال التفاصيل ---
async def create_ticket_channel(
    interaction: discord.Interaction, ticket_name: str, emoji: str, answers: list
):
  guild = interaction.guild
  overwrites = {
      guild.default_role: discord.PermissionOverwrite(view_channel=False),
      interaction.user: discord.PermissionOverwrite(
          view_channel=True, send_messages=True, read_message_history=True
      ),
      guild.me: discord.PermissionOverwrite(
          view_channel=True, send_messages=True
      ),
  }

  category = interaction.channel.category
  ticket_channel = await guild.create_text_channel(
      name=f"{ticket_name}-{interaction.user.name}",
      category=category,
      overwrites=overwrites,
  )

  # ترتيب إجابات العضو داخل التكت
  fields_text = ""
  for label, val in answers:
    fields_text += f"**{label}:** {val}\n"

  close_view = CloseTicketView()
  embed = discord.Embed(
      title=f"{emoji} تكت {ticket_name}",
      description=(
          f"مرحباً بك {interaction.user.mention}!\nتم فتح التكت بنجاح بناءً"
          f" على بياناتك:\n\n{fields_text}"
      ),
      color=discord.Color.from_rgb(138, 43, 226),
  )

  await ticket_channel.send(embed=embed, view=close_view)
  await interaction.response.send_message(
      f"تم إنشاء تذكرتك بنجاح: {ticket_channel.mention}", ephemeral=True
  )


# --- زر إغلاق التكت ---
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


# --- القائمة المنسدلة (Select Menu) لاختيار نوع التذكرة ---
class TicketSelect(discord.ui.Select):

  def __init__(self):
    options = [
        discord.SelectOption(
            label="وسيط مضمون",
            description="لضمان عملية التداول بوجود وسيط",
            emoji="⚖️",
            value="middleman",
        ),
        discord.SelectOption(
            label="تطوير المابات",
            description="لطلب خدمة تطوير ماب سرقه او ماب النطة",
            emoji="📊",
            value="dev",
        ),
        discord.SelectOption(
            label="التواصل مع الدعم الفني",
            description="لأى مشكله أو استفسار",
            emoji="🎧",
            value="support",
        ),
    ]
    super().__init__(
        placeholder="اختر نوع التذكرة",
        min_values=1,
        max_values=1,
        options=options,
        custom_id="ticket_select_menu",
    )

  async def callback(self, interaction: discord.Interaction):
    if self.values[0] == "middleman":
      await interaction.response.send_modal(MiddlemanModal())
    elif self.values[0] == "dev":
      await interaction.response.send_modal(DevModal())
    elif self.values[0] == "support":
      await interaction.response.send_modal(SupportModal())


class TicketSelectView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)
    self.add_item(TicketSelect())


# --- أمر إرسال اللوحة الرئيسية (/ticket) ---
@bot.tree.command(
    name="ticket", description="إرسال لوحة التكتات المتقدمة للسيرفر"
)
@app_commands.checks.has_permissions(administrator=True)
async def ticket_panel(interaction: discord.Interaction):
  embed = discord.Embed(
      title="نحن هنا لخدمتك",
      description=(
          "إذا كان لديك أي سؤال أو استفسار، كل ما عليك هو فتح تذكرة،\nوسيتواصل"
          " معك فريق الدعم مباشرة بكل اهتمام وسرعة.\nنضمن لك تجربة دعم سهلة،"
          " واضحة، وسريعة."
      ),
      color=discord.Color.from_rgb(138, 43, 226),
  )
  view = TicketSelectView()
  await interaction.channel.send(embed=embed, view=view)
  await interaction.response.send_message(
      "تم إرسال لوحة التكتات بنجاح! ✅", ephemeral=True
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
