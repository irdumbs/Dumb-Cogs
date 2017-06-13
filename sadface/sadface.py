import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils import checks
import os
import aiohttp

# if this seem hard to read/understand, remove the comments. Might make it easier

class Sadface:
    """D:"""

    def __init__(self,bot):
        self.bot = bot
        self.url = "https://cdn.betterttv.net/emote/55028cd2135896936880fdd7/1x"
        self.sadLoaded = os.path.exists('data/sadface/sadface.png')
        self.image = "data/sadface/sadface.png"
        self.servers = dataIO.load_json("data/sadface/servers.json")

    # doesn't make sense to use this command in a pm, because pms aren't in servers
    # mod_or_permissions needs something in it otherwise it's mod or True which is always True
    @commands.command(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_roles=True)
    async def sadface(self, ctx):
        """Enables/Disables sadface for this server"""
        #default off.
        server = ctx.message.server
        if server.id not in self.servers:
            self.servers[server.id] = False
        else:
            self.servers[server.id] = not self.servers[server.id]
        #for a toggle, settings should save here in case bot fails to send message
        dataIO.save_json("data/sadface/servers.json", self.servers)
        if self.servers[server.id]:
            await self.bot.say("Sadface on. Please turn this off in the Red - DiscordBot server. This is only an example cog.")
        else:
            await self.bot.say("Sadface off.")

    async def check_sad(self, message):
        # check if setting is on in this server
        #let sadfaces happen in PMs always
        server = message.server
        if server != None:
            if server.id not in self.servers:
                #default off
                self.servers[server.id] = False
            # sadface is off, so ignore
            if not self.servers[server.id]:
                return

        # comments explaining next section. seemed easier to read this way
        # check for a phrase in message
        #   if sadface isn't downloaded yet, dl it
        #       try
        #           get image from url
        #           write image to file
        #           it worked \o/
        #           send it
        #       except
        #           there was a problem, print an error then try to send the url instead
        #   else sadface image already downloaded, send it

        if "D:" in message.content.split():
            if not self.sadLoaded:
                try:
                    async with aiohttp.get(self.url) as r:
                        image = await r.content.read()
                    with open('data/sadface/sadface.png','wb') as f:
                        f.write(image)
                    self.sadLoaded = os.path.exists('data/sadface/sadface.png')
                    await self.bot.send_file(message.channel,self.image)
                except Exception as e:
                    print(e)
                    print("Sadface error D: I couldn't download the file, so we're gonna use the url instead")
                    await self.bot.send_message(message.channel,self.url)
            else:
                await self.bot.send_file(message.channel,self.image)

def check_folders():
    # create data/sadface if not there
    if not os.path.exists("data/sadface"):
        print("Creating data/sadface folder...")
        os.makedirs("data/sadface")

def check_files():
    # create server.json if not there
    # put in default values
    f = "data/sadface/servers.json"
    default = {}
    if not dataIO.is_valid_json(f):
        print("Creating default sadface servers.json...")
        dataIO.save_json(f, default)


def setup(bot):
    check_folders()
    check_files()
    n = Sadface(bot)
    # add an on_message listener
    bot.add_listener(n.check_sad, "on_message")
    bot.add_cog(n)
