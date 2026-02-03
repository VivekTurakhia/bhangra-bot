import discord
from discord import app_commands
from discord.ext import commands


class BasicCommands(commands.Cog):
    """Basic bot commands."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="talk", description="Bot responds with Hello World")
    async def talk(self, interaction: discord.Interaction):
        """Respond with Hello World."""
        await interaction.response.send_message("Hello World")


async def setup(bot):
    """Load the BasicCommands cog."""
    await bot.add_cog(BasicCommands(bot))
