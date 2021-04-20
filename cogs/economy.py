import os, sys, discord
from discord.ext import commands

if not os.path.isfile("settings.py"):
	sys.exit("'settings.py' not found!")
else:
	import settings


# Cog for computing stuff connected with sb economy
# main goal is approximate player networth based on current prices 


class Economy(commands.Cog, name="economy"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="networth", aliases=['nw'])
    async def testcommand(self, context):
        pass

def setup(bot):
    bot.add_cog(Economy(bot))