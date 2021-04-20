import os
import sys
import discord
import asyncio
import aiohttp
import json
from discord.ext import commands, tasks
from database import Database
import session
from datetime import datetime, timedelta
from pytz import timezone
import logging
import numpy as np 

if not os.path.isfile("settings.py"):
    sys.exit("'settings.py' not found!")
else:
    import settings



#This cog is responsible for signing up guild and updating database

class Clan(commands.Cog, name="clan"):
    def __init__(self, bot):
        self.bot = bot
        self.clans_queue = []
        self.sb_queue = []
        self.refresh.start()
        self.tz = timezone('EST')
        self.today_local = datetime.now().strftime('%Y-%m-%d')

    #This command is used for signing up new clans (hypixel guilds) to db

    @commands.cooldown(1, 120, commands.BucketType.user)
    @commands.command(name="register",aliases=['r'])
    async def register(self, context, arg):
        """
        Use this command to register your guild!
        """

        arg = str.lower(arg)
        if Database.find_one('guild', {'name': arg}):
            embed = discord.Embed(title=f'Failed!',description=f'{arg} exist in database, please use {settings.BOT_PREFIX}guild {arg} instead.')
            self.register.reset_cooldown(context)
            await context.send(embed=embed)
            return 0

        embed = discord.Embed(title=f'Fetching data, please wait!')
        message = await context.send(embed=embed)

        headers = {'API-Key': settings.API_AUTH}
        params = {'name': arg}
        url = "https://api.hypixel.net/guild"
        response = await session.get(url=url, params=params, headers=headers)

        if(response['success'] and (response['guild'] is not None)):
            gid = response['guild']['_id']
            name = str.lower(response['guild']['name'])
            members = parse_members(response['guild']['members'])
            
            if len(members) < 3:
                embed = discord.Embed(
                    description=f'U need at least 3 members to register guild!')
                await message.edit(embed=embed)
                return 0
            
            g_exp = parse_gexp(response['guild']['members'])
            today = datetime.now(self.tz).strftime('%Y-%m-%d') 
            yesterday = (datetime.now(self.tz) - timedelta(days=1)).strftime('%Y-%m-%d')

            gxp_today = []
            gxp_yesterday = []
            for i in g_exp:
                gxp_today.append(i[today])
                gxp_yesterday.append(i[yesterday])
            gxp_today = sum(gxp_today)
            gxp_yesterday = sum(gxp_yesterday)
            record = {'_id': gid, 'name': name, 'members': members, 'daily_xp': {today: gxp_today, yesterday: gxp_yesterday}}

            try:
                fetched = await self.update_skyblock(members, gid, g_exp)
            except Exception as e:
                logging.error(f'{e} update_skyblock failed')
                embed = discord.Embed(title=f"Failed! Try again in few minutes.")
                await message.edit(emded=embed)
                return 0 
            for i in fetched:
                filter = {'_id': i['_id']}
                new = {"$set": i}
                Database.update_one('members',filter, new, upsert=True)

            Database.insert_one('guild',record)


            embed = discord.Embed(title=f"Success!", description=f"{arg} registered succefully!")
        else:
            embed = discord.Embed(title=f"Failed!",description=f"{arg} not found")


        await message.edit(embed=embed)

    # don't run before bot_ready()
    def g_queue_start(self):
        clans = []
        for i in Database.find('guild',{}):
            clans.append(i['_id'])
        return clans

    @staticmethod
    async def get_guild(id):
        headers = {'API-Key': settings.API_AUTH}
        params = {'id': id}
        url = "https://api.hypixel.net/guild"

        response = await session.get(url=url, params=params, headers=headers)
        return response 

    @staticmethod
    async def get_guild_db(id):
        await asyncio.sleep(0)
        return Database.find_one('guild', {'_id': id})


    async def update_gxp(self, id):
        response_api = await self.get_guild(id)
        # if response_api == 0:
        #     return 0 
        today = datetime.now(self.tz).strftime('%Y-%m-%d')
        yesterday = (datetime.now(self.tz) - timedelta(days=1)).strftime('%Y-%m-%d')
        gxp = []
        for i in parse_gexp(response_api['guild']['members']):
            gxp.append(i[today])
        gxp_today = sum(gxp)

        members = response_api['guild']['members']
        
        for i in members:
            try:
                today_xp = i['expHistory'][today]
            except KeyError:
                yesterday_xp = 0
            try:
                yesterday_xp = i['expHistory'][yesterday]
            except KeyError:
                yesterday_xp = 0
            else:
                filter = {'_id': i['uuid']}
                newvalue = { "$set": {f"gxp.{today}": today_xp, f"gxp.{yesterday}": yesterday_xp} }
                Database.update_one('members',filter,newvalue)

        Database.update_one('guild',{'_id': id},{'$set': {f'daily_xp.{today}': gxp_today}})

    async def compare(self,id):
        response_api = await self.get_guild(id)
        members_api = parse_members(response_api['guild']['members'])

        response_db = await self.get_guild_db(id)
        members_db = response_db['members']

        #removing member from guild and removing gid
        removed = (set(members_db)-set(members_api))
        if len(removed)>0:
            removed = list(removed)
            for i in removed:
                filter = {'_id': id}
                newvalue = {'$pull': {'members': f'{i}'}}
                Database.update_one('guild',filter,newvalue)

                filter = {'_id': i}
                Database.update_one('members',filter,{'$set': {'gid': None}})

            print(f"Cleaned user memberships: {removed}")

        #adding player to guild and getting his skyblock data
        added = (set(members_api) - set(members_db))
        if len(added)>0:
            fetched = await self.update_skyblock(list(added),id,register=False)
            for i in fetched:
                filter = {'_id': i['_id']}
                new = {"$set": i}
                Database.update_one('members',filter, new, upsert=True)

                filter = {'_id': id}
                newvalue = {'$push': {'members': f"{i['_id']}" }}
                Database.update_one('guild',filter,newvalue)

            print(f"Added new users: {added}")


    @tasks.loop(seconds=60)
    async def refresh(self):
        if len(self.clans_queue) == 0:
            self.clans_queue = self.g_queue_start()

        #print(self.clans_queue)
        try:
            current = self.clans_queue.pop(0)
        except IndexError:
            print('Database is empty')
            return 0
        try:
            await self.update_gxp(current)
        except Exception as e:
            logging.error(f"{e}")
            print("Couldn't refresh {current}")
            return 0

        await self.compare(current)

        if(self.today_local != datetime.now().strftime('%Y-%m-%d')):
            logging.info(f"Udpading!")
            print('Updating!')
            print(self.today_local,datetime.now().strftime('%Y-%m-%d'))
            await self.daily_update()
            self.today_local = datetime.now().strftime('%Y-%m-%d')
            logging.info(f"Udpate is done")
            print(f"Update is done!")
        logging.info(f"Refreshed {current} succefully!")
        print(f"Refreshed {current} succefully!")

    @refresh.before_loop
    async def before_refresh(self):
        print('Initializing refresh loop...')
        await self.bot.wait_until_ready()

    async def daily_update(self):
        sb_queue = self.g_queue_start()
        
        for current in sb_queue:
            #current = sb_queue.pop(0)
            print(f'Updating {current}...')
            g = Database.find_one('guild',{'_id': current})
            try:
                await self.update_players(g['members'],current)
            except Exception:
                print(f'Faled to update {current}')
                logging.error(f'[Update Error] {e}')
            print(f'{current}: updated!')
            await asyncio.sleep(120)

    @commands.is_owner()
    @commands.command(name='force')
    async def force_update(self,context):
            await self.daily_update()
            embed = discord.Embed(title=f"Update is done!")
            await context.send(embed=embed)


    @staticmethod
    async def update_skyblock(players, gid,g_exp=[None],register=True):
        if register==False:
            g_exp = [None]*len(players)
        sb_profiles = await asyncio.gather(*[get_player(i, settings.API_AUTH) for i in players])
        main_profiles = await asyncio.gather(*[determine_main(sb_profiles[i], players[i]) for i in range(0, len(players))])
        names = await asyncio.gather(*[uuid_to_name(i) for i in players])
        fetched = await asyncio.gather(*[fetch_player_data(main_profiles[i], players[i], names[i], gid, g_exp[i]) for i in range(0, len(players))])
        return fetched

    @staticmethod
    async def update_player(player,gid,g_exp):
        sb_profiles = await get_player(player, settings.API_AUTH)
        main_profile = await determine_main(sb_profiles,player)
        name = await uuid_to_name(player)
        fetched = await fetch_player_data(main_profile,player,name,gid,g_exp)
        return fetched



    async def update_players(self, players,gid):
        fetched = await self.update_skyblock(players,gid,register=False)
        for i in fetched:
            filter = {'_id': i['_id']}
            new = {"$set": i}
            Database.update_one('members',filter, new, upsert=True)
        await asyncio.sleep(0)


