import os
import asyncio
import random
import threading
from flask import Flask
import discord
from discord import app_commands
from discord.ext import commands

# --- خادم الويب لإبقاء البوت شغال 24/7 على Render ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is active 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

# ==========================================
# --- ⚙️ إعدادات الأيديات والروابط ---
# ==========================================

VOUCHES_CHANNEL_ID = 123456789012345678  # <--- غير هذا برقم آي دي روم VOUCHES عندك

CONFIG = {
    "middleman": {
        "category_id": 1555679947467784212,
        "role_id": 1555673464470376479,
        "name": "وسيط-مضمون"
    },
    "support": {
        "category_id": 1556375191980998698,
        "role_id": 1555335120582344784,
        "name": "دعم-فني"
    },
    "dev": {
        "category_id": 1556375365314945024,
        "role_id": 1561565278045736970,
        "name": "تطوير-مابات"
    }
}

PURPLE_COLOR = discord.Color.from_rgb(138, 43, 226)
BANNER_URL = "https://i.ibb.co/6P2T2gM/asc-banner.png" 

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول بنجاح باسم: {bot.user}")

# --- أمر خاص لمزامنة أوامر السلاش يدوياً بالشرطة النقطية (!sync) ---
@bot.command()
async def sync(ctx):
    if ctx.author.guild_permissions.administrator:
        synced = await bot.tree.sync()
        await ctx.send(f"تمت مزامنة {len(synced)} أمر بنجاح! ✅")

# --- نظام ردود الأرقام (1, 2, 3) ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.strip()
    channel_name = message.channel.name
    vouche_tag = f"<#{VOUCHES_CHANNEL_ID}>" if VOUCHES_CHANNEL_ID else "#VOUCHES⭐"

    # 1. اختصار الوسيط
    if content == "1" and "وسيط-مضمون" in channel_name:
        user_roles = [r.id for r in message.author.roles]
        if CONFIG["middleman"]["role_id"] in user_roles or message.author.guild_permissions.administrator:
            try:
                await message.delete()
            except:
                pass

            embed = discord.Embed(
                description=(
                    f"كان معكم الوسيط: {message.author.mention} 🤝\n\n"
                    f"شكراً لتعاملكم معنا! نرجو منكم كتابة تقييمكم للخدمة في روم التقييمات:\n"
                    f"{vouche_tag}\n\n"
                    "نتمنى لكم يوماً سعيداً! ❤️"
                ),
                color=PURPLE_COLOR
            )
            await message.channel.send(embed=embed)

    # 2. اختصار الدعم الفني
    elif content == "2" and "دعم-فني" in channel_name:
        user_roles = [r.id for r in message.author.roles]
        if CONFIG["support"]["role_id"] in user_roles or message.author.guild_permissions.administrator:
            try:
                await message.delete()
            except:
                pass

            embed = discord.Embed(
                description=f"كان معك {message.author.mention} من فريق الدعم الفني، لا تنسى التقيييم في روم {vouche_tag}\n❤️",
                color=PURPLE_COLOR
            )
            await message.channel.send(embed=embed)

    # 3. اختصار فريق التطوير
    elif content == "3" and "تطوير-مابات" in channel_name:
        user_roles = [r.id for r in message.author.roles]
        if CONFIG["dev"]["role_id"] in user_roles or message.author.guild_permissions.administrator:
            try:
                await message.delete()
            except:
                pass

            embed = discord.Embed(
                description=f"كان معك {message.author.mention}\nمن فريق التطوير\nلاتنسى التقييم في روم\n{vouche_tag}",
                color=PURPLE_COLOR
            )
            await message.channel.send(embed=embed)

    await bot.process_commands(message)

