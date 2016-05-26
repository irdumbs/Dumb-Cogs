import discord

class Ide:
    """Red-Discordbot IDE - a cog port of Alias efficiencies for the lazy bot owner / cog creator

    This cog is under construction atm. only useful thing in installing this is the sublime snippets in the data folder.
    Place them in Packages/User to use them."""

    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    n = Ide(bot)
    bot.add_cog(n)
