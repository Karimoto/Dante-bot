import os, sys, discord
from discord.ext import commands
from database import Database
import asyncio
from datetime import datetime, timedelta
from pytz import timezone
import pandas as pd

if not os.path.isfile("settings.py"):
	sys.exit("'settings.py' not found!")
else:
	import settings
tz = timezone('EST')


#   This cog is used to compute stuff like skill average etc. basically everything connected with basic statistics.
#   Tbh few things should be done on database side but it's kinda impossible (very time consuming and probably will increase efficiency by only a little bit)

class Stat(commands.Cog, name="stat"):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.command(name="guild",aliases=['g'])
    async def guild(self, ctx, arg):
        """
        Show your guild insights!
        """
        items = await self.get_guild(arg)
        if not items:
            embed = discord.Embed(description=f'Please use first register guild!')
            await ctx.send(embed=embed)
            self.guild.reset_cooldown(ctx)
            return 0

        embed = discord.Embed(title='Collecting data...')
        embed.set_footer(text='If this process takes a long time, it means that your guild has insufficient data ')
        message = await ctx.send(embed=embed)

        embeds = []

        embed = await self.embed_overall(arg)
        embed1 = await self.embed_skills_top3(arg)
        embed2 = await self.embed_dungeons_top3(arg)
        embed3 = await self.embed_slayers_top3(arg)
        embed4 = await self.embed_dungeons_fastest_time_top3(arg)
        

        embeds = [embed,embed1,embed2,embed3,embed4]
        await message.edit(embed=embed) #stop "collecting data"

        #declaring slider

        emotes = ['⬅️','➡️']
        for emo in emotes:
            await message.add_reaction(emo)

        emoji1 = '⬅️'
        emoji2 = '➡️'

        emojis = [str(emoji1), str(emoji2)]

        print(message.author)
        def check(reaction, user):
            return user == ctx.author and str(reaction) in emojis

        embed_index = 0 
        max_index = 4


        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                return
            else:
                if str(reaction)==str(emoji1) and embed_index != 0:
                        embed_index-=1
                        await message.edit(embed=embeds[embed_index])

                if str(reaction)==str(emoji2) and embed_index != max_index:
                    embed_index+=1
                    await message.edit(embed=embeds[embed_index])
            #print(embed_index)

    async def embed_overall(self,arg):
        items = await self.get_guild(arg)
        today = datetime.now(tz).strftime('%Y-%m-%d')
        yesterday = (datetime.now(tz) - timedelta(days=1)).strftime('%Y-%m-%d')

        embed = discord.Embed(title=items['name']+'🎭', colour=discord.Colour(0x3e038c),
            description='**Gxp today:** '+str(items['daily_xp'][today]) + '\n\u200b' +
                            '**Gxp yesterday:** '+str(items['daily_xp'][yesterday]))

        skill_avg = await self.get_skill_avg(arg)
        slayer_avg = await self.get_slayer_avg(arg)
        cata_avg = await self.get_cata_avg(arg)
        embed.add_field(name=f"Skill avg ⚒️", value=skill_avg, inline=True )

        embed.add_field(name=f"Slayer avg 🗡️", value=slayer_avg, inline=True )

        embed.add_field(name=f"Catagombs avg 💀", value=cata_avg, inline=True )

        #keycaps = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']


        top10 = await self.get_top10(arg)
        top10_name = top10['name'].tolist()
        top10_name = '\n\u200b'.join(top10_name)
        index = '\n\u200b'.join([f'{i}' for i in range(1,11)])
        top10_gxp = top10['gxp'].tolist()
        top10_gxp = map(str, top10_gxp)
        top10_gxp = '\n\u200b'.join(top10_gxp)

        embed.add_field(name=f"no", value=index, inline=True )
        embed.add_field(name=f"Player", value=top10_name, inline=True )
        embed.add_field(name=f"Gxp", value=top10_gxp, inline=True )

        return embed

    async def embed_skills_top3(self,arg):
        max_avg = await self.get_max_skill_avg(arg)


        embed = discord.Embed(title='Best players',description=f'Guild: {arg}', colour=discord.Colour(0x3e038c))
        embed.add_field(name=f"\u200b", value='\u200b', inline=True )
        embed.add_field(name=f"Skill average 👑", value=self.styledf(max_avg), inline=True )
        embed.add_field(name=f"\u200b", value='\u200b', inline=True )

        #List
        # 0 combat
        # 1 mining
        # 2 farming
        # 4 alchemy
        # 5 fishing
        # 6 foraging
        max_skills = await self.get_max_skills(arg)

        embed.add_field(name=f"Combat 🗡️", value=self.styledf(max_skills[0]), inline=True )
        embed.add_field(name=f"Mining ⛏️", value=self.styledf(max_skills[1]), inline=True )
        embed.add_field(name=f"Farming 🐄", value=self.styledf(max_skills[2]), inline=True )
        embed.add_field(name=f"Fishing 🐟", value=self.styledf(max_skills[5]), inline=True )
        embed.add_field(name=f"Foraging 🪓", value=self.styledf(max_skills[6]), inline=True )
        embed.add_field(name=f"Alchemy ⚗️", value=self.styledf(max_skills[4]), inline=True )

        return embed

    async def embed_slayers_top3(self,arg):

        embed = discord.Embed(title='Slayers',description=f'Guild: {arg}',colour=discord.Colour(0x3e038c))
        data_max_slayer = await self.get_max_slayer(arg)

        embed.add_field(name='Zombie 🧟', value =self.styledf(data_max_slayer[0]), inline=False)

        embed.add_field(name='Spider 🕸️', value =self.styledf(data_max_slayer[1]), inline=False)
        embed.add_field(name='Wolf 🐺', value =self.styledf(data_max_slayer[2]), inline=False)

        return embed

    async def embed_dungeons_fastest_time_top3(self,arg):
        fastest_times = await self.get_dungeons_fastest_time(arg)
        embed = discord.Embed(title='Dungeon fastest times',colour=discord.Colour(0x3e038c))
        embed.add_field(name='Entrace', value =self.styledf(fastest_times[0]), inline=True)
        for i in range(1,7):
            embed.add_field(name=f'Floor {i}', value =self.styledf(fastest_times[i]), inline=True)
        embed.add_field(name='\u200b', value ='\u200b', inline=True)
        embed.add_field(name=f'Floor {7}', value =self.styledf(fastest_times[7]), inline=True)
        return embed

    async def embed_dungeons_top3(self,arg):

        embed = discord.Embed(title= f"Dungeons top3:", description=f'Guild: {arg}',colour=discord.Colour(0x3e038c))
        #embed.set_footer(text=f'{arg}')
        data_max_dungeons = await self.get_max_dungeons(arg)
        

        embed.add_field(name='Cata lvl 🦴', value =self.styledf(data_max_dungeons[0]), inline=True)
        embed.add_field(name='Healer 💓', value =self.styledf(data_max_dungeons[1]), inline=True)
        embed.add_field(name='Mage 🪄', value =self.styledf(data_max_dungeons[2]), inline=True)
        embed.add_field(name='Berserk 🗡️', value =self.styledf(data_max_dungeons[3]), inline=True)
        embed.add_field(name='Archer 🏹', value =self.styledf(data_max_dungeons[4]), inline=True)
        embed.add_field(name='Tank 🛡️', value =self.styledf(data_max_dungeons[5]), inline=True)
        return embed


    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(name="skills",aliases=['sk'])
    async def skills(self, ctx, arg):
        """
        Top3 skills leaderboard
        """
        items = await self.get_guild(arg)
        if not items:
            items = await self.get_guild(arg)
            embed = discord.Embed(description=f'Please use first register guild!')
            await ctx.send(embed=embed)
            self.guild.reset_cooldown(ctx)
            return 0
        embed = await self.embed_skills_top3(arg)
        await ctx.send(embed=embed)

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(name="slayers",aliases=['sl'])
    async def slayers(self, ctx, arg):
        """
        Top3 slayers leaderboard
        """
        items = await self.get_guild(arg)
        if not items:
            embed = discord.Embed(description=f'Please use first register guild!')
            await ctx.send(embed=embed)
            self.guild.reset_cooldown(ctx)
            return 0
        embed = await self.embed_slayers_top3(arg)
        await ctx.send(embed=embed)

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(name="dtime",aliases=['dt'])
    async def dtime(self, ctx, arg):
        """
        Fastest dungeons runs!
        """
        items = await self.get_guild(arg)
        if not items:
            embed = discord.Embed(description=f'Please use first register guild!')
            await ctx.send(embed=embed)
            self.dtime.reset_cooldown(ctx)
            return 0
        embed = await self.embed_dungeons_fastest_time_top3(arg)
        await ctx.send(embed=embed)

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(name='leaderboard',aliases=['l'])
    async def leaderboard(self, ctx, arg):
        """
        Show your guild gxp leaderboard
        """
        items = await self.get_guild(arg)
        if not items:
            embed = discord.Embed(description=f'Please use first register command!')
            await ctx.send(embed=embed)
            self.leaderboard.reset_cooldown(ctx)
            return 0
        embed = await self.embed_overall(arg)
        await ctx.send(embed=embed)

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(name="dungeons",aliases=['d'])
    async def dungeons(self, ctx, arg):
        """
        Top3 cata/class level
        """
        items = await self.get_guild(arg)
        if not items:
            embed = discord.Embed(description=f'Please use first register guild!')
            await ctx.send(embed=embed)
            self.guild.reset_cooldown(ctx)
            return 0
        embed = await self.embed_dungeons_top3(arg)
        await ctx.send(embed=embed)

    # @commands.command(name="top")
    # async def top(self, ctx, *args):
    #     all = ['skills','slayers']

    #     columns_skills = ['combat', 'mining',
    #                     'farming', 'enchanting','alchemy', 'fishing','foraging', 'taming']

    #     columns_slayers = ['zombie','spider','wolf']

    #     if args:
    #         if len(args)<3 or args[0] not in all or : 
    #             embed = discord.Embed(description=f'Usage -> skills <guildname> <skills/slayers> <cap max 50>')
    #             await ctx.send(embed=embed)
    #             return 0

    #     #that's big brain code ngl
    #     if args[0] == 'skills':
    #         if args[1] in columns_skills:
    #             result = await self.get_max_skills(args[0],ammount=args[2])
    #             for i in columns_skills:
    #                 if args[1] == i:
    #                     result[]
    #         else:
    #             return 0
    #     elif args[0] == 'slayers':
    #         if args[1] in columns_slayers:
    #             pass
    #         else:
    #             return 0


    @staticmethod
    async def get_guild(name):
        name = str.lower(name)
        await asyncio.sleep(0)
        return Database.find_one('guild', {'name': name})

    async def get_top10(self,name):
        items = await self.get_guild(name)
        today = datetime.now(tz).strftime('%Y-%m-%d')
        df = []
        for i in items['members']:
            player = Database.find_one('members', {'_id': i})
            try:
                raw_row = (player['name'],player['gxp'][today])
            except Exception as e:
                raw_row = (player['name'],0)
                logging.warning(f'{e} get_top10')
            df.append(raw_row)
        df = pd.DataFrame(df)
        df.columns = ['name','gxp']
        return df.nlargest(10, ['gxp'])


    async def get_skill_df(self, name):

        columns_skills60 = ['experience_skill_combat', 'experience_skill_mining',
                        'experience_skill_farming', 'experience_skill_enchanting']

        columns_skills50 = ['experience_skill_alchemy', 'experience_skill_fishing','experience_skill_foraging', 'experience_skill_taming']


        items = await self.get_guild(name)
        df = []
        for i in items['members']:
            player = Database.find_one('members', {'_id': i})
            try:
                raw_row = [player['name']] + [self.calculate_lvl(player['skills'][j],50) for j in columns_skills50]
                raw_row = raw_row + [self.calculate_lvl(player['skills'][j],60) for j in columns_skills60]
            except Exception as e:
                raise e
            
            df.append(raw_row)
        df = pd.DataFrame(df)
        df.columns = ['name'] + columns_skills50 + columns_skills60

        df = df.dropna()
        if df.empty:
            raise commands.BadArgument

        return df


    async def get_skill_avg(self,name):
        df = await self.get_skill_df(name)
        df['mean'] = df.mean(axis=1)
        mean = df['mean'].mean()
        await asyncio.sleep(0)

        return round(mean,2)

    async def get_max_skill_avg(self,name):
        df = await self.get_skill_df(name)
        df['mean'] = df.mean(axis=1)
        top3avg = df[['name','mean']].nlargest(3,'mean')
        top3avg['mean'] = top3avg['mean'].apply(round,args=(2,))
        await asyncio.sleep(0)
        #print(top3avg)
        return top3avg




    #that's a long name ngl
    async def get_skill_avg_for_every_skill(self,name):
        df = await self.get_skill_df(name)
        df = df[['experience_skill_combat', 'experience_skill_mining','experience_skill_farming', 
                'experience_skill_enchanting','experience_skill_alchemy', 'experience_skill_fishing','experience_skill_foraging',
                'experience_skill_taming']].mean()
        await asyncio.sleep(0)
        return df



    # async def get_skill_max(self,name):
    #     df = await self.get_skill_df(name)
    #     skills = ['experience_skill_combat', 'experience_skill_mining','experience_skill_farming', 'experience_skill_enchanting','experience_skill_alchemy', 'experience_skill_fishing','experience_skill_foraging', 'experience_skill_taming']
    #     data_max = []
    #     data_max = df[df.experience_skill_combat == df.experience_skill_combat.max()]
    #     await asyncio.sleep(0)
    #     print(data_max)

    async def get_slayer_df(self, name):

        columns_slayers = ['zombie', 'spider',
                        'wolf']

        items = await self.get_guild(name)
        df = []
        for i in items['members']:
            player = Database.find_one('members', {'_id': i})
            try:
                raw_row = [player['name']] + [player['slayers'][j] for j in columns_slayers]
            except Exception as e:
                raise e
            df.append(raw_row)
        df = pd.DataFrame(df)
        df.columns = ['name'] + columns_slayers
        await asyncio.sleep(0)
        df = df.dropna()
        if df.empty:
            print('bad argument')
            raise commands.BadArgument

        return df


    async def get_slayer_avg(self,name):
        df = await self.get_slayer_df(name)
        df['mean'] = df.mean(axis=1)
        mean = df['mean'].mean()
        await asyncio.sleep(0)
        return round(mean,2)

    async def get_max_slayer(self,name):
        columns_slayers = ['zombie', 'spider',
                        'wolf']

        df = await self.get_slayer_df(name)
        data_max_slayer = []
        for i in columns_slayers:
            tmp_df = df[['name',i]]
            tmp_df = tmp_df.nlargest(3, [i])
            tmp_df[i] = tmp_df[i].round(decimals=0).apply(int)
            data_max_slayer.append(tmp_df)
        await asyncio.sleep(0)
        return data_max_slayer




    async def get_max_dungeons(self,name):
        columns_dungeons = ['experience_cata','healer','mage','berserk','archer','tank']

        df = await self.get_cata_df(name)
        data_max_dungeons = []
        for i in columns_dungeons:
            tmp_df = df[['name',i]]
            tmp_df = tmp_df.nlargest(3, [i])
            tmp_df[i] = tmp_df[i].round(decimals=0).apply(self.calculate_cata)
            data_max_dungeons.append(tmp_df)
        await asyncio.sleep(0)
        print(data_max_dungeons[0])
        return data_max_dungeons

    async def get_cata_df(self, name):
        items = await self.get_guild(name)
        df = []
        columns_dungeons = ['experience_cata','healer','mage','berserk','archer','tank']
        for i in items['members']:
            player = Database.find_one('members', {'_id': i})
            try:
                raw_row = [player['name']] + [player['dungeons'][j] for j in columns_dungeons] + [self.calculate_cata(player['dungeons']['experience_cata'])] 
            except Exception as e:
                raise e
            df.append(raw_row)
        df = pd.DataFrame(df)
        df.columns = ['name'] + columns_dungeons + ['lvl_cata']
        await asyncio.sleep(0)
        df = df.dropna()
        if df.empty:
            raise commands.BadArgument
        return df



    async def get_cata_avg(self,name):
        df = await self.get_cata_df(name)
        df = df[['name','lvl_cata']]
        df['mean'] = df.mean(axis=1)
        mean = df['mean'].mean()
        await asyncio.sleep(0)
        return round(mean,2)


    @staticmethod
    def calculate_lvl(xp,max_lvl=60):
        if(xp is None):
            return(None)
        xp_cumsum = [0, 175,   375,     675,   1175,   1925, 2925,    4425,    6425,    9925,
                14925,  22425, 32425,  47425, 67425,  97425,   147425, 222425, 322425, 522425,   822425,
                1222425,  1722425,   2322425, 3022425, 3822425, 4722425, 5722425, 6822425, 8022425, 9322425, 10722425,
                12222425, 13822425, 15522425, 17322425, 19222425, 21222425, 23322425, 25522425, 27822425, 30222425, 32722425,
                35322425, 38022425, 40772425, 43672425,  46772425,  50172425, 53872425,  57872425, 62172425,  66772425, 71672425,
                76872425, 82372425, 88172425, 94272425, 100672425, 107372425, 114372425]

        return(min(max_lvl,(sum([xp>i for i in xp_cumsum]))))
    @staticmethod
    def calculate_slayer(xp,monster):
        if(xp is None):
            return(None)
        if(monster=='zombie'):
            xp_cumsum = [5 ,     20 ,    220 ,   1220,    6220   ,26220  ,126220,  526220, 1526220]
        if(monster=='spider'):
            xp_cumsum = [10 ,     35 ,    235 ,   1235,    6235   ,26235 , 126235 , 526235, 1526235]
        if(monster=='wolf'):
            xp_cumsum = [10  ,    40  ,   290  ,  1790 ,   6790   ,26790,  126790,  526790, 1526790]

        return(min(9,(sum([xp>i for i in xp_cumsum]))))

    @staticmethod
    def calculate_cata(xp):
        if(xp is None):
            return(None)
        xp_cumsum = [50,  125,  235,  395,  625,  955, 1425,
                     2095,  3045,  4385,  6275,  8940, 12700, 17960,
                     25340,  35640,  50040,  70040,  97640, 135640, 188140,
                     259640, 356640,  488640,  668640,  911640, 1239640, 1684640,
                     2284640, 2364640,  3429640,  4839640,  6739640,  9239640, 12539640,
                     16839640, 22439640,  29639640,  38839640,  50839640,  65839640,  84839640,
                     108839640, 138839640]
        return(sum([xp>i for i in xp_cumsum]))


    async def get_skill_df_raw(self, name):

        columns_skills = ['experience_skill_combat', 'experience_skill_mining',
                        'experience_skill_farming', 'experience_skill_enchanting','experience_skill_alchemy', 'experience_skill_fishing','experience_skill_foraging', 'experience_skill_taming']


        items = await self.get_guild(name)
        df = []
        for i in items['members']:
            player = Database.find_one('members', {'_id': i})
            try:
                raw_row = [player['name']] + [player['skills'][j] for j in columns_skills]
            except Exception as e:
                raise e
            
            df.append(raw_row)
        df = pd.DataFrame(df)
        df.columns = ['name'] + columns_skills
        df = df.dropna()
        if df.empty:
            raise commands.BadArgument

        return df

    async def get_max_skills(self,name):
        df = await self.get_skill_df_raw(name)
        columns_skills = ['experience_skill_combat', 'experience_skill_mining',
                        'experience_skill_farming', 'experience_skill_enchanting','experience_skill_alchemy', 'experience_skill_fishing','experience_skill_foraging', 'experience_skill_taming']
        columns_skills60 = ['experience_skill_combat', 'experience_skill_mining',
                        'experience_skill_farming', 'experience_skill_enchanting']

        columns_skills50 = ['experience_skill_alchemy', 'experience_skill_fishing','experience_skill_foraging', 'experience_skill_taming']
        data_max = []
        for i in columns_skills:
            tmp_df = df[['name',i]]
            tmp_df = tmp_df.nlargest(3, [i])

            if i in columns_skills50:
                tmp_df[i] = tmp_df[i].apply(self.calculate_lvl,args=(50,))
            else:
                tmp_df[i] = tmp_df[i].apply(self.calculate_lvl,args=(60,))
            data_max.append(tmp_df)
        await asyncio.sleep(0)
        return data_max


    async def get_dungeon_times_df(self, name):
        items = await self.get_guild(name)
        df = []
        for i in items['members']:
            player = Database.find_one('members', {'_id': i})
            try:
                raw_row = [player['name']] + [player['dungeons']['fastest_time'][str(j)] for j in range(0,8)]
            except Exception as e:
                raise e
            df.append(raw_row)
        df = pd.DataFrame(df)
        df.columns = ['name'] + [str(i) for i in range(0,8)]
        await asyncio.sleep(0)
        return df.dropna()

    async def get_dungeons_fastest_time(self,name):
        df = await self.get_dungeon_times_df(name)
        data_max = []

        def convert(millis):
            millis = int(millis)
            seconds=(millis/1000)%60
            seconds = int(seconds)
            minutes=(millis/(1000*60))%60
            minutes = int(minutes)
            mil = millis%1000

            strw = f"{minutes}:{seconds}:{mil}"
            def add_zeros(item: str) -> str:
                nums = item.split(":")
                formatted_item = ":".join(f"{int(num):02d}" for num in nums)
                return formatted_item

            return(add_zeros(strw))

        for i in range(0,8):
            tmp_df = df[['name',str(i)]]
            tmp_df = tmp_df.nsmallest(3, [str(i)])
            tmp_df[str(i)] = tmp_df[str(i)].apply(convert)
            data_max.append(tmp_df)

        return(data_max)

    @staticmethod
    def tuple_sort(my_tuple):
        return(sorted(my_tuple, key = lambda x: x[2],reverse=True))

    @staticmethod
    def styledf(df):
        x = df.to_string(header=False,
                        index=False,
                        index_names=False).split('\n')
        vals = [': '.join(ele.split()) for ele in x]
        return ('\n\u200b'.join(vals))

def setup(bot):
    bot.add_cog(Stat(bot))
