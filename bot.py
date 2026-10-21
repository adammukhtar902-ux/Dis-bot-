import asyncio
import os
from flask import Flask
from threading import Thread
import discord
from discord import TextStyle
from discord.ext import commands
from discord.ui import Modal, Select, TextInput, View

# ---------------------------------------------------------
# 1. إعداد سيرفر Flask لضمان تشغيل 24/7 مع UptimeRobot
# ---------------------------------------------------------
app = Flask("")


@app.route("/")
def home():
  return "Bot is active 24/7!"


def run_flask():
  app.run(host="0.0.0.0", port=10000)


def keep_alive():
  t = Thread(target=run_flask)
  t.start()


# ---------------------------------------------------------
# 2. إعدادات البوت والبادئة (Prefix)
# ---------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# البوت يستجيب للعلامات المباشرة والأوامر النصية العادية
bot = commands.Bot(command_prefix=["!", "bot ", ""], intents=intents)

# متغيّرات قابلة للتعديل ديناميكياً بدون مساس الكود
PANEL_CONFIG = {
    "title": "نحن هنا لخدمتك",
    "description": "يرجى اختيار نوع طلبك من القائمة أدناه، ثم أجب على الأسئلة المطلوبة وسيتم إنشاء التذكرة تلقائياً.",
    "color": 0x6A0DAD,
}


# ---------------------------------------------------------
# 3. واجهات التكت والأسئلة (Select & Modals)
# ---------------------------------------------------------
class TicketQuestionsModal(Modal, title="أسئلة التذكرة"):

  def __init__(self, service_type, map_name, color_name):
    super().__init__()
    self.service_type = service_type
    self.map_name = map_name
    self.color_name = color_name

  daman = TextInput(
      label="وش ضمانك؟",
      style=TextStyle.paragraph,
      placeholder="اكتب ضمانك هنا...",
      required=True,
  )
  mokaabel = TextInput(
      label="وش مقابلتك؟",
      style=TextStyle.paragraph,
      placeholder="اكتب مقابلتك هنا...",
      required=True,
  )
  ingame_name = TextInput(
      label="اسمك باللعبة؟",
      style=TextStyle.short,
      placeholder="اكتب اسمك الحقيقي باللعبة...",
      required=True,
  )

  async def on_submit(self, interaction: discord.Interaction):
    guild = interaction.guild
    user = interaction.user

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(
            read_messages=True, send_messages=True
        ),
        guild.me: discord.PermissionOverwrite(
            read_messages=True, send_messages=True
        ),
    }

    ticket_channel = await guild.create_text_channel(
        name=f"تكت-{user.name}", overwrites=overwrites
    )

    embed = discord.Embed(
        title="🎟️ تفاصيل طلب التذكرة", color=discord.Color.purple()
    )
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    embed.add_field(name="النوع", value=self.service_type, inline=True)
    embed.add_field(name="الماب", value=self.map_name, inline=True)
    embed.add_field(name="اللون المطلوب", value=self.color_name, inline=True)
    embed.add_field(name="الضمان", value=self.daman.value, inline=False)
    embed.add_field(name="المقابل", value=self.mokaabel.value, inline=False)
    embed.add_field(
        name="الاسم باللعبة", value=self.ingame_name.value, inline=False
    )

    await ticket_channel.send(
        content=f"مرحباً {user.mention}، تم فتح التكت بنجاح!", embed=embed
    )
    await interaction.response.send_message(
        f"✅ تم فتح التكت بنجاح في {ticket_channel.mention}", ephemeral=True
    )


class ColorSelect(Select):

  def __init__(self, service_type, map_name):
    self.service_type = service_type
    self.map_name = map_name
    options = [
        discord.SelectOption(label="لون أكوا", value="لون أكوا"),
        discord.SelectOption(label="لون الكريستال", value="لون الكريستال"),
        discord.SelectOption(label="لون قولد", value="لون قولد"),
        discord.SelectOption(label="لون لافا", value="لون لافا"),
        discord.SelectOption(label="لون بلاك وايت", value="لون بلاك وايت"),
        discord.SelectOption(label="لون كاندي", value="لون كاندي"),
        discord.SelectOption(label="لون سايبر", value="لون سايبر"),
        discord.SelectOption(label="لون جلكسي", value="لون جلكسي"),
    ]
    super().__init__(placeholder="اختر اللون المطلوب...", options=options)

  async def callback(self, interaction: discord.Interaction):
    modal = TicketQuestionsModal(
        self.service_type, self.map_name, self.values[0]
    )
    await interaction.response.send_modal(modal)


