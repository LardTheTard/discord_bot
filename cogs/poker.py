import discord
import json
import random
import os
from discord.ext import commands

class poker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.blind_index = 0

        # Finds the file paths to the json files, since they're stored in the 'json' folder
        self.cur_sess_file_path = os.path.join(os.path.dirname(__file__), '..', 'json', 'cur_sess.json')
        self.user_data_file_path = os.path.join(os.path.dirname(__file__), '..', 'json', 'user_data.json')

        # Opens json files for reading
        try:
            with open(self.cur_sess_file_path, 'r') as f:
                self.cur_sess = json.load(f)
        except FileNotFoundError:
            self.cur_sess = {}
        try:
            with open(self.user_data_file_path, 'r') as f:
                self.user_data = json.load(f)
        except FileNotFoundError:
            self.user_data = {}

    def initialize_user_data(self, user_id: str, member: discord.Member):
            if user_id not in self.user_data:
                self.user_data[user_id] = {'name': member.name, 'chips': 0}

    @commands.command()
    async def join(self, ctx):
        user_id = str(ctx.author.id)
        if user_id in self.cur_sess:
            await ctx.send(f"You are already in the session, {ctx.author.name}.")
        else:
            # References buy_in_value, which if not set due to not being in json/self.user_data.json, will return an error. Therefore, must pull data from github first or set it manually using !setbuyin
            self.cur_sess[user_id] = {'name': ctx.author.name, 'chips': self.user_data['buy_in_value']['chips'], 'buyins': -1, 'folded': False, 'contribution': 0}
            with open(self.user_data_file_path, 'w') as f:
                json.dump(self.user_data, f) 
            with open(self.cur_sess_file_path, 'w') as f:
                json.dump(self.cur_sess, f) 
            await ctx.send(f"{ctx.author.name} is now in the session.")

    @commands.command()
    async def leave(self, ctx):
        user_id = str(ctx.author.id)
        if user_id not in self.cur_sess:
            await ctx.send(f"You are not currently in the session, {ctx.author.name}.")
        else:
            self.user_data[user_id]['chips'] += self.cur_sess[user_id]['chips'] + self.cur_sess[user_id]['buyins'] * self.user_data['buy_in_value']['chips']
            del self.cur_sess[user_id]
            with open(self.user_data_file_path, 'w') as f:
                json.dump(self.user_data, f) 
            with open(self.cur_sess_file_path, 'w') as f:
                json.dump(self.cur_sess, f) 
            await ctx.send(f"{ctx.author.name} left the session.")

    @commands.command(aliases=["ss"])
    async def sessstats(self, ctx):
        def sortByChips(dict):
            return -(dict['chips'] - dict['buyins'] * self.user_data['buy_in_value']['chips'])

        embed = discord.Embed(
            title=f"Current Session Leaderboard",
            color=discord.Color.red()
        )
        user_list = []
        for i in self.cur_sess:
            user_list.append(self.cur_sess[i])
        user_list.sort(key=sortByChips)
        rank = 1
        for i in user_list:
            embed.add_field(name=f"{rank}. {i['name']}", value=f"{i['buyins']} buyins, {i['chips']} chips", inline=False)
            rank += 1
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)


    @commands.command(aliases=["sc"])
    async def setchips(self, ctx, member: discord.Member, num: int):
        user_id = str(member.id)
        self.initialize_user_data(user_id, member)
        self.user_data[user_id]['chips'] = num
        with open(self.user_data_file_path, 'w') as f:
            json.dump(self.user_data, f) 
        await ctx.send(f"{member.name}'s now has {num} chips.")

    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx):
        def sortByChips(dict):
            return -dict['chips']

        embed = discord.Embed(
            title=f"{ctx.guild.name} Leaderboard",
            color=discord.Color.green()
        )
        user_list = []
        for i in self.user_data:
            if i != "buy_in_value":
                user_list.append(self.user_data[i])
        user_list.sort(key=sortByChips)
        rank = 1
        for i in user_list:
            embed.add_field(name=f"{rank}. {i['name']}", value=f"{i['chips']} chips", inline=False)
            rank += 1
            # embed.add_field(name=self.user_data[i]['name'], value=self.user_data[i]['chips'], inline=True)
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

    @commands.command(aliases=["cc"])
    async def changechips(self, ctx, member: discord.Member, num: int):
        user_id = str(member.id)
        self.initialize_user_data(user_id, member)
        self.user_data[user_id]['chips'] += num
        with open(self.user_data_file_path, 'w') as f:
            json.dump(self.user_data, f)
        await ctx.send(f"{member.name}'s chips have been updated to {self.user_data[user_id]['chips']}.")

    @commands.command()
    async def reset(self, ctx, member: discord.Member):
        user_id = str(member.id)
        self.user_data[user_id] = {'name': member.name, 'chips': 0}
        with open(self.user_data_file_path, 'w') as f:
            json.dump(self.user_data, f)
        await ctx.send(f"{member.name}'s stats have been reset.")

    @commands.command()
    async def resetseason(self, ctx):
        for i in self.user_data:
            self.user_data[i] = {'name': self.user_data[i]['name'], 'chips': 0}
        with open(self.user_data_file_path, 'w') as f:
            json.dump(self.user_data, f)
        await ctx.send("All stats have been reset.")

    @commands.command()
    async def setbuyin(self, ctx, num: int):
        if len(self.cur_sess) == 0:
            self.user_data['buy_in_value'] = {'name': None, 'chips': num}
            with open(self.user_data_file_path, 'w') as f:
                json.dump(self.user_data, f)
                await ctx.send(f"Buy-in value changed to {num}.")
        else:
            await ctx.send("A session is current ongoing, please end the session before changing buy-in values.")

    @commands.command()
    async def start(self, ctx):

        class Card:
            def __init__(self, value, alias, suit):
                self.value = value
                self.alias = alias
                self.suit = suit

            def __str__(self):
                return f"{self.alias} of {self.suit}"

        suits = ["Hearts♥️", "Spades♠️", "Diamonds♦️", "Clubs♣️"]
        aliases = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"]
        deck = []
        board = []
        player_order = []
        pot = 0
        stage_index = 0
        highest_raise = 0
        for j in suits:
            for i in range(1, 14):
                card = Card(i, aliases[i - 1], j)
                deck.append(card)
        random.shuffle(deck)
        # deck_str = ", ".join(str(card) for card in deck)
        for id in self.cur_sess:
            id = int(id.strip())
            try:
                member = ctx.guild.get_member(id)
                await member.send(f"**Hand:**\n{deck.pop(0)}\n{deck.pop(0)}")
            except discord.Forbidden:
                await ctx.send(f"❌ Could not DM {member.name}. They may have DMs disabled.")
        # await ctx.send(deck_str)
        for id in self.cur_sess:
            id = int(id.strip())
            member = ctx.guild.get_member(id)
            player_order.append(member)
        await ctx.send("Preflop betting round, hands have been sent to players.")
        # blind_index += 1 (Add this in afterwards, it just changes who has the blind)
        blind_index %= len(player_order)
        raised_player_index = blind_index
        turn_order = blind_index
        while True: #while people havent folded, continue
        #any(not player['folded'] for player in self.cur_sess.values())
            playing = 0
            for player in self.cur_sess.values():
                if not player['folded']:
                    playing += 1
            if playing <= 1:
                break
            turn_order %= len(player_order)
            cur_player = player_order[turn_order]
            cur_id = str(cur_player.id)
            #Does NOT account for raising and matching the raise to go to the next stage
            if turn_order == raised_player_index:
                if stage_index == 1:
                    for i in range(3):
                        board.append(deck.pop(0))
                    await ctx.send(f"**Flop:**\n{board[0]}\n{board[1]}\n{board[2]}")
                elif stage_index == 2:
                    board.append(deck.pop(0))
                    await ctx.send(f"**Turn:**\n{board[0]}\n{board[1]}\n{board[2]}\n{board[3]}")
                elif stage_index == 3:
                    board.append(deck.pop(0))
                    await ctx.send(f"**River:**\n{board[0]}\n{board[1]}\n{board[2]}\n{board[3]}\n{board[4]}")
                stage_index += 1
            if self.cur_sess[cur_id]['folded'] == False:
                def checkmsg(m): #use for checking message input for current players turn, whether it is valid (ie. from cur_player and in the same channel)
                    return m.author.id == cur_player.id and m.channel == ctx.channel
                await ctx.send(f"It is {cur_player.name}'s turn. You may 'check', 'call', 'fold', or 'raise (value here)'")
                while True:
                    #action = await bot.wait_for("message", timeout = 30.0, check = checkmsg)
                    action = await self.bot.wait_for("message", check = checkmsg) #checks what the message input is, also maybe catch timeout error
                    action = action.content
                    if action.lower() == 'fold' or action.lower() == 'check' or action.lower() == 'call' or action.startswith('raise'): #will do stuff based on what action it is
                        if action.lower() == 'fold': #folds
                            await ctx.send("what the hellyante")
                            await ctx.send(cur_player.name)
                            if len(self.cur_sess) != 0 and ctx.author == cur_player:
                                self.cur_sess[cur_id]['folded'] = True
                                await ctx.send("what the fuck")
                            # forgot to dump the folded change into the self.cur_sess json, so only the self.cur_sess has the folded change
                        elif action.lower() == 'call': #calls, if raise is 0, works the same as checking
                            self.cur_sess[cur_id]['chips'] -= highest_raise - self.cur_sess[cur_id]['contribution']
                            self.cur_sess[cur_id]['contribution'] = highest_raise
                            print('current highest that contribution is adding is', highest_raise, 'and the cur_id is', cur_id)
                        elif action.lower() == 'check': #checks
                            print(highest_raise)
                            if self.cur_sess[cur_id]['contribution'] != highest_raise:
                                await ctx.send(f"Cannot check, must call/raise to match bet. {highest_raise - self.cur_sess[cur_id]['contribution']} to match.")
                                continue
                        else: #raises
                            if len(action.lower().split()) == 2 and action.lower().split()[1].isdigit():
                                raise_value = int(action.lower().split()[1])
                            else:
                                await ctx.send("Invalid value/format for a raise, please try again.")
                                continue
                            self.cur_sess[cur_id]['chips'] -= highest_raise - self.cur_sess[cur_id]['contribution'] + raise_value
                            self.cur_sess[cur_id]['contribution'] = highest_raise + raise_value
                            highest_raise += raise_value
                            raised_player_index = turn_order
                        with open(self.cur_sess_file_path, 'w') as f:
                            json.dump(self.cur_sess, f) 
                        turn_order += 1
                        pot = 0
                        for i in self.cur_sess:
                            pot += self.cur_sess[i]['contribution']
                        print('pot:', pot)
                        break
                    else:
                        ctx.send(f"Invalid action, please 'check', 'call', 'fold', or 'raise (value here)', {cur_player.name}")
            else:
                turn_order += 1
        for player in self.cur_sess.values():
            if not player['folded']:
                await ctx.send(f"{player['name']} is the winner!")
                break

        
    # unfinished



            


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if 'hello' in message.content.lower():
            await message.channel.send('Hello!')

    # Simple commands
    @commands.command()
    async def stop(self, ctx):
        await ctx.send("bot is shutting down")
        print('bot shut down')
        await self.bot.close()   

    # 📌 Command: Get User Info
    @commands.command()
    async def userinfo(self, ctx, member: discord.Member = None):
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
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Missing arguments! Please provide all required inputs.")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Unknown command! Type `!help` to see available commands.")
        else:
            await ctx.send(error)
            await ctx.send("❌ An error occurred!")

async def setup(bot):
    await bot.add_cog(poker(bot))