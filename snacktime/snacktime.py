import discord
from discord.ext import commands
from random import randint
from random import choice as randchoice
import datetime
import time
import os
import asyncio
from copy import deepcopy
from __main__ import send_cmd_help
from .utils.dataIO import fileIO, dataIO
from .utils import checks


CUSTOM_DIR = "data/snacktime/custom_messages"

DEFAULT_FRIENDS = [
    "Pancakes",
    "Mr Pickles",
    "Satin",
    "Thunky",
    "Jingle",
    "FluffButt",
    "Urahorse",
    "Staplefoot"
]

PHRASE_FILES = {
    "SNACKTIME":   "start.txt",
    "OUT":         "stop.txt",
    "LONELY":      "lonely.txt",
    "NO_TAKERS":   "no_takers.txt",
    "GIVE":        "give.txt",
    "LAST_SECOND": "last_second.txt",
    "GREEDY":      "greedy.txt",
    "NO_BANK":     "no_bank.txt",
    "ENABLE":      "enable.txt",
    "DISABLE":     "disable.txt"
}

SNACKBURR_PHRASES = {
    "SNACKTIME": [
        "`ʕ •ᴥ•ʔ < It's snack time!`",
        "`ʕ •ᴥ•ʔ < I'm back with s'more snacks! Who wants!?`",
        "`ʕ •ᴥ•ʔ < I'm back errbody! Who wants some snacks!?`",
        "`ʕ •ᴥ•ʔ < Woo man those errands are crazy! Anyways, anybody want some snacks?`",
        "`ʕ •ᴥ•ʔ < I got snacks! If nobody wants em, I'm gonna eat em all!!`",
        "`ʕ •ᴥ•ʔ < Hey, I'm back! Anybody in the mood for some snacks?!`",
        "`ʕ •ᴥ•ʔ < Heyyaaayayyyaya! I say Hey, I got snacks!`",
        "`ʕ •ᴥ•ʔ < Heyyaaayayyyaya! I say Hey, What's goin on?... I uh.. I got snacks.`",
        "`ʕ •ᴥ•ʔ < If anybody has reason why these snacks and my belly should not be wed, speak now or forever hold your peace!`",
        "`ʕ •ᴥ•ʔ < Got another snack delivery guys!`",
        "`ʕ •ᴥ•ʔ < Did somebody say snacks?!?! o/`",
        "`ʕ •ᴥ•ʔ < Choo Choo! it's the pb train! Come on over guys!`",
        "`ʕ •ᴥ•ʔ < Snacks are here! Dig in! Who wants a plate?`",
        "`ʕ >ᴥ>ʔ < Pstt.. I got the snacks you were lookin for. <.<`",
        "`ʕ •ᴥ•ʔ < I hope you guys are hungry! Cause i'm loaded to the brim with snacks!!!`",
        "`ʕ •ᴥ•ʔ < I was hungry on the way over so I kinda started without you guys :3 Who wants snacks!?!`",
        "`ʕ •ᴥ•ʔ < Beep beep! I got a snack delivery comin in! Who wants snacks!`",
        "`ʕ •ᴥ•ʔ < Guess what time it is?! It's snacktime!! Who wants?!`",
        "`ʕ •ᴥ•ʔ < Hey check out this sweet stach o' snacks I found! Who wants a cut?`",
        "`ʕ •ᴥ•ʔ < Who's ready to gobble down some snacks!?`",
        "`ʕ •ᴥ•ʔ < So who's gonna help me eat all these snacks? :3`"
    ],
    "OUT": [
        "`ʕ •ᴥ•ʔ < I'm out of snacks! I'll be back with more soon.`",
        "`ʕ •ᴥ•ʔ < I'm out of snacks :( I'll be back soon with more!`",
        "`ʕ •ᴥ•ʔ < Aight, I gotta head out! I'll be back with more, don worry :3`",
        "`ʕ •ᴥ•ʔ < Alright, I gotta get back to my errands. I'll see you guys soon!`"
    ],
    "LONELY": [
        "`ʕ •ᴥ•ʔ < I guess you guys don't like snacktimes.. I'll stop comin around.`"
    ],
    "NO_TAKERS": [
        "`ʕ •ᴥ•ʔ < I guess nobody wants snacks... more for me!`",
        "`ʕ •ᴥ•ʔ < Guess nobody's here.. I'll just head out then`",
        "`ʕ •ᴥ•ʔ < I don't see anybody.. <.< ... >.> ... All the snacks for me!!`",
        "`ʕ •ᴥ•ʔ < I guess nobody wants snacks huh.. Well, I'll come back later`",
        "`ʕ •ᴥ•ʔ < I guess i'll just come back later..`"
    ],
    "GIVE": [
        "`ʕ •ᴥ•ʔ < Here ya go, {0}, here's {1} pb!`",
        "`ʕ •ᴥ•ʔ < Alright here ya go, {0}, {1} pb for you!`",
        "`ʕ •ᴥ•ʔ < Yeah! Here you go, {0}! {1} pb!`",
        "`ʕ •ᴥ•ʔ < Of course {0}! Here's {1} pb!`",
        "`ʕ •ᴥ•ʔ < Ok {0}, here's {1} pb for you. Anyone else want some?`",
        "`ʕ •ᴥ•ʔ < Alllright, {1} pb for {0}!`",
        "`ʕ •ᴥ•ʔ < Hold your horses {0}! Alright, {1} pb for you :)`"
    ],
    "LAST_SECOND": [
        "`ʕ •ᴥ•ʔ < Fine fine, {0}, I'll give you {1} of my on-the-road pb.. Cya!`",
        "`ʕ •ᴥ•ʔ < Oh! {0}, you caught me right before I left! Alright, i'll give you {1} of my own pb`"
    ],
    "GREEDY": [
        "`ʕ •ᴥ•ʔ < Don't be greedy now! you already got some pb {0}!`",
        "`ʕ •ᴥ•ʔ < You already got your snacks {0}!`",
        "`ʕ •ᴥ•ʔ < Come on {0}, you already got your snacks! We gotta make sure there's some for errbody!`"
    ],
    "NO_BANK": [
        "`ʕ •ᴥ•ʔ < You don't have a pb bank account, {0}! But here ya go, you can just eat these {1} pb jars!`",
        "`ʕ •ᴥ•ʔ < Dang, {0}! You don't have a pb bank account. Are you just gonna eat these {1} pb jars?!`",
        "`ʕ •ᴥ•ʔ < {0}, you don't really have a place to put these {1} pb jars, but I'll give em to you to eat here n now :)`"
    ],
    "ENABLE": [
        "`ʕ •ᴥ•ʔ < Oh you guys want snacks?! Aight, I'll come around every so often to hand some out!`"
    ],
    "DISABLE": [
        "`ʕ •ᴥ•ʔ < You guys don't want snacks anymore? Alright, I'll stop comin around.`"
    ]
}


