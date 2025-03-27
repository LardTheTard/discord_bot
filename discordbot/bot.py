import discord
import json
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

try:
    with open('cur_sess.json', 'r') as f:
        cur_sess = json.load(f)
except FileNotFoundError:
    cur_sess = {}

try:
    with open('user_data.json', 'r') as f:
        user_data = json.load(f)
except FileNotFoundError:
    user_data = {}

@bot.command()
async def join(ctx):
    user_id = str(ctx.author.id)
    if user_id in cur_sess:
        await ctx.send(f"You are already in the session, {ctx.author.name}.")
    else:
        # References buy_in_value, which if not set due to not being in user_data.json, will return an error. Therefore, must pull data from github first or set it manually using !setbuyin
        cur_sess[user_id] = {'name': ctx.author.name, 'chips': user_data['buy_in_value']['chips'], 'buyins': -1}
        with open('user_data.json', 'w') as f:
            json.dump(user_data, f) 
        with open('cur_sess.json', 'w') as f:
            json.dump(cur_sess, f) 
        await ctx.send(f"{ctx.author.name} is now in the session.")

@bot.command()
async def leave(ctx):
    user_id = str(ctx.author.id)
    if user_id not in cur_sess:
        await ctx.send(f"You are not currently in the session, {ctx.author.name}.")
    else:
        user_data[user_id]['chips'] += cur_sess[user_id]['chips'] + cur_sess[user_id]['buyins'] * user_data['buy_in_value']['chips']
        del cur_sess[user_id]
        with open('user_data.json', 'w') as f:
            json.dump(user_data, f) 
        with open('cur_sess.json', 'w') as f:
            json.dump(cur_sess, f) 
        await ctx.send(f"{ctx.author.name} left the session.")

@bot.command(aliases=["ss"])
async def sessstats(ctx):
    def sortByChips(dict):
        return -(dict['chips'] - dict['buyins'] * user_data['buy_in_value']['chips'])

    embed = discord.Embed(
        title=f"Current Session Leaderboard",
        color=discord.Color.red()
    )
    user_list = []
    for i in cur_sess:
        user_list.append(cur_sess[i])
    user_list.sort(key=sortByChips)
    rank = 1
    for i in user_list:
        embed.add_field(name=f"{rank}. {i['name']}", value=f"{i['buyins']} buyins, {i['chips']} chips", inline=False)
        rank += 1
    embed.set_footer(text=f"Requested by {ctx.author}")
    await ctx.send(embed=embed)


@bot.command(aliases=["sc"])
async def setchips(ctx, member: discord.Member, num: int):
    user_id = str(member.id)
    if user_id not in user_data:
        user_data[user_id] = {'name': member.name, 'chips': 0}
    user_data[user_id]['chips'] = num
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f) 
    await ctx.send(f"{member.name}'s now has {num} chips.")

@bot.command(aliases=["lb"])
async def leaderboard(ctx):
    def sortByChips(dict):
        return -dict['chips']

    embed = discord.Embed(
        title=f"{ctx.guild.name} Leaderboard",
        color=discord.Color.green()
    )
    user_list = []
    for i in user_data:
        if i != "buy_in_value":
            user_list.append(user_data[i])
    user_list.sort(key=sortByChips)
    rank = 1
    for i in user_list:
        embed.add_field(name=f"{rank}. {i['name']}", value=f"{i['chips']} chips", inline=False)
        rank += 1
        # embed.add_field(name=user_data[i]['name'], value=user_data[i]['chips'], inline=True)
    embed.set_footer(text=f"Requested by {ctx.author}")
    await ctx.send(embed=embed)

@bot.command(aliases=["cc"])
async def changechips(ctx, member: discord.Member, num: int):
    user_id = str(member.id)
    if user_id not in user_data:
        user_data[user_id] = {'name': member.name, 'chips': 0}
    user_data[user_id]['chips'] += num
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)
    await ctx.send(f"{member.name}'s chips have been updated to {user_data[user_id]['chips']}.")

@bot.command()
async def reset(ctx, member: discord.Member):
    user_id = str(member.id)
    user_data[user_id] = {'name': member.name, 'chips': 0}
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)
    await ctx.send(f"{member.name}'s stats have been reset.")

@bot.command()
async def resetseason(ctx):
    for i in user_data:
        user_data[i] = {'name': user_data[i]['name'], 'chips': 0}
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)
    await ctx.send("All stats have been reset.")

@bot.command()
async def setbuyin(ctx, num: int):
    if len(cur_sess) == 0:
        user_data['buy_in_value'] = {'name': None, 'chips': num}
        with open('user_data.json', 'w') as f:
            json.dump(user_data, f)
            await ctx.send(f"Buy-in value changed to {num}.")
    else:
        await ctx.send("A session is current ongoing, please end the session before changing buy-in values.")



@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if 'hello' in message.content.lower():
        await message.channel.send('Hello!')
    
    await bot.process_commands(message)



# Simple commands
@bot.command()
async def stop(ctx):
    await ctx.send("bot is shutting down")
    print('bot shut down')
    await bot.close()   

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
bot.run()