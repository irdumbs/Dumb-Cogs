from discord.ext import commands
import red
from cogs.utils import checks
from cogs.utils.dataIO import dataIO
from cogs.utils.chat_formatting import pagify
import asyncio
import traceback
import discord
import inspect
from contextlib import redirect_stdout
from __main__ import send_cmd_help
import io
import os
import subprocess
from collections import OrderedDict

# TODO: rtfs
#   * functionify
#   * commandify
#   * option to open file in text editor
#   * Cogs
#   * path/file.py
#   * cog info / author
#       * look in downloads if not found
#           * mention that it's not installed

class ReactionRemoveEvent(asyncio.Event):
    def __init__(self, emojis, author):
        super().__init__()
        self.emojis = emojis
        self.author = author
        self.reaction = None

    def set(self, reaction):
        self.reaction = reaction
        return super().set()


class REPL:
    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json('data/repl/settings.json')
        self.output_file = "data/repl/temp_output.txt"
        self.sessions = set()
        self.reaction_remove_events = {}

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, e):
        return '```py\n{0.text}{1:>{0.offset}}\n{2}: {0}```'.format(e, '^', type(e).__name__)

    async def print_results(self, ctx, results):
        msg = ctx.message
        nbs = '​'
        discord_fmt = nbs + '```py\n{}\n```'
        if len(discord_fmt.format(results)) > 2000:
            if self.settings["OUTPUT_REDIRECT"] == "pages":
                page = self.interactive_results(ctx, results,
                                                single_msg=not self.settings["MULTI_MSG_PAGING"])
                self.bot.loop.create_task(page)
            elif self.settings["OUTPUT_REDIRECT"] == "pm":
                await self.bot.send_message(msg.channel, 'Content too big. Check your PMs')
                enough_paper = 20
                for page in pagify(results, ['\n', ' '], shorten_by=12):
                    await self.bot.send_message(msg.author, discord_fmt.format(page))
                    enough_paper -= 1
                    if not enough_paper:
                        await self.bot.send_message(msg.author,
                                                    "**Too many pages! Think of the trees!**")
                        return
            elif self.settings["OUTPUT_REDIRECT"] == "console":
                await self.bot.send_message(msg.channel, 'Content too big. Check your console')
                print(results)
            else:
                await self.bot.send_message(msg.channel, 'Content too big. Writing to file')
                with open(self.output_file, 'w') as f:
                    f.write(results)
                open_cmd = self.settings["OPEN_CMD"]
                if open_cmd:
                    subprocess.Popen([open_cmd, self.output_file])
        else:
            await self.bot.send_message(msg.channel, discord_fmt.format(results))

    async def interactive_results(self, ctx, results, single_msg=True):
        author = ctx.message.author
        channel = ctx.message.channel

        if single_msg:
            choices = OrderedDict((('◀', 'prev'),
                                   ('❌', 'close'),
                                   ('▶', 'next')))
        else:
            choices = OrderedDict((('❌', 'close'),
                                   ('🔽', 'next')))

        nbs = '​'
        discord_fmt = nbs + '```py\n{}\n```'
        prompt = ("  Output too long. Navigate pages with ({})"
                  .format('/'.join(choices.values())))

        pager = pagify(results, ['\n', ' '], page_length=1500)
        # results is not a generator, so no reason to keep this as one
        pages = [discord_fmt.format(p) + 'pg. {}'.format(c + 1)
                 for c, p in enumerate(pager)]
        pages[0] += prompt

        choice = 'next'
        page_num = 0
        dirs = {'next': 1, 'prev': -1}
        msgs = []
        while choice:
            msg = await self.display_page(pages[page_num], channel, choices,
                                          msgs, single_msg)
            choice = await self.wait_for_interaction(msg, author, choices)
            if choice == 'close':
                try:
                    await self.bot.delete_messages(msgs)
                except:  # selfbots
                    for m in msgs:
                        await self.bot.delete_message(m)
                break
            if choice in dirs:
                page_num = (page_num + dirs[choice]) % len(pages)
        if choice is None:
            await self.remove_reactions(msgs.pop())

    async def remove_reactions(self, msg):
        channel = msg.channel
        botm = msg.server.me
        if botm.permissions_in(channel).manage_messages:
            await self.bot.clear_reactions(msg)
        else:
            await asyncio.gather(*(self.bot.remove_reaction(msg, r.emoji, botm)
                                   for r in msg.reactions if r.me),
                                 return_exceptions=True)

    async def display_page(self, page, channel, emojis, msgs, overwrite_prev):
        if msgs and overwrite_prev:
            msg = msgs.pop()
            embed = msg.embeds[0] if len(msg.embeds) else None
            msg = await self.bot.edit_message(msg, new_content=page, embed=embed)
        else:
            send_msg = self.bot.send_message(channel, page)
            if msgs:
                # refresh msg
                prv_msg = await self.bot.get_message(channel, msgs[len(msgs) - 1].id)
                tasks = (send_msg, self.remove_reactions(prv_msg))
                results = await asyncio.gather(*tasks, return_exceptions=True)
                msg = results[0]
            else:
                msg = await send_msg
            try:
                for e in emojis:  # we want these to be in order
                    await self.bot.add_reaction(msg, e)
            except:
                pass
        msgs.append(msg)
        return msg

    async def wait_for_interaction(self, msg, author, choices: OrderedDict,
                                   timeout=120, delete_msg=True):
        """waits for a message or reaction add/remove
        if the resonse is a msg, schedules msg deletion it if delete_msg"""

        emojis = tuple(choices.keys())
        words = tuple(choices.values())

        def mcheck(msg):
            return msg.content.lower() in words

        tasks = (self.bot.wait_for_message(author=author, timeout=timeout,
                                           channel=msg.channel, check=mcheck),
                 self.bot.wait_for_reaction(user=author, timeout=timeout,
                                            message=msg, emoji=emojis),
                 self.wait_for_reaction_remove(user=author, timeout=timeout,
                                               message=msg, emoji=emojis))

        def msgconv(msg):
            res = msg.content.lower()

            async def try_del():
                try:
                    await self.bot.delete_message(msg)
                except:
                    pass
            self.bot.loop.create_task(try_del())
            return res

        def mojichoice(r):
            return choices[r.reaction.emoji]

        converters = (msgconv, mojichoice, mojichoice)
        return await wait_for_first_response(tasks, converters)

    async def wait_for_reaction_remove(self, emoji=None, *, user=None,
                                       timeout=None, message=None, check=None):
        """Waits for a reaction to be removed by a user from a message within a time period.
        Made to act like other discord.py wait_for_* functions but is not fully implemented.

        Because of that, wait_for_reaction_remove(self, emoji: list, user, message, timeout=None)
        is a better representation of this function's def

        returns the actual event or None if timeout
        """
        if not (emoji and user and message) or check or isinstance(emoji, str):
            raise NotImplementedError("wait_for_reaction_remove(self, emoji, "
                                      "user, message, timeout=None) is a better "
                                      "representation of this function definition")
        remove_event = ReactionRemoveEvent(emoji, user)
        self.reaction_remove_events[message.id] = remove_event
        done, pending = await asyncio.wait([remove_event.wait()],
                                           timeout=timeout)
        res = self.reaction_remove_events.pop(message.id)
        try:
            return done.pop().result() and res
        except:
            return None

    @commands.command(pass_context=True, hidden=True)
    @checks.is_owner()
    async def repl(self, ctx):
        msg = ctx.message

        variables = {
            'ctx': ctx,
            'bot': self.bot,
            'message': msg,
            'server': msg.server,
            'channel': msg.channel,
            'author': msg.author,
            '_': None,
        }

        if msg.channel.id in self.sessions:
            await self.bot.say('Already running a REPL session in this channel. Exit it with `quit`.')
            return

        self.sessions.add(msg.channel.id)
        await self.bot.say('Enter code to execute or evaluate. `exit()` or `quit` to exit.')
        while True:
            response = await self.bot.wait_for_message(author=msg.author, channel=msg.channel,
                                                       check=lambda m: m.content.startswith('`'))

            cleaned = self.cleanup_code(response.content)

            if cleaned in ('quit', 'exit', 'exit()'):
                await self.bot.say('Exiting.')
                self.sessions.remove(msg.channel.id)
                return

            executor = exec
            if cleaned.count('\n') == 0:
                # single statement, potentially 'eval'
                try:
                    code = compile(cleaned, '<repl session>', 'eval')
                except SyntaxError:
                    pass
                else:
                    executor = eval

            if executor is exec:
                try:
                    code = compile(cleaned, '<repl session>', 'exec')
                except SyntaxError as e:
                    await self.bot.say(self.get_syntax_error(e))
                    continue

            variables['message'] = response

            fmt = None
            stdout = io.StringIO()

            try:
                with redirect_stdout(stdout):
                    result = executor(code, variables)
                    if inspect.isawaitable(result):
                        result = await result
            except Exception as e:
                value = stdout.getvalue()
                fmt = '{}{}'.format(value, traceback.format_exc())
            else:
                value = stdout.getvalue()
                if result is not None:
                    fmt = '{}{}'.format(value, result)
                    variables['_'] = result
                elif value:
                    fmt = '{}'.format(value)

            try:
                if fmt is not None:
                    await self.print_results(ctx, fmt)
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await self.bot.send_message(msg.channel, 'Unexpected error: `{}`'.format(e))

    @commands.group(pass_context=True)
    async def replset(self, ctx):
        """global repl settings"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @replset.command(pass_context=True, name="print", no_pm=True)
    async def replset_print(self, ctx, discord_console_file):
        """Sets where repl content goes when response is too large.
        Choices are
          pages    - navigable pager in the current
          pm       - send up to 20 pages via pm
          console  - print results to console
          file     - write results to a file, optionally opening in subl/atom
        """
        author = ctx.message.author
        if discord_console_file not in ['pm', 'console', 'file', 'pages']:
            await self.bot.say('Choices are discord/console/file')
            return
        if discord_console_file == 'file':
            choices = ['subl', 'subl.exe', 'atom', 'atom.exe']
            msg = ("You chose to print to file. What would you like to open it with?\n"
                   "Choose between:  {}".format(' | '.join(choices + ['nothing'])))
            answer = await self.user_choice(author, msg, choices)
            if answer not in choices:
                await self.bot.say("ok, I won't open it after writing to "
                                   "{}".format(self.output_file))
            else:
                await self.bot.say("output will be opened with: {} "
                                   "{}".format(answer, self.output_file))
            self.settings['OPEN_CMD'] = answer
        elif discord_console_file == 'pages':
            choices = ['yes', 'no', 'y', 'n']
            msg = ("Add pages as new messages instead of navigating through the pages "
                   "by editing one message? (yes/no)")
            answer = await self.user_choice(author, msg, choices)
            answer = answer is not None and answer[0] == 'y'
            if answer:
                await self.bot.say("ok, you will be given the option to page via adding new pages")
            else:
                await self.bot.say("ok, regular single-message paging will be used instead")
            self.settings['MULTI_MSG_PAGING'] = answer
        self.settings["OUTPUT_REDIRECT"] = discord_console_file
        dataIO.save_json("data/repl/settings.json", self.settings)
        await self.bot.say("repl overflow will now go to " + discord_console_file)

    async def user_choice(self, author, msg, choices, timeout=20):
        await self.bot.say(msg)
        choices = [c.lower() for c in choices]
        answer = await self.bot.wait_for_message(timeout=timeout,
                                                 author=author)
        answer = answer.content.lower()
        return answer if answer in choices else None

    async def on_reaction_remove(self, reaction, user):
        """Handles watching for reactions for wait_for_reaction_remove"""
        event = self.reaction_remove_events.get(reaction.message.id, None)
        if (event and not event.is_set() and
            user == event.author and
            reaction.emoji in event.emojis):
            event.set(reaction)


async def wait_for_first_response(tasks, converters):
    """given a list of unawaited tasks and non-coro result parsers to be called on the results,
    this function returns the 1st result that is returned and converted

    if it is possible for 2 tasks to complete at the same time,
    only the 1st result deteremined by asyncio.wait will be returned

    returns None if none successfully complete
    returns 1st error raised if any occur (probably)
    """
    primed = [wait_for_result(t, c) for t, c in zip(tasks, converters)]
    done, pending = await asyncio.wait(primed, return_when=asyncio.FIRST_COMPLETED)
    for p in pending:
        p.cancel()

    try:
        return done.pop().result()
    except:
        return None


async def wait_for_result(task, converter):
    """await the task call and return its results parsed through the converter"""
    # why did I do this?
    return converter(await task)


def check_folders():
    folder = "data/repl"
    if not os.path.exists(folder):
        print("Creating {} folder...".format(folder))
        os.makedirs(folder)


def check_files():
    default = {"OUTPUT_REDIRECT": "discord", "OPEN_CMD": None,
               "MULTI_MSG_PAGING": False}
    settings_path = "data/repl/settings.json"

    if not os.path.isfile(settings_path):
        print("Creating default repl settings.json...")
        dataIO.save_json(settings_path, default)
    else:  # consistency check
        current = dataIO.load_json(settings_path)
        if current.keys() != default.keys():
            for key in default.keys():
                if key not in current.keys():
                    current[key] = default[key]
                    print(
                        "Adding " + str(key) + " field to repl settings.json")
            dataIO.save_json(settings_path, current)


def setup(bot: red.Bot):
    check_folders()
    check_files()
    bot.add_cog(REPL(bot))