DEFAULT_SETTINGS = {"FRIENDS": False, "EVENT_START_DELAY": 1800,
                    "EVENT_START_DELAY_VARIANCE": 900, "SNACK_DURATION": 240,
                    "SNACK_DURATION_VARIANCE": 120, "MSGS_BEFORE_EVENT": 8,
                    "SNACK_AMOUNT": 200}


def ensure_friend_file_structure():
    for friend_name in os.listdir(CUSTOM_DIR):
        if friend_name == 'snackburr':
            continue
        friend_path = os.path.join(CUSTOM_DIR, friend_name)
        for phrase_file in PHRASE_FILES.values():
            phrase_path = os.path.join(friend_path, phrase_file)
            if not os.path.exists(phrase_path):
                open(phrase_path, 'a').close()


def load_customs():
    """
    {
        "Pancakes": {
            "SNACKTIME": ['a', 'b', 'c'],
            "OUT"...
        }
    }
    """
    ensure_friend_file_structure()
    customs = {name: {} for name in os.listdir(CUSTOM_DIR)}
    for friend_name in os.listdir(CUSTOM_DIR):  # go through all friend dirs
        friend_path = os.path.join(CUSTOM_DIR, friend_name)

        for phrase_group, phrase_file in PHRASE_FILES.items():  # each phrase file
            phrase_path = os.path.join(friend_path, phrase_file)

            with open(phrase_path) as f:
                li = [line.strip() for line in f if line.strip()]
                if not li:  # if a phrase file doesn't exist, remove friend
                    del customs[friend_name]
                    break
                customs[friend_name][phrase_group] = li
    return customs


