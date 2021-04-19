import os
import sys
import discord
import platform
import random
import aiohttp
import json
from discord.ext import commands
import asyncio
import random


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
        Just info... Check out stats/clan!
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

    @commands.command(name="invite")
    async def invite(self, context):
        """
        Get the invite link of the Dante bot. 
        """
        await context.send("I sent you a private message!")
        await context.author.send(f"Invite me by clicking here: https://discordapp.com/oauth2/authorize?&client_id={settings.APPLICATION_ID}&scope=bot&permissions=515136")
    @commands.command(name="quote", aliases=["date"])
    async def quote(self, context):
        """
        Great leader Dante quotes
        """

        quotes = ["Things have been getting out of control lately.",
                    "People are losing their values and other candidates are acting like everything is fine.",
                    "They simply don't have the grip required to lead this great land.",
                    "Values. Progress. Justice",
                    "I will stabilize this rapidly declining system, permanently.",
                    "I will fix the declining economy, but above all things, safety is my priority.",
                    "Power needs to be in the right hands.",
                    "ORDER",
                    "SECURITY",
                    "FREEDOM",
                    "JUSTICE",
                    "ORDER. SECURITY AND FREEDOM",
                    "Do not sub to Technoblade. He is a dangerous individual."
                    "Due to safety concerns, dungeons have been outlawed, effective immediately. I have your security in mind.",
                    "Pets have now been outlawed effective immediately. They were too distracting which is too dangerous to players.",
                    "They also won't stop sniffing the goons...",
                    "Until further notice, we have ended our alliance with the sketchy Dwarves and will be preventing players from going to their mines.",
                    "Mining Islands have now been outlawed, effective immediately. We will be considering outlawing Mining in general too, but that's for another time. It's just too dangerous.",
                    "Island Transportation has been outlawed. Nowhere is safer than home."]
        choosen_index = random.randint(0,len(quotes)-1)

        embed = discord.Embed(description=quotes[choosen_index])
        await context.send(embed=embed)

def setup(bot):
    bot.add_cog(general(bot))
