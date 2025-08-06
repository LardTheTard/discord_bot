from discord.ext import commands

class EventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        print(f'Message from {message.author}: {message.content}')

def setup(bot):
    bot.add_cog(EventCog(bot))