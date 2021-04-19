import os, sys, discord
from discord.ext import commands
import session
import logging

if not os.path.isfile("settings.py"):
	sys.exit("'settings.py' not found!")
else:
	import settings

class Admin(commands.Cog, name="admin"):
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, cog: str):
            try:
                self.bot.unload_extension(cog)
            except Exception as e:
                await ctx.send('Could not unload cog')
                return
            if cog == 'cogs.clan':
                await session.close()
            await ctx.send('Unloaded cog!')

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, cog: str):
            try:
                self.bot.load_extension(cog)
            except Exception as e:
                await ctx.send('Could not load cog')
                return
            await ctx.send('Loaded cog!')


    @commands.command()
    @commands.is_owner()
    async def refresh(self, ctx, cog: str):
            try:
                self.bot.unload_extension(cog)
                self.bot.load_extension(cog)
            except Exception as e:
                await ctx.send('Could not refresh cog')
                return
            await ctx.send('Refreshed cog!')

    @commands.command()
    @commands.is_owner()
    async def turnoff(self, ctx):
            logging.info('Turned off by command!')
            logging.disable()
            await session.close()
            await ctx.send('Bye bye!')
            sys.exit("rip bot")






def setup(bot):
    bot.add_cog(Admin(bot))