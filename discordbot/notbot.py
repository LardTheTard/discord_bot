import discord
import json
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")



try:
    with open('user_data.json', 'r') as f:
        user_data = json.load(f)
except FileNotFoundError:
    user_data = {}

@bot.command()
async def setchips(ctx, member: discord.Member, num: int):
    user_id = str(member.id)
    if user_id not in user_data:
        user_data[user_id] = {'name': member.name, 'chips': 0, 'xp': 0}
    user_data[user_id]['chips'] = num
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f) 
    await ctx.send(f"{member.name}'s XP is now set to {num}.")

@bot.command()
async def setxp(ctx, xp: int):
    user_id = str(ctx.author.id)  # Convert user ID to string for JSON compatibility
    if user_id not in user_data:
        user_data[user_id] = {'name': member.name, 'chips': 0, 'xp': 0}
    user_data[user_id]['xp'] = xp  # Store XP for the user
    # Save data to the file
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)
    await ctx.send(f"{ctx.author.name}'s XP is now set to {xp}.")

@bot.command()
async def getxp(ctx):
    user_id = str(ctx.author.id)
    xp = user_data.get(user_id, 0)  # Default to 0 XP if no data exists
    await ctx.send(f"{ctx.author.name} has {xp} XP.")

@bot.command()
async def leaderboard(ctx):
    def sortByChips(dict):
        return -dict['chips']

    embed = discord.Embed(
        title=f"{ctx.guild.name} Leaderboard",
        color=discord.Color.green()
    )
    user_list = []
    for i in user_data:
        user_list.append(user_data[i])
    user_list.sort(key=sortByChips)
    for i in user_list:
        embed.add_field(name=i['name'], value=i['chips'], inline=False)
        # embed.add_field(name=user_data[i]['name'], value=user_data[i]['chips'], inline=True)
    embed.set_footer(text=f"Requested by {ctx.author}")
    await ctx.send(embed=embed)



@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('hello'):
        await message.channel.send('Hello!')
    
    await bot.process_commands(message)



# Simple commands
@bot.command()
async def stop(ctx):
    await ctx.send("bot is shutting down")
    print('bot shut down')
    await bot.close()

# 📌 Command: Simple Hello
@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.mention}! 👋")

# 📌 Command: Get User Info
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author  # Default to command sender if no user is mentioned
    embed = discord.Embed(
        title=f"User Info: {member.name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Username", value=member.name, inline=True)
    embed.add_field(name="User ID", value=member.id, inline=True)
    embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d"), inline=False)
    embed.set_thumbnail(url=member.avatar.url)  # User's profile picture
    await ctx.send(embed=embed)

# 📌 Command: Send an Embed
@bot.command()
async def embed(ctx):
    embed = discord.Embed(
        title="This is an Embed!",
        description="Embeds make messages look **cool** 😎",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Requested by {ctx.author}")
    await ctx.send(embed=embed)

# 📌 Error Handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing arguments! Please provide all required inputs.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Unknown command! Type `!help` to see available commands.")
    else:
        await ctx.send("❌ An error occurred!")

# Run the Bot (Replace "YOUR_TOKEN_HERE" with your bot token)
bot.run(os.getenv('DISCORD_API_KEY'))

