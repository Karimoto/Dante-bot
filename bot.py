import discord
import os
import sys
from discord.ext.commands import Bot
from discord.ext import commands
import asyncio
from database import Database
if not os.path.isfile("settings.py"):
    sys.exit("'settings.py' not found!")
else:
    import settings
import session
import logging


bot = Bot(command_prefix=settings.BOT_PREFIX)

logging.basicConfig(filename='./logs/log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)


@bot.event
async def on_ready():
    print('Logged as {0.user}'.format(bot))
    Database.initialize()
    session.WebSession.create()
    print(bot.guilds)
    # activityvar = discord.Activity(
    #     type=discord.ActivityType.custom, state=f"{settings.BOT_PREFIX}help")
    # await bot.change_presence(activity=activityvar)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{settings.BOT_PREFIX}help"))

if __name__ == "__main__":
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                bot.load_extension(f"cogs.{extension}")
                print(f"Loaded extension '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                print(f"Failed to load extension {extension}\n{exception}")


@bot.event
async def on_command_completion(ctx):
    fullCommandName = ctx.command.qualified_name
    split = fullCommandName.split(" ")
    executedCommand = str(split[0])
    print(f"Executed {executedCommand} command in {ctx.guild.name} (ID: {ctx.message.guild.id}) by {ctx.message.author} (ID: {ctx.message.author.id})")
    logging.info(
        f"Executed {executedCommand} command in {ctx.guild.name} (ID: {ctx.message.guild.id}) by {ctx.message.author} (ID: {ctx.message.author.id})")


@bot.event
async def on_command_error(ctx, error):

    executedCommand = str(ctx.command)

    if isinstance(error, commands.CommandOnCooldown):
        em = discord.Embed(title=f"Slow it down bro!",
                           description=f"Try again in {error.retry_after:.2f}s.")
        await ctx.send(embed=em)
        logging.info(
            f"[On cooldown] Executed {executedCommand} command in {ctx.guild.name} (ID: {ctx.message.guild.id}) by {ctx.message.author} (ID: {ctx.message.author.id})")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument")
        logging.info(
            f"[Missing argument] Executed {executedCommand} command in {ctx.guild.name} (ID: {ctx.message.guild.id}) by {ctx.message.author} (ID: {ctx.message.author.id})")

    elif isinstance(error, commands.BadArgument):
        await ctx.send("Bad argument!")
        logging.info(
            f"[Bad argument] Executed {executedCommand} command in {ctx.guild.name} (ID: {ctx.message.guild.id}) by {ctx.message.author} (ID: {ctx.message.author.id})")

    elif isinstance(error, commands.errors.CheckFailure):
        await ctx.send("Error: {}".format(error.param))
        logging.warning(
            f"[Checkfailure] Executed {executedCommand} command in {ctx.guild.name} (ID: {ctx.message.guild.id}) by {ctx.message.author} (ID: {ctx.message.author.id})")

    elif isinstance(error, commands.errors.ExpectedClosingQuoteError):
        await ctx.send(f"Quote bug")
        logging.info(
            f"[Quote not closed] Executed {executedCommand} command in {ctx.guild.name} (ID: {ctx.message.guild.id}) by {ctx.message.author} (ID: {ctx.message.author.id})")

    elif isinstance(error, commands.errors.CommandNotFound):
        await ctx.send(f"{error}")
        logging.info(
            f"[Tried weird command] Executed {executedCommand} command in {ctx.guild.name} (ID: {ctx.message.guild.id}) by {ctx.message.author} (ID: {ctx.message.author.id})")
    raise error


bot.run(settings.TOKEN)