class ColorView(View):

  def __init__(self, service_type, map_name):
    super().__init__()
    self.add_item(ColorSelect(service_type, map_name))


class MapSelect(Select):

  def __init__(self, service_type):
    self.service_type = service_type
    options = [
        discord.SelectOption(
            label="ماب السرقة",
            value="ماب السرقة",
            description="طلب ألوان ماب السرقة",
        ),
        discord.SelectOption(
            label="ماب النطة",
            value="ماب النطة",
            description="طلب ألوان ماب النطة",
        ),
    ]
    super().__init__(placeholder="اختر ماب الألوان...", options=options)

  async def callback(self, interaction: discord.Interaction):
    view = ColorView(self.service_type, self.values[0])
    await interaction.response.send_message(
        "يرجى اختيار اللون المراد فكه:", view=view, ephemeral=True
    )


class MapView(View):

  def __init__(self, service_type):
    super().__init__()
    self.add_item(MapSelect(service_type))


class TicketTypeSelect(Select):

  def __init__(self):
    options = [
        discord.SelectOption(
            label="وسيط مضمون",
            value="وسيط مضمون",
            description="لضمان عملية التداول بوجود وسيط",
            emoji="⚖️",
        ),
        discord.SelectOption(
            label="تطوير المابات",
            value="تطوير المابات",
            description="لطلب خدمة تطوير ماب سرقه او ماب نط",
            emoji="📊",
        ),
        discord.SelectOption(
            label="الالوان بيوت",
            value="الالوان بيوت",
            description="لطلب خدمة اللوان البيوت (ماب النطة)، او (ماب السرقة)",
            emoji="🏠",
        ),
        discord.SelectOption(
            label="التواصل مع الدعم الفني",
            value="الدعم الفني",
            description="لأي مشكله او استفسار ، افتح تذكرة هنا ويصلك الدعم",
            emoji="🎧",
        ),
    ]
    super().__init__(placeholder="اختر نوع التذكرة...", options=options)

  async def callback(self, interaction: discord.Interaction):
    if self.values[0] == "الالوان بيوت":
      view = MapView(self.values[0])
      await interaction.response.send_message(
          "يرجى تحديد ماب الألوان:", view=view, ephemeral=True
      )
    else:
      modal = TicketQuestionsModal(self.values[0], "غير محدد", "غير محدد")
      await interaction.response.send_modal(modal)


class MainTicketView(View):

  def __init__(self):
    super().__init__(timeout=None)
    self.add_item(TicketTypeSelect())


# ---------------------------------------------------------
# 4. أوامر التحكم بالتكتات (إضافة عضو، قفل، تغيير اسم)
# ---------------------------------------------------------
@bot.command(name="ضيف", aliases=["add"])
async def add_member(ctx, member: discord.Member):
  """إضافة عضو للتكت بكلمة: ضيف @user"""
  await ctx.channel.set_permissions(
      member, read_messages=True, send_messages=True
  )
  await ctx.send(f"✅ تم إضافة {member.mention} إلى التكت بنجاح.")


@bot.command(name="احذف_عضو", aliases=["remove"])
async def remove_member(ctx, member: discord.Member):
  """إزالة عضو من التكت"""
  await ctx.channel.set_permissions(member, overwrite=None)
  await ctx.send(f"🚫 تم إزالة {member.mention} من التكت.")


@bot.command(name="اعادة_تسمية", aliases=["rename"])
async def rename_ticket(ctx, *, new_name: str):
  """تغيير اسم التكت: rename new-name"""
  await ctx.channel.edit(name=new_name)
  await ctx.send(f"✏️ تم تغيير اسم التكت إلى: `{new_name}`")


@bot.command(name="حذف_التكت", aliases=["delete", "close", "قفل"])
async def delete_ticket(ctx):
  """حذف التكت فوراً"""
  await ctx.send("🛑 سيتم حذف التكت خلال 3 ثوانٍ...")
  await asyncio.sleep(3)
  await ctx.channel.delete()


