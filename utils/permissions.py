import discord

def is_admin(interaction: discord.Interaction) -> bool:
    """
    Check if the user has administrator permissions.

    Args:
        interaction: Discord interaction object

    Returns:
        True if user has administrator permission, False otherwise
    """
    return interaction.user.guild_permissions.administrator
