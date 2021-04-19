import os
import sys
import discord
import platform
import random
import aiohttp
import json
from discord.ext import commands
import asyncio


#todo, nothing here

if not os.path.isfile("settings.py"):
	sys.exit("'settings.py' not found!")
else:
	import settings

class general(commands.Cog, name="general"):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="info", aliases=["botinfo"])
    async def info(self, context):
        """
        Nothing interesting here... Check out stats/clan!
        """
        embed = discord.Embed(
            name="Bot Information"
        )
        embed.add_field(
            name="Owner:",
            value="Karimotoo#9520",
            inline=True
        )
        embed.add_field(
            name="Prefix:",
            value=f"{settings.BOT_PREFIX}",
            inline=False
        )
        embed.set_footer(
            text=f"Requested by {context.message.author}"
        )
        await context.send(embed=embed)


def setup(bot):
    bot.add_cog(general(bot))