class Snacktime:
    """The Snackburr's passing out pb jars!

    Snackburr has some friends now! Invite them to the party by
    adding messages to the files in data/snacktime/custom_messages!
    """

    def __init__(self,bot):
        self.bot = bot
        try:
            self.loop = asyncio.get_event_loop()
        except:
            self.loop = None
        self.econ = None
        #self.msgTime = None
        self.snackSchedule = {}
        self.snacktimePrediction = {}
        self.previousSpeaker = {}
        self.snackInProgress = {}
        self.acceptInput = {}
        self.alreadySnacked = {}
        self.msgsPassed = {}
        self.startLock = {}
        self.snacktimeCheckLock = {}
        self.lockRequests = {}
        self.repeatMissedSnacktimes = fileIO("data/snacktime/repeatMissedSnacktimes.json", "load")
        self.channels = fileIO("data/snacktime/channels.json", "load")
        self.settings = fileIO("data/snacktime/settings.json", "load")
        self.phrases = self.update_phrases()
        self.channel_persona = {}

    #TODO:
    #   o - Make deliver channel-based instead of server
    #    - channel or server-specific settings
    #    - link economy
    #    - make sure to try/except messages if needed
    #    - more phrases. can use {0} in the strings i think
    #    - adjust/think through timing
    #    - other commands?
    #    - how much to give? random sometimes? from a pot? same throughout? link type to startPhrases? put in startSnack as a different event
    #    - status affects, stickerburr
    #   o - x# msgs must have been sent before start snacktime - setting

    async def ready_up(self):
        self.loop = asyncio.get_event_loop()

    def persona_choice(self, msg):
        scid = msg.server.id+"-"+msg.channel.id
        invite_friends = self.settings[scid]["FRIENDS"]
        personas = set(self.phrases)
        if not invite_friends:
            return "snackburr"
        elif invite_friends is True:
            personas.remove("snackburr")
        return randchoice(personas)

    async def get_response(self, msg, phrase_type):
        scid = msg.server.id+"-"+msg.channel.id
        persona = self.channel_persona[scid]
        phrases = self.phrases[persona]
        return randchoice(phrases[phrase_type])

    def update_phrases(self):
        phrases = load_customs()
        phrases['snackburr'] = SNACKBURR_PHRASES
        return phrases

    @commands.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_server=True)
    async def snackset(self, ctx):
        """snack stuff"""
        scid = ctx.message.server.id+"-"+ctx.message.channel.id
        if self.settings.get(scid, None) == None:
            self.settings[scid] = deepcopy(DEFAULT_SETTINGS)
            fileIO("data/snacktime/settings.json", "save", self.settings)
        if ctx.invoked_subcommand is None:
            msg = "```"
            for k, v in self.settings[scid].items():
                msg += str(k) + ": " + str(v) + "\n"
            msg += "DELIVER_HERE " + str(scid in self.channels.keys()) + "\n"
            msg += "```\nType help snackset to see the list of commands."
            await self.bot.say(msg)

    @snackset.command(pass_context=True)
    async def errandtime(self, ctx, seconds: int):
        """How long snackburr needs to be out doin errands.. more or less."""
        scid = ctx.message.server.id+"-"+ctx.message.channel.id
        if seconds <= self.settings[scid]["EVENT_START_DELAY_VARIANCE"]:
            await self.bot.say("errandtime must be greater than errandvariance!")
        elif seconds <= 0:
            await self.bot.say("errandtime must be greater than 0")
        else:
            self.settings[scid]["EVENT_START_DELAY"] = seconds
            await self.bot.say("snackburr's errands will now take around " + str(self.settings[scid]["EVENT_START_DELAY"]/60) + " minutes!")
            fileIO("data/snacktime/settings.json", "save", self.settings)

    @snackset.command(pass_context=True)
    async def errandvariance(self, ctx, seconds: int):
        """How early or late snackburr might be to snacktime"""
        scid = ctx.message.server.id+"-"+ctx.message.channel.id
        if seconds >= self.settings[scid]["EVENT_START_DELAY"]:
            await self.bot.say("errandvariance must be less than errandtime!")
        elif seconds < 0:
            await self.bot.say("errandvariance must be 0 or greater!")
        else:
            self.settings[scid]["EVENT_START_DELAY_VARIANCE"] = seconds
            await self.bot.say("snackburr now might be " + str(self.settings[scid]["EVENT_START_DELAY_VARIANCE"]/60) + " minutes early or late to snacktime")
            fileIO("data/snacktime/settings.json", "save", self.settings)

    @snackset.command(name="snacktime", pass_context=True)
    async def snacktimetime(self, ctx, seconds: int):
        """How long snackburr will hang out giving out snacks!.. more or less."""
        scid = ctx.message.server.id+"-"+ctx.message.channel.id
        if seconds <= self.settings[scid]["SNACK_DURATION_VARIANCE"]:
            await self.bot.say("snacktime must be greater than snackvariance!")
        elif seconds <= 0:
            await self.bot.say("snacktime must be greater than 0")
        else:
            self.settings[scid]["SNACK_DURATION"] = seconds
            await self.bot.say("snacktimes will now last around " + str(self.settings[scid]["SNACK_DURATION"]/60) + " minutes!")
            fileIO("data/snacktime/settings.json", "save", self.settings)

    @snackset.command(name="snackvariance", pass_context=True)
    async def snacktimevariance(self, ctx, seconds: int):
        """How early or late snackburr might have to leave for errands"""
        scid = ctx.message.server.id+"-"+ctx.message.channel.id
        if seconds >= self.settings[scid]["SNACK_DURATION"]:
            await self.bot.say("snackvariance must be less than snacktime!")
        elif seconds < 0:
            await self.bot.say("snackvariance must be 0 or greater!")
        else:
            self.settings[scid]["SNACK_DURATION_VARIANCE"] = seconds
            await self.bot.say("snackburr now may have to leave snacktime " + str(self.settings[scid]["SNACK_DURATION_VARIANCE"]/60) + " minutes early or late")
            fileIO("data/snacktime/settings.json", "save", self.settings)

    @snackset.command(pass_context=True)
    async def msgsneeded(self, ctx, amt: int):
        """How many messages must pass in a conversation before a snacktime can start"""
        scid = ctx.message.server.id+"-"+ctx.message.channel.id
        if amt <= 0:
            await self.bot.say("msgsneeded must be greater than 0")
        else:
            self.settings[scid]["MSGS_BEFORE_EVENT"] = amt
            await self.bot.say("snackburr will now wait until " + str(self.settings[scid]["MSGS_BEFORE_EVENT"]) + " messages pass until he comes with snacks")
            fileIO("data/snacktime/settings.json", "save", self.settings)

    @snackset.command(pass_context=True)
    async def amount(self, ctx, amt: int):
        """How much pb max snackburr should give out to each person per snacktime"""
        scid = ctx.message.server.id+"-"+ctx.message.channel.id
        if amt <= 0:
            await self.bot.say("amount must be greater than 0")
        else:
            self.settings[scid]["SNACK_AMOUNT"] = amt
            await self.bot.say("snackburr will now give out " + str(self.settings[scid]["SNACK_AMOUNT"]) + " pb max per person per snacktime.")
            fileIO("data/snacktime/settings.json", "save", self.settings)

    @snackset.command(pass_context=True, name="friends")
    async def snackset_friends(self, ctx, choice: int):
        """snackburr's friends wanna know what all the hub-bub's about!

        Do you want to 
        1: invite them to the party, 
        2: only allow snackburr to chillax with you guys, or 
        3: kick snackburr out on the curb in favor of his obviously cooler friends?

        *Invite them to the party by adding friend folders
        and messages to the files in data/snacktime/custom_messages/FRIEND_NAME!
        There should alread be a blank friend folder there for you as an example.

        Each line counts as a message

        You can use {0} in last_second, give, no_bank, and greedy 
        to refer to the snacker
        You can use {1} in last_second, give, and no_bank 
        to specify snack amount"""
        server = ctx.message.server
        channel = ctx.message.channel
        author = ctx.message.author

        self.customs = load_customs()
        if choice not in (1, 2, 3) or not self.customs:
            return await send_cmd_help(ctx)

        scid = ctx.message.server.id+"-"+ctx.message.channel.id

        # TODO: only use one persona per snacktime
        # DONE: allow multiple custom personas by using subdirectories
        # TODO: Write snackburr's text to file as an example

        choices = {
            1: ("both", "Everybody's invited!"),
            2: (False, "You chose to not invite snackburr's friends"),
            3: (True, "You kick snackburr out in favor of "
                      "his friends! Ouch. Harsh..")
        }
        choice = choices[choice]

        settings = self.settings[scid]
        settings["FRIENDS"] = choice[0]
        await self.bot.say(choice[1])
        dataIO("data/snacktime/settings.json", self.settings)

    @snackset.command(pass_context=True)
    async def deliver(self, ctx):
        """Asks snackburr to start delivering to this channel"""
        scid = ctx.message.server.id+"-"+ctx.message.channel.id
        if scid not in self.channels.keys():
            self.channels[scid] = False
        self.channels[scid] = not self.channels[scid]
        fileIO("data/snacktime/channels.json", "save", self.channels)
        if self.channels[scid]:
            await self.bot.say(self.get_response(ctx.message, "ENABLE"))
        else:
            await self.bot.say(self.get_response(ctx.message, "DISABLE"))

    @commands.command(pass_context=True)
    async def snacktime(self, ctx):
        """Man i'm hungry! When's snackburr gonna get back with more snacks?"""
        scid = ctx.message.server.id+"-"+ctx.message.channel.id
        if self.snacktimePrediction.get(scid,None) == None:
            if self.acceptInput.get(scid,False):
                return
            else:
                phrases = ["Don't look at me. I donno where snackburr's at ¯\_(ツ)_/¯","I hear snackburr likes parties. *wink wink","I hear snackburr is attracted to channels with active conversations","If you party, snackburr will come! 〈( ^o^)ノ"]
                await self.bot.say(randchoice(phrases))
            return
        seconds = self.snacktimePrediction[scid] - self.loop.time()
        if self.snacktimeCheckLock.get(scid,False):
            if randint(1,4) == 4:
                await self.bot.say("Hey, snackburr's on errands. I ain't his keeper Kappa")
            return
        self.snacktimeCheckLock[scid] = True
        if seconds < 0:
            await self.bot.say("I'm not sure where snackburr is.. He's already "+ str(-int(seconds/60)) + " minutes late!")
        else:
            await self.bot.say("snackburr's out on errands! I think he'll be back in " + str(int(seconds/60)) + " minutes")
        await asyncio.sleep(40)
        self.snacktimeCheckLock[scid] = False

    async def startSnack(self, message):
        scid = message.server.id+"-"+message.channel.id
        if self.acceptInput.get(scid,False):
            return
        self.phrases = self.update_phrases()
        self.channel_persona[scid] = self.persona_choice(message)
        await self.bot.send_message(message.channel, self.get_response(message, "SNACKTIME"))
        #set econ here? don't need to unset it.
        self.econ = self.bot.get_cog('Economy')
        self.acceptInput[scid] = True
        self.alreadySnacked[scid] = []
        duration = self.settings[scid]["SNACK_DURATION"] + randint(-self.settings[scid]["SNACK_DURATION_VARIANCE"], self.settings[scid]["SNACK_DURATION_VARIANCE"])
        await asyncio.sleep(duration)
        #sometimes fails sending messages and stops all future snacktimes. Hopefully this fixes it.
        try:
            #list isn't empty
            if self.alreadySnacked.get(scid,False):
                await self.bot.send_message(message.channel, self.get_response(message, "OUT"))
                self.repeatMissedSnacktimes[scid] = 0
                fileIO("data/snacktime/repeatMissedSnacktimes.json", "save", self.repeatMissedSnacktimes)
            else:
                await self.bot.send_message(message.channel, self.get_response(message, "NO_TAKERS"))
                self.repeatMissedSnacktimes[scid] = self.repeatMissedSnacktimes.get(scid,0) + 1
                await asyncio.sleep(2)
                if self.repeatMissedSnacktimes[scid] > 9: #move to a setting
                    await self.bot.send_message(message.channel, self.get_response(message, "LONELY"))
                    self.channels[scid] = False
                    fileIO("data/snacktime/channels.json", "save", self.channels)
                    self.repeatMissedSnacktimes[scid] = 0
                fileIO("data/snacktime/repeatMissedSnacktimes.json", "save", self.repeatMissedSnacktimes)

        except:
            print("Failed to send message")
        self.acceptInput[scid] = False
        self.snackInProgress[scid] = False

    async def check_messages(self, message):
        #no pms
        if message.server == None:
            return
        scid = message.server.id+"-"+message.channel.id
        if not self.channels.get(scid,False):
            return
        if self.loop == None:
            try:
                self.loop = asyncio.get_event_loop()
            except:
                print("Error: Not able to get event loop")
                return

        if message.author.id != self.bot.user.id:
            self.econ = self.bot.get_cog('Economy')
            #if nobody has said anything since start
            if self.previousSpeaker.get(scid,None) == None:
                self.previousSpeaker[scid] = message.author.id
            #if new speaker
            elif self.previousSpeaker[scid] != message.author.id:
                self.previousSpeaker[scid] = message.author.id
                msgTime = self.loop.time()
                #if there's a scheduled snack
                if self.snackSchedule.get(scid,None) != None:
                    #if it's time for a snack
                    if msgTime > self.snackSchedule[scid]:
                        #1 schedule at a time, so remove schedule
                        self.snackSchedule[scid] = None
                        self.snackInProgress[scid] = True

                        #wait to make it more natural
                        naturalWait = randint(30,240)
                        print("snack trigger msg: " + message.content)
                        print("Waiting " + str(naturalWait) + " seconds")
                        await asyncio.sleep(naturalWait)
                        #start snacktime
                        await self.startSnack(message)
                #if no snack coming, schedule one
                elif self.snackInProgress.get(scid,False) == False and not self.startLock.get(scid,False):
                    self.msgsPassed[scid] = self.msgsPassed.get(scid,0) + 1
                    #check for collisions
                    if self.msgsPassed[scid] > self.settings[scid]["MSGS_BEFORE_EVENT"]:
                        self.startLock[scid] = True
                        if self.lockRequests.get(scid,None) == None:
                            self.lockRequests[scid] = []
                        self.lockRequests[scid].append(message)
                        await asyncio.sleep(1)
                        print(":-+-|||||-+-: Lock request: " + str(self.lockRequests[scid][0] == message))
                        if self.lockRequests[scid][0] == message:
                            await asyncio.sleep(5)
                            print(message.author.name + " I got the Lock")
                            self.lockRequests[scid] = []
                            #someone got through already
                            if self.msgsPassed[scid] < self.settings[scid]["MSGS_BEFORE_EVENT"] or self.snackInProgress.get(scid,False):
                                print("Lock: someone got through already.")
                                return
                            else:
                                print("Lock: looks like i'm in the clear. lifting lock. If someone comes now, they should get the lock")
                                self.msgsPassed[scid] = self.settings[scid]["MSGS_BEFORE_EVENT"]
                                self.startLock[scid] = False
                        else:
                            print(message.author.name + " Failed lock")
                            return
                    if self.msgsPassed[scid] == self.settings[scid]["MSGS_BEFORE_EVENT"]:
                        #schedule a snack
                        print("activity: " + message.content)
                        timeTillSnack = self.settings[scid]["EVENT_START_DELAY"] + randint(-self.settings[scid]["EVENT_START_DELAY_VARIANCE"], self.settings[scid]["EVENT_START_DELAY_VARIANCE"])
                        print(str(timeTillSnack) + " seconds till snacktime")
                        self.snacktimePrediction[scid] = msgTime + self.settings[scid]["EVENT_START_DELAY"]
                        self.snackSchedule[scid] = msgTime + timeTillSnack
                        self.msgsPassed[scid] = 0

            #it's snacktime! who want's snacks?
            if self.acceptInput.get(scid,False):
                if message.author.id not in self.alreadySnacked.get(scid,[]):
                    agree_phrases = ["holds out hand","im ready","i'm ready","hit me up","hand over","hand me","kindly","i want","i'll have","ill have","yes","pls","plz","please","por favor","can i","i'd like","i would","may i","in my mouth","in my belly","snack me","gimme","give me","i'll take","ill take","i am","about me","me too","of course"]
                    userWants = False
                    for agreePhrase in agree_phrases:
                        #no one word answers
                        if agreePhrase in message.content.lower() and len(message.content.split()) > 1:
                            userWants = True
                            break
                    if userWants:
                        if self.alreadySnacked.get(scid,None) == None:
                            self.alreadySnacked[scid] = []
                        self.alreadySnacked[scid].append(message.author.id)
                        await asyncio.sleep(randint(1,6))
                        snackAmt = randint(1,self.settings[scid]["SNACK_AMOUNT"])
                        if self.econ.bank.account_exists(message.author):
                            try:
                                if self.acceptInput.get(scid,False):
                                    await self.bot.send_message(message.channel, self.get_response(message, "GIVE").format(message.author.name,snackAmt))
                                else:
                                    await self.bot.send_message(message.channel, self.get_response(message, "LAST_SECOND").format(message.author.name,snackAmt))
                                self.econ.bank.deposit_credits(message.author, snackAmt)
                            except:
                                print("Failed to send message. " + message.author.name + " didn't get pb")

                        else:
                            await self.bot.send_message(message.channel, self.get_response(message, "NO_BANK").format(message.author.name,snackAmt))

                else:
                    more_phrases = ["more pl","i have some more","i want more","i have another","i have more","more snack"]
                    userWants = False
                    for morePhrase in more_phrases:
                        if morePhrase in message.content.lower():
                            userWants = True
                            break
                    if userWants:
                        await asyncio.sleep(randint(1,6))
                        if self.acceptInput.get(scid,False):
                            await self.bot.send_message(message.channel, self.get_response(message, "GREEDY").format(message.author.name))


