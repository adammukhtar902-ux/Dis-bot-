import asyncio
import os
from flask import Flask
from threading import Thread
import discord
from discord import TextStyle
from discord.ext import commands
from discord.ui import Modal, Select, TextInput, View

# ---------------------------------------------------------
# 1. إعداد سيرفر Flask لضمان التشغيل 24/7 مع UptimeRobot
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
# 2. إعدادات البوت ودعم أوامر السلاش
# ---------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=["!"], intents=intents)

PANEL_CONFIG = {
    "title": "نحن هنا لخدمتك",
    "description": (
        "يرجى اختيار نوع طلبك من القائمة أدناه، ثم أجب على الأسئلة المطلوبة"
        " وسيتم إنشاء التذكرة تلقائياً."
    ),
    "color": 0x6A0DAD,
}


# ---------------------------------------------------------
# 3. أزرار التحكم داخل التكت (قفل، استلام)
# ---------------------------------------------------------
class TicketControlView(View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(
      label="استلام التكت", style=discord.ButtonStyle.green, custom_id="claim_ticket"
  )
  async def claim_ticket(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    await interaction.response.send_message(
        f"✋ تم استلام التكت بواسطة {interaction.user.mention}", ephemeral=False
    )

  @discord.ui.button(
      label="قفل التكت", style=discord.ButtonStyle.red, custom_id="close_ticket"
  )
  async def close_ticket(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    if not interaction.user.guild_permissions.manage_channels:
      await interaction.response.send_message(
          "❌ عذراً، الإدارة فقط هي من تستطيع إغلاق التكت!", ephemeral=True
      )
      return
    await interaction.response.send_message("🛑 جاري إغلاق التكت وحذفه...")
    await asyncio.sleep(3)
    await interaction.channel.delete()


# ---------------------------------------------------------
# 4. نافذة الأسئلة والاستمارة (Modal) - مع صلاحية إرسال الصور
# ---------------------------------------------------------
class TicketQuestionsModal(Modal, title="أسئلة التذكرة"):

  def __init__(self, service_type):
    super().__init__()
    self.service_type = service_type

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

    # شرط عدم فتح أكثر من تكت بنفس الوقت
    clean_user_name = user.name.lower().replace(" ", "-")
    existing_channel = discord.utils.get(
        guild.text_channels, name=f"تكت-{clean_user_name}"
    )
    if existing_channel:
      await interaction.response.send_message(
          f"❌ لديك تكت مفتوح بالفعل في {existing_channel.mention}!",
          ephemeral=True,
      )
      return

    # إعطاء صلاحيات القراءة، الكتابة، إرسال الصور، وإرفاق الروابط للعضو
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
            attach_files=True,  # إمكانية إرسال الصور والملفات
            embed_links=True,  # إمكانية إرسال الروابط
        ),
        guild.me: discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
            attach_files=True,
            embed_links=True,
        ),
    }

    ticket_channel = await guild.create_text_channel(
        name=f"تكت-{clean_user_name}", overwrites=overwrites
    )

    embed = discord.Embed(
        title="🎟️ تفاصيل طلب التذكرة", color=discord.Color.purple()
    )
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    embed.add_field(name="النوع", value=self.service_type, inline=True)
    embed.add_field(name="الضمان", value=self.daman.value, inline=False)
    embed.add_field(name="المقابل", value=self.mokaabel.value, inline=False)
    embed.add_field(
        name="الاسم باللعبة", value=self.ingame_name.value, inline=False
    )

    await ticket_channel.send(
        content=f"مرحباً {user.mention}، تم فتح التكت بنجاح!",
        embed=embed,
        view=TicketControlView(),
    )
    await interaction.response.send_message(
        f"✅ تم فتح التكت بنجاح في {ticket_channel.mention}", ephemeral=True
    )


# ---------------------------------------------------------
# 5. قائمة اختيار الخدمات الرئيسية
# ---------------------------------------------------------
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
            description="لطلب خدمة تطوير مابات",
            emoji="📊",
        ),
        discord.SelectOption(
            label="تكت الهلاوين",
            value="تكت الهلاوين",
            description="لطلب خدمات وفعاليات الهلاوين",
            emoji="🎃",
        ),
        discord.SelectOption(
            label="التواصل مع الدعم الفني",
            value="الدعم الفني",
            description="لأي مشكلة أو استفسار",
            emoji="🎧",
        ),
    ]
    super().__init__(placeholder="اختر نوع التذكرة...", options=options)

  async def callback(self, interaction: discord.Interaction):
    clean_user_name = interaction.user.name.lower().replace(" ", "-")
    existing_channel = discord.utils.get(
        interaction.guild.text_channels, name=f"تكت-{clean_user_name}"
    )
    if existing_channel:
      await interaction.response.send_message(
          f"❌ لديك تكت مفتوح بالفعل في {existing_channel.mention}!",
          ephemeral=True,
      )
      return

    modal = TicketQuestionsModal(self.values[0])
    await interaction.response.send_modal(modal)


