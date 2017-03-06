# LOLspeak translator library
# Created by Stephen Newey
#
# Python stuff, copyright (c)2008 Stephen Newey
# Inspired by Dave Dribin's Ruby library lolspeak (http://www.dribin.org/dave/lolspeak/)
# tranzlator.yml dictionary by Dave Dribin
#
# python code licensed under the Mozilla Public License v1.1.
# http://www.mozilla.org/MPL/MPL-1.1.html
#
# downloaded from: https://code.google.com/archive/p/pylolz/

# Credit for idea/implementation: Will(@tekulvw) / Nikki(@cookiezeater) / Mash(@Canule) / irdumb(@irdumbs)


from discord.ext import commands
import discord.utils
from .utils.dataIO import fileIO, dataIO
import logging
import asyncio
import re
import os
from random import randint
from copy import deepcopy
from __main__ import settings


log = logging.getLogger(__name__)
request_logging_format = '{method} {response.url} has returned {response.status}'
request_success_log = '{response.url} with {json} received {data}'
mvs = '᠎'
nbs = '﻿'
LOLZ_PREFIX = nbs + mvs + nbs

default_settings = {"SERVER": {"DEFAULT": False}, "DM": {"DEFAULT" : False}}


class Lolz:
    """translates all text the bot speaks to lolcat"""

    # regex's edited from lolz
    def __init__(self, bot):
        self.bot = bot

        self.easy_regex = [
            (re.compile("(.*)ed$"), 'd'),
            (re.compile("(.*)ing$"), 'in'),
            (re.compile("(.*)ss$"), 's'),
            (re.compile("(.*)er$"), 'r'),
        ]

        # more complicated search/replace operations
        self.regex = {
            'apostrophy': re.compile('(?P<prefix>.*)(?P<suffix>[\']\w*)'),
            'tion': re.compile("(.*)tion(s?)$"),
            'stoz': re.compile("^([\w]+)s$"),
            'ous': re.compile("ous$"),
            'link': re.compile("https?://..")  # not the same as discord's
        }

        self.cached = {}
        self.settings = fileIO("data/lolz/settings.json", "load")
        self.tranzlashun = fileIO("data/lolz/tranzlashun.json", "load")

        self._monkeymanager = self.bot.loop.create_task(self.patcher())

        # object independant send_message. do not overwrite
        # self.old_send = commands.Bot.send_message
        # self.old_send = self.bot.send_message

    @commands.command(pass_context=True)
    async def lolz(self, ctx):
        """Toggle lolspeak for this server"""
        server = ctx.message.server
        key = "SERVER"
        if server is None or check_mod(ctx):
            if server is None:
                server = ctx.message.author
                key = "DM"
            if server.id not in self.settings[key]:
                self.settings[key][
                    server.id] = default_settings[key]["DEFAULT"]
            self.settings[key][
                server.id] = not self.settings[key][server.id]
            if self.settings[key][server.id]:
                await self.bot.say("I will now lolz sentences.")
            else:
                await self.bot.say("I won't lolz sentences anymore.")
        else:
            await self.bot.say("You don't have permission to touch the lolz.")
            return
        fileIO("data/lolz/settings.json", "save", self.settings)

    # This is bad. If you're reading this, you're probably trying to find out how it does what it does.
    # Please head to Red's #testing/#coding channels and ask for help from the contributors listed above
    # We do not recommend doing this. If multiple cogs start doing this, things will be very messy and very buggy
    # We do not have a standard/protocol yet on how to communicate these changes between cogs.
    # We will be very leery of doing so, as this is a BAD programming practice.
    # Again, speak to the contributors if you have questions. More notably, Will(@tekulvw)
    def send_lolz(self, old_send):
        async def predicate(destination, content=None, *args, **kwargs):

            embed = kwargs.get('embed', None)
            content = content and str(content)

            # replaced _resolve_destination. assume not getting Object
            chan_or_id = self.bot.get_channel(destination.id) or destination.id
            # channel should be PrivateChannel, Channel, or id here.
            if self.can_lolz(chan_or_id):
                content, embed = self.translate_message(content, embed)

            # msg = await old_send(self.bot, destination, content, *args,
            # **kwargs)
            msg = await old_send(destination, content, *args, **kwargs)
            return msg

        predicate.old = old_send
        return predicate

    def edit_lolz(self, old_edit):
        async def predicate(message, new_content=None, *args, **kwargs):
            embed = kwargs.get('embed', None)
            content = new_content and str(new_content)

            chan_or_id = message.channel or message.author.id

            if self.can_lolz(chan_or_id):
                content, embed = self.translate_message(content, embed)

            msg = await old_edit(message, content, *args, **kwargs)
            return msg

        predicate.old = old_edit
        return predicate

    def can_lolz(self, chan_or_id):
        # channel should be PrivateChannel, Channel, or id.
        if isinstance(chan_or_id, str):
            return self.settings["DM"].get(chan_or_id, False)

        # if no is_private, it should be private.
        # might not be relevant with the above handling strings
        is_private = getattr(chan_or_id, 'is_private', True)
        server_on = (not is_private and
                     self.settings["SERVER"].get(chan_or_id.server.id, False))

        dm_on = (is_private and
                 self.settings["DM"].get(chan_or_id.user.id, False))

        return server_on or dm_on

    def translate_message(self, content=None, embed=None):
        if content:
            # if not a link -- moved to sentence
            content = self.translate_sentence(content)
        if embed:
            self.in_place_translate_embed(embed)
        content = LOLZ_PREFIX + (content or '')  # for tracking
        return content, embed

    def in_place_translate_embed(self, embed):
        # not sure what provider is
        # assuming patterns. thought it'd make it easier to maintain.
        # will probably make it harder..
        safe_attrs = ('title', 'description',
                      'author', 'name',
                      'footer', 'text',
                      'fields', 'name', 'value')
        view = deepcopy(embed.to_dict())

        def translate_dict(d):
            return {attr: self.translate_sentence(val)
                    for attr, val in d.items()
                    if attr in safe_attrs}

        for k, v in view.items():
            if k not in safe_attrs:
                # only try to translate the safe attributes
                continue
            if isinstance(v, str):
                # strings are safe to go
                setattr(embed, k, self.translate_sentence(v))
            elif isinstance(v, dict):
                # all dict representations have a cooresponding set_arg function
                f = getattr(embed, 'set_' + k)
                lolzd = translate_dict(v)
                f(**lolzd)
            elif isinstance(v, list):
                # all list representations have a set_arg_at where arg is singular
                f = getattr(embed, 'set_' + k[:-1] + '_at')
                for i, d in enumerate(v):
                    lolzd = translate_dict(d)
                    f(i, **lolzd)

    # add randomization from Nikki's link. see todo

    # code edited from lolz
    def translate_word(self, word):
        # don't LOLZ links
        # if re.findall(self.regex['link'], word):
        #     return word

        # if emoji, don't change we're just gonna ignore all :words: regardless if emoji
        # : is probably being sent as a word itself. - fixed in sentence regex
        if word.startswith(':') and word.endswith(':'):
            return word

        # lower case lolz pleaz, ph is pronounces f!
        word = word.lower()

        # easiest first, look in dictionary
        if word in self.tranzlashun:
            return self.tranzlashun[word].upper()

        # fastest, check the cache...
        if word in self.cached:
            return self.cached[word].upper()

        word = word.replace('ph', 'f')

        # not found, perhaps a possesive apostrophy or the like?
        if self.regex['apostrophy'].search(word):
            result = self.regex['apostrophy'].search(word).groupdict()
            if result['prefix'] in self.tranzlashun:
                self.cached[word] = '%s%s' % (
                    self.tranzlashun[result['prefix']], result['suffix'])
                return self.cached[word].upper()

        # no matches? try heuristics unless we've been told otherwise
        # if self.heuristics is True:
        for regex, replace in self.easy_regex:
            match = regex.search(word)
            if match:
                self.cached[word] = match.group(1) + replace
                return self.cached[word].upper()
        tion = self.regex['tion'].search(word)
        if tion:
            self.cached[word] = tion.group(1) + 'shun' + tion.group(2)
            return self.cached[word].upper()
        stoz = self.regex['stoz'].search(word)
        if stoz and not self.regex['ous'].search(word):
            self.cached[word] = stoz.group(1) + 'z'
            return self.cached[word].upper()

        # no matches, leave it alone!
        self.cached[word] = word
        return word.upper()

    # code edited from lolz
    def translate_sentence(self, sentence):
        # no links
        if re.findall(self.regex['link'], sentence):
            return sentence

        new_sentence = ''
        # reminder to self...
        # ([\w]*) - match 0 or more a-zA-Z0-9_ group
        # ([\W]*) - match 0 or more non-(see above) group
        for word, space in re.findall("([:\w]*)([^:\w]*)", sentence):
            word = self.translate_word(word)
            # if word != '':
            new_sentence += word + space
        return new_sentence

    async def patcher(self):
        await self.bot.wait_until_ready()
        try:
            await asyncio.sleep(5)  # be safe lolz
            while True:
                await asyncio.sleep(1)
                if not hasattr(self.bot.send_message, 'old'):
                    self.info_prompt('WARNING', 'send_message')
                    self.bot.send_message = self.send_lolz(self.bot.send_message)
                if not self.bot.user.bot and not hasattr(self.bot.edit_message, 'old'):
                    self.info_prompt('WARNING', 'edit_message')
                    self.bot.edit_message = self.edit_lolz(self.bot.edit_message)
        except asyncio.CancelledError:
            pass

    def __unload(self):
        self._monkeymanager.cancel()
        # revert any changes done with this method. we should check instead for only lolz override
        if hasattr(self.bot.send_message, 'old'):
            self.info_prompt('TRY_CLEANUP', 'send_message')
            self.bot.send_message = self.bot.send_message.old
        if hasattr(self.bot.edit_message, 'old'):
            self.info_prompt('TRY_CLEANUP', 'edit_message')
            self.bot.edit_message = self.bot.edit_message.old
        self.info_prompt('DONE', 'send_message')

    def info_prompt(self, option, func_name):
        if option == 'WARNING':
            print('[WARNING:] -- Overwriting bot.{0} with send_lolz. '
                  'If bot.{0} is not reloaded,'.format(func_name))
            print('[WARNING:] -- in the event of a crash of the lolz '
                  'cog, you may not be able revert to bot.{} '
                  'without a restart/reloading lolz'.format(func_name))
        elif option == 'TRY_CLEANUP':
            print('[CLEANUP:] -- Trying to reload old bot.{}'.format(func_name))
        else:
            print('[CLEANUP:] -- Done. Reloading should have been successful '
                  'unless the lolz cog crashed without cleaning up')
            print('[CLEANUP:] -- If that is the case, the bot may need to be '
                  'restarted')

    async def on_message(self, message):
        chan_or_id = message.channel or message.author.id

        if not self.bot.user.bot:
            return
        if self.bot.user != message.author:
            return
        if not self.can_lolz(chan_or_id):
            return
        if message.content.startswith(LOLZ_PREFIX):
            return

        embed = message.embeds[0] if len(message.embeds) else None

        await self.bot.edit_message(message,
                                    new_content=message.content,
                                    embed=embed)


def check_mod(ctx):
    if ctx.message.author.id == settings.owner:
        return True
    server = ctx.message.server
    mod_role = settings.get_server_mod(server).lower()
    admin_role = settings.get_server_admin(server).lower()
    author = ctx.message.author
    role = discord.utils.find(lambda r: r.name.lower() in (mod_role,admin_role), author.roles)
    return role is not None


def check_folders():
    if not os.path.exists("data/lolz"):
        print("Creating lolz folder...")
        os.makedirs("data/lolz")


def check_files():
    settings_path = "data/lolz/settings.json"

    if not os.path.isfile(settings_path):
        print("Creating default lolz settings.json...")
        fileIO(settings_path, "save", default_settings)
    else: #consistency check
        current = fileIO(settings_path, "load")
        if current.keys() != default_settings.keys():
            for key in default_settings.keys():
                if key not in current.keys():
                    current[key] = default_settings[key]
                    print("Adding " + str(key) + " field to lolz settings.json")
            fileIO(settings_path, "save", current)


def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Lolz(bot))
