from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
import os

TRACKED_GUILD_ID = (int) (os.getenv("TRACKED_GUILD_ID"))
TRACKED_USER_ID = (int) (os.getenv("TRACKED_USER_ID"))
RECIEVER_ID = (int) (os.getenv("RECIEVER_ID"))

class stalker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.presence_cache = {}
        self.SendMessage = False

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        user_id = after.id
        current_status = after.status
        current_activities = set(a.name for a in after.activities if a and a.name)
        timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        
        mutual_guild = self.bot.get_guild(TRACKED_GUILD_ID)
        tracked_user = mutual_guild.get_member(TRACKED_USER_ID) or await mutual_guild.fetch_member(TRACKED_USER_ID)
        reciever = mutual_guild.get_member(RECIEVER_ID) or await mutual_guild.fetch_member(RECIEVER_ID)

        prev_state = self.presence_cache.get(user_id, {
            "status": before.status,
            "activities": set(a.name for a in before.activities if a and a.name)
        })

        # Only log if there's a meaningful change
        status_changed = prev_state["status"] != current_status
        activity_changed = prev_state["activities"] != current_activities

        # Update cache
        self.presence_cache[user_id] = {
            "status": current_status,
            "activities": current_activities
        }

        if status_changed:
            if user_id == TRACKED_USER_ID and str(current_status) == "dnd":
                await tracked_user.send("I love you ♥")
            print(f"[{timestamp}]: {after.name} changed status from {prev_state['status']} to {current_status}. " + ('' if activity_changed else '\n'))
            if self.SendMessage:
                await reciever.send(f"[{timestamp}]: {after.name} changed status from {prev_state['status']} to {current_status}.")

        if activity_changed:
            print(f"[{timestamp}]: {after.name} changed activity from {', '.join(prev_state['activities']) or 'None'} to {', '.join(current_activities) or 'None'}\n")
            if self.SendMessage:
                await reciever.send(f"[{timestamp}]: {after.name} changed activity from {', '.join(prev_state['activities']) or 'None'} to {', '.join(current_activities) or 'None'}\n")

    @commands.command()
    async def sendmsgs(self, ctx):
        user_id = str(ctx.author.id)
        if user_id == str(RECIEVER_ID) and self.SendMessage:
            self.SendMessage = False
            await ctx.send("Stopped sending messages to reciever.")
        elif user_id == str(RECIEVER_ID) and not self.SendMessage:
            self.SendMessage = True
            await ctx.send("Started sending messages to reciever.")
        else:
            await ctx.send("You are not the reciever.")
        

async def setup(bot):
    await bot.add_cog(stalker(bot))