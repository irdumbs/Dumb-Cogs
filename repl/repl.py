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
import io, sys, os
import subprocess

# TODO: rtfs
#   * functionify
#   * commandify
#   * option to open in text editor
#   * Cogs
#   * path/file.py
#   * cog info / author
#       * look in downloads if not found
#           * mention that it's not installed


class REPL:
    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json('data/repl/settings.json')
        self.output_file = "data/repl/temp_output.txt"
        self.sessions = set()

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
        discord_fmt = '```py\n{}\n```'
        if len(discord_fmt.format(results)) > 2000:
            if self.settings["OUTPUT_REDIRECT"] == "pm":
                await self.bot.send_message(msg.channel, 'Content too big. Check your PMs')
                enough_paper = 20
                for page in pagify(results, ['\n', ' '], shorten_by=12):
                    await self.bot.send_message(msg.author, discord_fmt.format(page))
                    enough_paper -= 1
                    if not enough_paper:
                        await self.bot.send_message(msg.author, "**Too many pages! Think of the trees!**")
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
          pm
          console
          file
        """
        server = ctx.message.server
        channel = ctx.message.channel
        author = ctx.message.author
        if discord_console_file not in ['pm','console','file']:
            await self.bot.say('Choices are discord/console/file')
            return
        if discord_console_file == 'file':
            choices = ['subl','subl.exe','atom','atom.exe']
            await self.bot.say("You chose to print to file. What would you like to open it with?\n"
                    "Choose between:  {}".format(' | '.join(choices+['nothing'])))
            answer = await self.bot.wait_for_message(timeout=20, author=author)
            answer = answer.content
            if answer not in choices:
                answer = None
                await self.bot.say("ok, I won't open it after writing to {}".format(self.output_file))
            else:
                await self.bot.say("output will be opened with: {} {}".format(answer,self.output_file))
            self.settings['OPEN_CMD'] = answer
        self.settings["OUTPUT_REDIRECT"] = discord_console_file
        dataIO.save_json("data/repl/settings.json", self.settings)
        await self.bot.say("repl overflow will now go to "+discord_console_file)


def check_folders():
    folder = "data/repl"
    if not os.path.exists(folder):
        print("Creating {} folder...".format(folder))
        os.makedirs(folder)


def check_files():
    default = {"OUTPUT_REDIRECT" : "discord", "OPEN_CMD" : None}
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