# ---------------------------------------------------------
# 5. الأوامر الإدارية والسجن والحماية
# ---------------------------------------------------------
user_warnings = {}


@bot.command(name="تحذير", aliases=["warn"])
@commands.has_permissions(manage_messages=True)
async def warn_user(ctx, member: discord.Member, *, reason: str = "غير محدد"):
  if member.id not in user_warnings:
    user_warnings[member.id] = []
  user_warnings[member.id].append(reason)
  await ctx.send(
      f"⚠️ تم تحذير {member.mention}. السبب: {reason} (إجمالي التحذيرات:"
      f" {len(user_warnings[member.id])})"
  )


@bot.command(name="تحذيرات", aliases=["warnings"])
async def get_warnings(ctx, member: discord.Member):
  warns = user_warnings.get(member.id, [])
  await ctx.send(f"📋 عدد تحذيرات {member.mention} هو: {len(warns)}")


@bot.command(name="سجن", aliases=["prison"])
@commands.has_permissions(manage_roles=True)
async def prison_user(ctx, member: discord.Member):
  prison_role = discord.utils.get(ctx.guild.roles, name="Prison")
  if not prison_role:
    prison_role = await ctx.guild.create_role(
        name="Prison", color=discord.Color.dark_gray()
    )
    for channel in ctx.guild.channels:
      await channel.set_permissions(prison_role, send_messages=False)

  await member.add_roles(prison_role)
  await ctx.send(f"🔒 تم سجن {member.mention} بنجاح!")


@bot.command(name="طرد", aliases=["kick"])
@commands.has_permissions(kick_members=True)
async def kick_user(ctx, member: discord.Member, *, reason=None):
  await member.kick(reason=reason)
  await ctx.send(f"👞 تم طرد {member.mention} من السيرفر.")


@bot.command(name="حظر", aliases=["ban"])
@commands.has_permissions(ban_members=True)
async def ban_user(ctx, member: discord.Member, *, reason=None):
  await member.ban(reason=reason)
  await ctx.send(f"🔨 تم حظر {member.mention} بنجاح.")


@bot.command(name="قفل", aliases=["lock"])
@commands.has_permissions(manage_channels=True)
async def lock_channel(ctx):
  await ctx.channel.set_permissions(
      ctx.guild.default_role, send_messages=False
  )
  await ctx.send("🔒 تم قفل الروم بنجاح.")


@bot.command(name="فتح", aliases=["unlock"])
@commands.has_permissions(manage_channels=True)
async def unlock_channel(ctx):
  await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
  await ctx.send("🔓 تم فتح الروم بنجاح.")


@bot.command(name="الوان", aliases=["colors"])
async def show_colors(ctx):
  embed = discord.Embed(
      title="🎨 قائمة ألوان السيرفر المتاحة", color=discord.Color.blue()
  )
  embed.description = "يمكنك الحصول على اللون عبر التكت بطلب ألوان البيوت."
  await ctx.send(embed=embed)


# ---------------------------------------------------------
# 6. أوامر إعداد بنل التكتات ديناميكياً
# ---------------------------------------------------------
@bot.command(name="تعديل_العنوان")
@commands.has_permissions(administrator=True)
async def set_panel_title(ctx, *, new_title: str):
  PANEL_CONFIG["title"] = new_title
  await ctx.send(f"✅ تم تعديل عنوان بنل التكتات إلى: **{new_title}**")


@bot.command(name="تعديل_الوصف")
@commands.has_permissions(administrator=True)
async def set_panel_desc(ctx, *, new_desc: str):
  PANEL_CONFIG["description"] = new_desc
  await ctx.send(f"✅ تم تعديل وصف بنل التكتات إلى: **{new_desc}**")


@bot.command(name="انشاء_بنل", aliases=["setup_tickets"])
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
  embed = discord.Embed(
      title=PANEL_CONFIG["title"],
      description=PANEL_CONFIG["description"],
      color=PANEL_CONFIG["color"],
  )
  await ctx.send(embed=embed, view=MainTicketView())


# ---------------------------------------------------------
# 7. تشغيل البوت
# ---------------------------------------------------------
@bot.event
async def on_ready():
  print(f"Logged in as {bot.user.name} - Ready & Online!")


keep_alive()
TOKEN = os.environ.get("TOKEN")
bot.run(TOKEN)
