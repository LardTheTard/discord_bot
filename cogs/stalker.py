from discord.ext import commands, tasks
from datetime import datetime, date, time, timedelta
import random
import os
import math
# drop sqlite3, use motor (async MongoDB driver)
from motor.motor_asyncio import AsyncIOMotorClient

TRACKED_GUILD_ID = int(os.getenv("TRACKED_GUILD_ID"))
TRACKED_USER_ID = int(os.getenv("TRACKED_USER_ID"))
HOME_GUILD_ID = int(os.getenv("HOME_GUILD_ID"))
HOME_GUILD_CHANNEL_ID = int(os.getenv("HOME_GUILD_CHANNEL_ID"))
RECIEVER_ID = int(os.getenv("RECIEVER_ID"))
MONGO_URI = os.getenv("MONGO_URI")
BOT_START_UP_TIME = datetime.now()

class stalker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.presence_cache = {}
        self.DmsToggled = False
        self.ServerUpdatesToggled = False

        # CHANGED: create Mongo client/collection once
        self._mongo = AsyncIOMotorClient(MONGO_URI)               # CHANGED
        self._db = self._mongo["discord_bot_db"]                  # CHANGED
        self._col = self._db["activity_log"]                      # CHANGED
        # Optional index (unique by day+user). Not required because we set `_id`.
        # self._col.create_index([("user_id", 1), ("date", 1)], unique=True)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        home_guild_main_channel = self.bot.get_channel(HOME_GUILD_CHANNEL_ID)
        timestamp = f"[{datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}]"
        await home_guild_main_channel.send(
            f"{timestamp} **{message.author.name}** deleted a message in {message.channel.name} in the {message.guild.name} guild: {message.content}"
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        home_guild_main_channel = self.bot.get_channel(HOME_GUILD_CHANNEL_ID)
        timestamp = f"[{datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}]"
        await home_guild_main_channel.send(
            f"{timestamp} **{after.author.name}** edited a message in {after.channel.name} in the {after.guild.name} guild. It was edited from '{before.content}' to '{after.content}'"
        )

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        user_id = after.id
        current_status = str(after.status)  # CHANGED: stringify once
        current_activities = set(a.name for a in after.activities if a and a.name)
        timestamp = datetime.now()          # CHANGED: keep as datetime (store as BSON Date)
        timestamp_str = timestamp.strftime("%Y-%m-%d %I:%M:%S %p")  # CHANGED: for human messages
        today = date.today().strftime("%Y-%m-%d")  # CHANGED

        home_guild = self.bot.get_guild(HOME_GUILD_ID)
        home_guild_main_channel = home_guild.get_channel(HOME_GUILD_CHANNEL_ID)
        tracked_user = self.bot.get_user(TRACKED_USER_ID)
        reciever = self.bot.get_user(RECIEVER_ID)

        # CHANGED: preserve earlier state; ensure we fallback to strings/sets
        prev_state = self.presence_cache.get(
            user_id,
            {
                "status": str(before.status),
                "activities": set(a.name for a in (before.activities or []) if a and a.name),
            },
        )

        status_changed = prev_state["status"] != current_status
        activity_changed = prev_state["activities"] != current_activities

        # CHANGED: cache strings, not Discord enums
        self.presence_cache[user_id] = {
            "status": current_status,
            "activities": current_activities,
        }

        # ===== DB KEY for the day =====
        doc_id_today = f"{user_id}_{today}"  # CHANGED: single compound key

        if status_changed:
            if user_id == TRACKED_USER_ID and current_status == "dnd":
                rng = random.randint(1, 99)
                if rng == 1:
                    await tracked_user.send("I hate you hehe")
                else:
                    await tracked_user.send("I love you ♥")

            # CHANGED: MongoDB logic replaces SELECT/INSERT/UPDATE
            if current_status in ("online", "dnd", "idle"):
                # User is online-ish: ensure today's doc exists, update last_seen
                await self._col.update_one(  # CHANGED
                    {"_id": doc_id_today},
                    {
                        # setOnInsert only applied when creating the doc the first time today
                        "$setOnInsert": {
                            "user_id": user_id,
                            "username": after.name,
                            "date": today,
                            "total_seconds": 0,
                        },
                        # always update last_seen when they become active
                        "$set": {"last_seen": timestamp},
                    },
                    upsert=True,
                )
            else:
                # going offline/invisible/etc.: add the elapsed time since last_seen to total_seconds
                doc = await self._col.find_one({"_id": doc_id_today})  # CHANGED
                if doc and doc.get("last_seen"):
                    last_seen = doc["last_seen"]  # stored as datetime
                    elapsed = int((timestamp - last_seen).total_seconds())
                    new_total = int(doc.get("total_seconds", 0)) + max(elapsed, 0)
                    await self._col.update_one(  # CHANGED
                        {"_id": doc_id_today},
                        {"$set": {"total_seconds": new_total, "last_seen": timestamp}},
                    )
                else:
                    # No doc for today (e.g., stayed online across midnight). Approximate from midnight.
                    start_of_day = datetime.combine(date.today(), time.min)  # 00:00 today
                    seconds_since_midnight = int((timestamp - start_of_day).total_seconds())
                    await self._col.update_one(  # CHANGED
                        {"_id": doc_id_today},
                        {
                            "$setOnInsert": {
                                "user_id": user_id,
                                "username": after.name,
                                "date": today,
                            },
                            "$set": {
                                "last_seen": timestamp,
                                "total_seconds": seconds_since_midnight,
                            },
                        },
                        upsert=True,
                    )

            print(
                f"[{timestamp_str}]: {after.name} changed status from {prev_state['status']} to {current_status}. "
                + ("" if activity_changed else "\n")
            )
            if self.DmsToggled:
                await reciever.send(
                    f"[{timestamp_str}]: {after.name} changed status from {prev_state['status']} to {current_status}."
                )
            if self.ServerUpdatesToggled:
                await home_guild_main_channel.send(
                    f"[{timestamp_str}]: {after.name} changed status from {prev_state['status']} to {current_status}."
                )

        if activity_changed:
            print(
                f"[{timestamp_str}]: {after.name} changed activity from "
                f"{', '.join(prev_state['activities']) or 'None'} to {', '.join(current_activities) or 'None'}\n"
            )
            if self.DmsToggled:
                await reciever.send(
                    f"[{timestamp_str}]: {after.name} changed activity from "
                    f"{', '.join(prev_state['activities']) or 'None'} to {', '.join(current_activities) or 'None'}\n"
                )
            if self.ServerUpdatesToggled:
                await home_guild_main_channel.send(
                    f"[{timestamp_str}]: {after.name} changed activity from "
                    f"{', '.join(prev_state['activities']) or 'None'} to {', '.join(current_activities) or 'None'}\n"
                )

    # CHANGED: ensure we use datetime.time from our imports, not module attribute
    @tasks.loop(time=time(hour=0, minute=0))  # CHANGED
    async def update_all_screentimes(self):
        today_str = date.today().strftime("%Y-%m-%d")                    # CHANGED
        yesterday_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")  # CHANGED
        start_of_today = datetime.combine(date.today(), time.min)        # 00:00 today
        now = datetime.now()

        for user_id, user_info in self.presence_cache.items():
            # CHANGED: statuses are strings in cache now
            if user_info["status"] != "offline":
                doc_id_y = f"{user_id}_{yesterday_str}"                  # CHANGED
                doc_y = await self._col.find_one({"_id": doc_id_y})      # CHANGED

                if doc_y and doc_y.get("last_seen"):
                    # add time from last_seen yesterday until midnight
                    extra = int((start_of_today - doc_y["last_seen"]).total_seconds())
                    new_total = int(doc_y.get("total_seconds", 0)) + max(extra, 0)
                    await self._col.update_one(                           # CHANGED
                        {"_id": doc_id_y},
                        {"$set": {"total_seconds": new_total}},
                    )

                # ensure today's doc exists with fresh last_seen (user is online at midnight)
                doc_id_t = f"{user_id}_{today_str}"
                await self._col.update_one(                               # CHANGED
                    {"_id": doc_id_t},
                    {
                        "$setOnInsert": {
                            "user_id": user_id,
                            "username": (self.bot.get_user(user_id).name if self.bot.get_user(user_id) else str(user_id)),
                            "date": today_str,
                            "total_seconds": 0,
                        },
                        "$set": {"last_seen": now},
                    },
                    upsert=True,
                )

    @commands.command()  # CHANGED: add parentheses so discord.py registers it
    async def botuptime(self, ctx):
        start_date = BOT_START_UP_TIME.strftime("%Y-%m-%d %I:%M:%S %p")  # CHANGED: match your format
        total_uptime_seconds = int((datetime.now() - BOT_START_UP_TIME).total_seconds())
        uptime_hours = math.floor(total_uptime_seconds / 3600)
        uptime_minutes = math.floor((total_uptime_seconds % 3600) / 60)
        uptime_seconds = math.floor(total_uptime_seconds % 60)
        await ctx.send(
            f"Bot started running at [{start_date}]. So far the uptime is {uptime_hours} hours, {uptime_minutes} minutes, and {uptime_seconds} seconds."
        )

    @commands.command(aliases=["tdms"])
    async def toggledms(self, ctx):
        user_id = str(ctx.author.id)
        if user_id == str(RECIEVER_ID) and self.DmsToggled:
            self.DmsToggled = False
            await ctx.send("Stopped sending messages to reciever.")
        elif user_id == str(RECIEVER_ID) and not self.DmsToggled:
            self.DmsToggled = True
            await ctx.send("Started sending messages to reciever.")
        else:
            await ctx.send("You are not the reciever.")

    @commands.command(aliases=["tsus"])
    async def toggleserverupdates(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id == str(HOME_GUILD_ID) and self.ServerUpdatesToggled:
            self.ServerUpdatesToggled = False
            await ctx.send("Stopped sending messages to home server.")
        elif guild_id == str(HOME_GUILD_ID) and not self.ServerUpdatesToggled:
            self.ServerUpdatesToggled = True
            await ctx.send("Started sending messages to home server.")
        else:
            await ctx.send("This is not the home server.")

async def setup(bot):
    await bot.add_cog(stalker(bot))