# --- أزرار التحكم داخل التكت ---
class TicketControlView(discord.ui.View):
    def __init__(self, staff_role_id: int):
        super().__init__(timeout=None)
        self.staff_role_id = staff_role_id
        self.is_claimed = False

    @discord.ui.button(label="قفل", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("جاري إغلاق وحذف التكت... ⏱️")
        await interaction.channel.delete()

    @discord.ui.button(label="استلام", style=discord.ButtonStyle.green, emoji="📌", custom_id="claim_ticket_btn")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_roles = [r.id for r in interaction.user.roles]
        if self.staff_role_id not in user_roles and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ عفواً، هذا الزر مخصص للطاقم المخصص فقط!", ephemeral=True)
            return

        if self.is_claimed:
            await interaction.response.send_message("⚠️ هذه التذكرة مستلمة بالفعل!", ephemeral=True)
            return

        self.is_claimed = True
        button.disabled = True
        button.label = "تم الاستلام"
        button.style = discord.ButtonStyle.secondary
        await interaction.message.edit(view=self)

        claim_embed = discord.Embed(
            description=f"تم استلام التذكره بواسطة {interaction.user.mention}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=claim_embed)

# --- المدخلات والنوافذ ---
class MiddlemanModal(discord.ui.Modal, title="أسئلة التذكرة - وسيط مضمون"):
    take = discord.ui.TextInput(label="وش بتاخذ؟", style=discord.TextStyle.paragraph, placeholder="اكتب وش بتاخذ بالتفصيل...", required=True)
    give = discord.ui.TextInput(label="وش بتعطي؟", style=discord.TextStyle.paragraph, placeholder="اكتب وش بتعطي...", required=True)
    other_user = discord.ui.TextInput(label="يوزر الطرف الثاني بالديسكورد", style=discord.TextStyle.short, placeholder="اكتب يوزر الطرف الثاني...", required=True)
    gift = discord.ui.TextInput(label="التيب او الهديه/غير إلزامي", style=discord.TextStyle.short, placeholder="اختياري...", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(
            interaction, 
            ticket_type="middleman", 
            answers=[
                ("وش بتاخذ؟", self.take.value),
                ("وش بتعطي؟", self.give.value),
                ("يوزر الطرف الثاني بالديسكورد", self.other_user.value),
                ("التيب او الهديه/غير إلزامي", self.gift.value or "لا يوجد")
            ],
            welcome_msg="اهلاً بك في تكت طلب وسيط في سيرفر Asc\nلقد تم إشعار الوسطاء الرجاء انتظار الوسيط حتى ياتي ❤️"
        )

class DevModal(discord.ui.Modal, title="أسئلة التذكرة - تطوير المابات"):
    details = discord.ui.TextInput(label="اكتب طلبك بالتفصيل", style=discord.TextStyle.paragraph, placeholder="اشرح تفاصيل طلبك للماب...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(
            interaction, 
            ticket_type="dev", 
            answers=[("اكتب طلبك بالتفصيل", self.details.value)],
            welcome_msg="اهلاً بك في تكت تطوير المابات في سيرفر Asc\nلقد تم إشعار فريق التطوير الرجاء التحلي بالصبر ❤️"
        )

class SupportModal(discord.ui.Modal, title="أسئلة التذكرة - الدعم الفني"):
    problem = discord.ui.TextInput(label="اكتب مشكلتك", style=discord.TextStyle.paragraph, placeholder="اشرح مشكلتك أو استفسارك هنا...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(
            interaction, 
            ticket_type="support", 
            answers=[("اكتب مشكلتك", self.problem.value)],
            welcome_msg="لقد تم إشعار فريق الدعم الفني الرجاء التحلي بالصبر ❤️"
        )

async def create_ticket(interaction: discord.Interaction, ticket_type: str, answers: list, welcome_msg: str):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    cfg = CONFIG[ticket_type]

    category = guild.get_channel(cfg["category_id"])
    staff_role = guild.get_role(cfg["role_id"])

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

    ticket_channel = await guild.create_text_channel(
        name=f"{cfg['name']}-{interaction.user.name}",
        category=category,
        overwrites=overwrites
    )

    staff_mention = staff_role.mention if staff_role else "@الطاقم"
    await ticket_channel.send(content=f"{staff_mention} {interaction.user.mention} **اهلا**\n\n{welcome_msg}")

    embed = discord.Embed(color=PURPLE_COLOR)
    for label, val in answers:
        embed.add_field(name=label, value=f"```\n{val}\n```", inline=False)
    embed.set_footer(text="Asc Support System")

    view = TicketControlView(staff_role_id=cfg["role_id"])
    await ticket_channel.send(embed=embed, view=view)
    await interaction.followup.send(f"تم إنشاء تذكرتك بنجاح: {ticket_channel.mention}", ephemeral=True)

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="وسيط مضمون", description="لضمان عملية التداول بوجود وسيط", emoji="⚖️", value="middleman"),
            discord.SelectOption(label="تطوير المابات", description="لطلب خدمة تطوير ماب سرقه او ماب النطة", emoji="📊", value="dev"),
            discord.SelectOption(label="التواصل مع الدعم الفني", description="لأى مشكله أو استفسار", emoji="🎧", value="support"),
        ]
        super().__init__(placeholder="اختر نوع التذكرة", min_values=1, max_values=1, options=options, custom_id="ticket_select_menu")

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        if val == "middleman":
            await interaction.response.send_modal(MiddlemanModal())
        elif val == "dev":
            await interaction.response.send_modal(DevModal())
        elif val == "support":
            await interaction.response.send_modal(SupportModal())

class TicketSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

@bot.tree.command(name="ticket", description="إرسال لوحة التكتات المتقدمة للسيرفر")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_panel(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    desc_text = (
        "إذا كان لديك أي سؤال أو استفسار، كل ما عليك هو فتح تذكرة،\n"
        "وسيتواصل معك فريق الدعم مباشرة بكل اهتمام وسرعة.\n"
        "نضمن لك تجربة دعم سهلة، واضحة، وسريعة."
    )

    embed = discord.Embed(
        title="نحن هنا لخدمتك",
        description=desc_text,
        color=PURPLE_COLOR
    )
    embed.set_image(url=BANNER_URL)

    view = TicketSelectView()
    await interaction.channel.send(embed=embed, view=view)
    await interaction.followup.send("تم إرسال لوحة التكتات بنجاح! ✅", ephemeral=True)

# المسابقات والألعاب
class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.entries = set()

    @discord.ui.button(label="دخول المسابقة 🎉", style=discord.ButtonStyle.primary, custom_id="join_giveaway_btn")
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.entries:
            self.entries.remove(interaction.user.id)
            await interaction.response.send_message("❌ تم إلغاء دخولك في المسابقة.", ephemeral=True)
        else:
            self.entries.add(interaction.user.id)
            await interaction.response.send_message("✅ تم تسجيل دخولك بنجاح في المسابقة!", ephemeral=True)

@bot.tree.command(name="gstart", description="بدء مسابقة جديدة بالسيرفر")
@app_commands.describe(prize="الجائزة", duration_seconds="المدة بالثواني", winners="عدد الفائزين")
@app_commands.checks.has_permissions(administrator=True)
async def gstart(interaction: discord.Interaction, prize: str, duration_seconds: int, winners: int = 1):
    await interaction.response.defer()

    view = GiveawayView()
    embed = discord.Embed(
        title=f"🎉 مسابقة جديدة: {prize}",
        description=f"اضغط على الزر بالأسفل للمشاركة!\n\n⏱️ **المدة:** {duration_seconds} ثانية\n👑 **عدد الفائزين:** {winners}",
        color=PURPLE_COLOR
    )
    embed.set_footer(text="Asc Giveaways")

    await interaction.followup.send(embed=embed, view=view)
    await asyncio.sleep(duration_seconds)

    if not view.entries:
        await interaction.channel.send(f"❌ انتهت المسابقة على **{prize}** ولكن لم يشارك أحد!")
        return

    winner_ids = random.sample(list(view.entries), min(winners, len(view.entries)))
    winner_mentions = ", ".join([f"<@{w_id}>" for w_id in winner_ids])

    win_embed = discord.Embed(
        title="🎉 نتائج المسابقة!",
        description=f"مبروك للفائز/ين بالجائزة **{prize}**:\n\n{winner_mentions}",
        color=discord.Color.green()
    )
    await interaction.channel.send(content=winner_mentions, embed=win_embed)

class RouletteView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=30)
        self.user = user

    @discord.ui.button(label="سحب الزناد 🎯", style=discord.ButtonStyle.danger)
    async def trigger(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("هذه اللعبة ليست لك!", ephemeral=True)
            return

        outcomes = ["💥 *آوت! طلقة في الراس، خسرت اللعبة!*", "🍀 *كلاك! نجاة، العجلة فارغة!*"]
        result = random.choice(outcomes)
        button.disabled = True
        await interaction.response.edit_message(content=f"{interaction.user.mention} {result}", view=self)

@bot.tree.command(name="roulette", description="لعبة الروليت السريعة")
async def roulette(interaction: discord.Interaction):
    view = RouletteView(interaction.user)
    embed = discord.Embed(
        title="🎲 لعبة الروليت",
        description=f"مرحباً {interaction.user.mention}، اضغط على الزر وسَم بالرحمن...",
        color=PURPLE_COLOR
    )
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="mafia", description="بدء غرفة لعبة المافيا")
async def mafia(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🕵️‍♂️ لعبة المافيا",
        description="تم بدء تجهيز روم المافيا! تجمعوا في روم الصوت للبدء باللعب وإسناد الأدوار تلقائياً.",
        color=PURPLE_COLOR
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="فحص سرعة استجابة البوت")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! 🏓 سرعة الاستجابة: {latency}ms")

token = os.getenv("TOKEN")
bot.run(token)