def check_folders():
    if not os.path.exists("data/snacktime"):
        print("Creating data/snacktime folder...")
        os.makedirs("data/snacktime")
    if not os.path.exists(CUSTOM_DIR):
        print("Creating {} folder...".format(CUSTOM_DIR))
        os.makedirs(CUSTOM_DIR)
    if not os.listdir(CUSTOM_DIR):
        friend_dir = os.path.join(CUSTOM_DIR, randchoice(DEFAULT_FRIENDS))
        print("Creating {} folder... (a default friend)".format(friend_dir))
        os.makedirs(friend_dir)


def check_files():

    f = "data/snacktime/settings.json"
    if not fileIO(f, "check"):
        print("Creating empty snacktime's settings.json...")
        fileIO(f, "save", {})

    f = "data/snacktime/channels.json"
    if not fileIO(f, "check"):
        print("Creating empty snacktime's channels.json...")
        fileIO(f, "save", {})

    f = "data/snacktime/repeatMissedSnacktimes.json"
    if not fileIO(f, "check"):
        print("Creating empty snacktime's repeatMissedSnacktimes.json...")
        fileIO(f, "save", {})

    ensure_friend_file_structure()

    settings = dataIO.load_json(f)
    dirty = False
    for unit_settings in settings.values():  # consistency check
        missing_keys = set(DEFAULT_SETTINGS) - set(unit_settings)
        fill = {k: DEFAULT_SETTINGS[k] for k in missing_keys}
        unit_settings.update(fill)
        if missing_keys:
            dirty = True

    if dirty:
        dataIO.save_json(f, settings)


def setup(bot):
    check_folders()
    check_files()
    n = Snacktime(bot)
    bot.add_listener(n.ready_up, "on_ready")
    bot.add_listener(n.check_messages, "on_message")
    bot.add_cog(n)