def setup(bot):
    bot.add_cog(Clan(bot))


def parse_members(x):
    sweaty_members = []
    for i in x:
        sweaty_members.append(i['uuid'])
    return sweaty_members


def parse_gexp(x):
    g_exp = []
    for i in x:
        g_exp.append(i['expHistory'])
    return g_exp


async def determine_main(response, uuid):
    prof = []
    try:
        for i in response['profiles']:
            if 'experience_skill_combat' in i['members'][uuid]:
                prof.append((i['profile_id'], i['members']
                            [uuid]['experience_skill_combat']))
            else:
                prof.append((i['profile_id'], 0))
    except Exception as e:
        exception = f"{type(e).__name__}: {e}"
        print(exception)
        return None

    main_profile = max(prof, key=lambda item: item[1])[0]
    await asyncio.sleep(0)
    for i in response['profiles']:
        if i['profile_id'] == main_profile:
            return i


async def get_player(uuid, API_AUTH):
    headers = {'API-Key': API_AUTH}
    params = {'uuid': uuid}
    url = "https://api.hypixel.net/skyblock/profiles"
    response = await session.get(url=url, params=params, headers=headers)
    return response


async def fetch_player_data(response, uuid, name, gid, gxp):
    columns_skills = ['experience_skill_combat', 'experience_skill_mining', 'experience_skill_alchemy',
                      'experience_skill_farming', 'experience_skill_taming', 'experience_skill_enchanting',
                      'experience_skill_fishing', 'experience_skill_foraging']

    columns_slayers = ['zombie', 'spider', 'wolf']

    columns_dungeons = ['healer', 'mage', 'berserk', 'archer', 'tank']

    if(response == None):
        temp = {}
    else:
        temp = response['members'][uuid]

    row = dict()
    row.update({'_id': uuid})

    if gxp:
        row.update({'gxp': gxp})

    row.update({'name': name})
    row.update({'name_lower': str.lower(name)})
    row.update({'gid': gid})
    row.update({'skills': {}})
    row.update({'slayers': {}})
    row.update({'dungeons': {}})
    row['dungeons'].update({'fastest_time': {}})

    for i in columns_skills:
        try:
            row['skills'].update({i: temp[i]})
        except KeyError:
            logging.warning(f"[Not found while fetching player] {row['_id']} {i} skill value marked as a NULL")
            row['skills'].update({i: None})

    for i in columns_slayers:
        try:
            row['slayers'].update({i: temp['slayer_bosses'][i]['xp']})
        except KeyError:
            logging.warning(f"[Not found while fetching player] {row['_id']} {i} slayer value marked as a NULL")
            row['slayers'].update({i: None})

    for i in columns_dungeons:
        try:
            row['dungeons'].update(
                {i: temp['dungeons']['player_classes'][i]['experience']})
        except KeyError:
            logging.warning(f"[Not found while fetching player] {row['_id']} {i} dungeons class value marked as a NULL")
            row['dungeons'].update({i: None})

    try:
        row['dungeons'].update(
            {'experience_cata': temp['dungeons']['dungeon_types']['catacombs']['experience']})
    except KeyError:
        logging.warning(f"[Not found while fetching player] {row['_id']} {i} catacombs value marked as a NULL")
        row['dungeons'].update({'experience_cata': None})

    for i in range(0,8):
        try:
            row['dungeons']['fastest_time'].update(
                    {str(i): temp['dungeons']['dungeon_types']['catacombs']['fastest_time'][str(i)]})
        except KeyError:
            logging.warning(f"[Not found while fetching player] {row['_id']} {i} dungeons fastest_time value marked as a NULL")
            row['dungeons']['fastest_time'].update({str(i): None})

    await asyncio.sleep(0)
    return(row)


async def uuid_to_name(uuid):
    url = f'https://api.mojang.com/user/profiles/{uuid}/names'
    raw_response = await session.get(url,raw=True)
    if(raw_response.status == 200):
        response = await raw_response.text()
        response = json.loads(response)
        return response[-1]['name']
    else:
        print(f'Failed to get name of {uuid}, returning None instead')
        return None

