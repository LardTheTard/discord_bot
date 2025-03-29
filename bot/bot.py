import discord
import json
import random
from dotenv import load_dotenv
import os
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)
blind_index = 0

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

cur_sess_file_path = os.path.join(os.path.dirname(__file__), '..', 'json', 'cur_sess.json')
user_data_file_path = os.path.join(os.path.dirname(__file__), '..', 'json', 'user_data.json')

try:
    with open(cur_sess_file_path, 'r') as f:
        cur_sess = json.load(f)
except FileNotFoundError:
    cur_sess = {}

try:
    with open(user_data_file_path, 'r') as f:
        user_data = json.load(f)
except FileNotFoundError:
    user_data = {}

def initialize_user_data(user_id: str, member: discord.Member):
    if user_id not in user_data:
        user_data[user_id] = {'name': member.name, 'chips': 0}

@bot.command()
async def join(ctx):
    user_id = str(ctx.author.id)
    if user_id in cur_sess:
        await ctx.send(f"You are already in the session, {ctx.author.name}.")
    else:
        # References buy_in_value, which if not set due to not being in json/user_data.json, will return an error. Therefore, must pull data from github first or set it manually using !setbuyin
        cur_sess[user_id] = {'name': ctx.author.name, 'chips': user_data['buy_in_value']['chips'], 'buyins': -1, 'folded': False, 'contribution': 0}
        with open(user_data_file_path, 'w') as f:
            json.dump(user_data, f) 
        with open(cur_sess_file_path, 'w') as f:
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
        with open(user_data_file_path, 'w') as f:
            json.dump(user_data, f) 
        with open(cur_sess_file_path, 'w') as f:
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
    initialize_user_data(user_id, member)
    user_data[user_id]['chips'] = num
    with open(user_data_file_path, 'w') as f:
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
    initialize_user_data(user_id, member)
    user_data[user_id]['chips'] += num
    with open(user_data_file_path, 'w') as f:
        json.dump(user_data, f)
    await ctx.send(f"{member.name}'s chips have been updated to {user_data[user_id]['chips']}.")

@bot.command()
async def reset(ctx, member: discord.Member):
    user_id = str(member.id)
    user_data[user_id] = {'name': member.name, 'chips': 0}
    with open(user_data_file_path, 'w') as f:
        json.dump(user_data, f)
    await ctx.send(f"{member.name}'s stats have been reset.")

@bot.command()
async def resetseason(ctx):
    for i in user_data:
        user_data[i] = {'name': user_data[i]['name'], 'chips': 0}
    with open(user_data_file_path, 'w') as f:
        json.dump(user_data, f)
    await ctx.send("All stats have been reset.")

@bot.command()
async def setbuyin(ctx, num: int):
    if len(cur_sess) == 0:
        user_data['buy_in_value'] = {'name': None, 'chips': num}
        with open(user_data_file_path, 'w') as f:
            json.dump(user_data, f)
            await ctx.send(f"Buy-in value changed to {num}.")
    else:
        await ctx.send("A session is current ongoing, please end the session before changing buy-in values.")

class Card:
    def __init__(self, value, alias, suit):
        self.value = value
        self.alias = alias
        self.suit = suit

    def __str__(self):
        return f"{self.alias} of {self.suit}"

@bot.command()
async def start(ctx):
    suits = ["Hearts♥️", "Spades♠️", "Diamonds♦️", "Clubs♣️"]
    aliases = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"]
    deck = []
    player_order = []
    highest_raise = 0
    for j in suits:
        for i in range(1, 14):
            card = Card(i, aliases[i - 1], j)
            deck.append(card)
    random.shuffle(deck)
    # deck_str = ", ".join(str(card) for card in deck)
    for id in cur_sess:
        id = int(id.strip())
        try:
            member = ctx.guild.get_member(id)
            await member.send(f"**Hand:**\n{deck.pop(0)}\n{deck.pop(0)}")
        except discord.Forbidden:
            await ctx.send(f"❌ Could not DM {member.name}. They may have DMs disabled.")
    # await ctx.send(deck_str)
    for id in cur_sess:
        id = int(id.strip())
        member = ctx.guild.get_member(id)
        player_order.append(member)
    await ctx.send("Preflop betting round, hands have been sent to players.")

    blind_index += 1
    blind_index %= len(player_order)
    turn_order = blind_index
    while (any(False in i for i in cur_sess)): #while people havent folded, continue
        turn_order %= len(player_order)
        cur_player = player_order[turn_order]
        if cur_sess[cur_player]['folded'] == False:
            def checkmsg(m): #use for checking message input for current players turn, whether it is valid (ie. from cur_player and in the same channel)
                return m.author == cur_player and m.channel == ctx.channel
            await ctx.send(f"It is {cur_player.name}'s turn. You may 'check', 'call', 'fold', or 'raise (value here)'")
            while True:
                action = await bot.wait_for("message", timeout = 30.0, check = checkmsg) #checks what the message input is
                if action.lower() == 'fold' or action.lower() == 'check' or action.lower() == 'call' or action.startsWith('raise'): #will do stuff based on what action it is
                    if action.lower() == 'fold': #folds
                        if len(cur_sess) != 0 and ctx.author == cur_player:
                            cur_sess[cur_player.id]['folded'] = True
                    elif action.lower() == 'call': #placeholder
                        pass
                    elif action.lower() == 'check': #checks
                        #if to check if player contribution matches max_raise
                        pass
                    else: #raises
                        if action.lower().split()[1].isdigit():
                            raise_value = action.lower().split()[1]
                        else:
                            ctx.send("Invalid value/format for a raise, please try again.")
                            continue
                        highest_raise += raise_value
                    turn_order += 1
                    break
                else:
                    ctx.send(f"Invalid action, please 'check', 'fold', or 'raise (value here)', {cur_player.name}")
        else:
            turn_order += 1

    
# unfinished



        


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
load_dotenv()
token = os.getenv("DISCORD_TOKEN")
bot.run(token)