class MainTicketView(View):

  def __init__(self):
    super().__init__(timeout=None)
    self.add_item(TicketTypeSelect())


# ---------------------------------------------------------
# 6. أوامر السلاش (Slash Commands)
# ---------------------------------------------------------
@bot.tree.command(name="add", description="إضافة عضو إلى التكت الحالي")
@discord.app_commands.describe(member="العضو المراد إضافته")
async def slash_add(interaction: discord.Interaction, member: discord.Member):
  await interaction.channel.set_permissions(
      member,
      read_messages=True,
      send_messages=True,
      attach_files=True,
      embed_links=True,
  )
  await interaction.response.send_message(
      f"✅ تم إضافة {member.mention} إلى التكت وبإمكانه إرسال الصور والرسائل."
  )


@bot.tree.command(name="remove", description="إزالة عضو من التكت الحالي")
@discord.app_commands.describe(member="العضو المراد إزالته")
async def slash_remove(
    interaction: discord.Interaction, member: discord.Member
):
  await interaction.channel.set_permissions(member, overwrite=None)
  await interaction.response.send_message(
      f"🚫 تم إزالة {member.mention} من التكت."
  )


@bot.tree.command(name="rename", description="إعادة تسمية التكت الحالي")
@discord.app_commands.describe(new_name="اسم التكت الجديد")
async def slash_rename(interaction: discord.Interaction, new_name: str):
  await interaction.channel.edit(name=new_name)
  await interaction.response.send_message(
      f"✏️ تم تغيير اسم التكت إلى: `{new_name}`"
  )


@bot.tree.command(name="close", description="إغلاق وحذف التكت الحالي")
async def slash_close(interaction: discord.Interaction):
  if not interaction.user.guild_permissions.manage_channels:
    await interaction.response.send_message(
        "❌ عذراً، الإدارة فقط هي من تستطيع إغلاق التكت!", ephemeral=True
    )
    return
  await interaction.response.send_message(
      "🛑 سيتم حذف التكت خلال 3 ثوانٍ..."
  )
  await asyncio.sleep(3)
  await interaction.channel.delete()


@bot.tree.command(name="lock", description="قفل الروم الحالي")
async def slash_lock(interaction: discord.Interaction):
  if not interaction.user.guild_permissions.manage_channels:
    return
  await interaction.channel.set_permissions(
      interaction.guild.default_role, send_messages=False
  )
  await interaction.response.send_message("🔒 تم قفل الروم بنجاح.")


@bot.tree.command(name="unlock", description="فتح الروم الحالي")
async def slash_unlock(interaction: discord.Interaction):
  if not interaction.user.guild_permissions.manage_channels:
    return
  await interaction.channel.set_permissions(
      interaction.guild.default_role, send_messages=True
  )
  await interaction.response.send_message("🔓 تم فتح الروم بنجاح.")


@bot.tree.command(name="warn", description="تحذير عضو في السيرفر")
@discord.app_commands.describe(member="العضو", reason="السبب")
async def slash_warn(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "غير محدد",
):
  if not interaction.user.guild_permissions.manage_messages:
    await interaction.response.send_message(
        "❌ لا تمتلك الصلاحية لاستخدام هذا الأمر.", ephemeral=True
    )
    return
  await interaction.response.send_message(
      f"⚠️ تم تحذير {member.mention} بسبب: {reason}"
  )


@bot.tree.command(name="prison", description="سجن عضو في السيرفر")
@discord.app_commands.describe(member="العضو المراد سجنه")
async def slash_prison(interaction: discord.Interaction, member: discord.Member):
  if not interaction.user.guild_permissions.manage_roles:
    await interaction.response.send_message(
        "❌ لا تمتلك صلاحية إدارة الرتب.", ephemeral=True
    )
    return
  prison_role = discord.utils.get(interaction.guild.roles, name="Prison")
  if not prison_role:
    prison_role = await interaction.guild.create_role(
        name="Prison", color=discord.Color.dark_gray()
    )
    for channel in interaction.guild.channels:
      await channel.set_permissions(prison_role, send_messages=False)
  await member.add_roles(prison_role)
  await interaction.response.send_message(f"🔒 تم سجن {member.mention} بنجاح!")


# ---------------------------------------------------------
# 7. أوامر إعداد البنل وإنشاء البوت
# ---------------------------------------------------------
@bot.command(name="انشاء_بنل")
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
  embed = discord.Embed(
      title=PANEL_CONFIG["title"],
      description=PANEL_CONFIG["description"],
      color=PANEL_CONFIG["color"],
  )
  await ctx.send(embed=embed, view=MainTicketView())


@bot.event
async def on_ready():
  try:
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} slash commands successfully.")
  except Exception as e:
    print(e)
  print(f"Logged in as {bot.user.name} - Ready & Online!")


keep_alive()
TOKEN = os.environ.get("TOKEN")
bot.run(TOKEN)
