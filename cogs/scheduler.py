import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from dateutil import parser as date_parser
import logging
from utils.permissions import is_admin

logger = logging.getLogger(__name__)


class CustomAnnouncementModal(discord.ui.Modal, title='Schedule Custom Announcement'):
    """Modal for collecting custom announcement details."""

    announcement_text = discord.ui.TextInput(
        label='Announcement Text',
        placeholder='Enter the announcement message...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    datetime_input = discord.ui.TextInput(
        label='Date and Time',
        placeholder='e.g., "Feb 15 6pm" or "2026-02-15 18:00"',
        required=True,
        max_length=100
    )

    repeating = discord.ui.TextInput(
        label='Repeating',
        placeholder='none or weekly',
        required=True,
        max_length=20,
        default='none'
    )

    role_name = discord.ui.TextInput(
        label='Role to Ping',
        placeholder='Enter role name (e.g., @everyone)',
        required=True,
        max_length=100
    )

    def __init__(self, scheduler):
        super().__init__()
        self.scheduler = scheduler

    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        try:
            # Parse datetime
            try:
                parsed_datetime = date_parser.parse(self.datetime_input.value)
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Invalid date/time format. Please use formats like 'Feb 15 6pm' or '2026-02-15 18:00'.",
                    ephemeral=True
                )
                return

            # Validate datetime is in the future
            if parsed_datetime <= datetime.now():
                await interaction.response.send_message(
                    "❌ The date and time must be in the future.",
                    ephemeral=True
                )
                return

            # Validate repeating value
            repeating_value = self.repeating.value.lower().strip()
            if repeating_value not in ['none', 'weekly']:
                await interaction.response.send_message(
                    "❌ Invalid repeating value. Must be: none or weekly",
                    ephemeral=True
                )
                return

            # Find the role
            role_input = self.role_name.value.strip()
            if role_input.lower() == '@everyone':
                role = interaction.guild.default_role
            else:
                # Remove @ if present
                role_input = role_input.lstrip('@')
                role = discord.utils.get(interaction.guild.roles, name=role_input)

            if not role:
                await interaction.response.send_message(
                    f"❌ Role '{self.role_name.value}' not found. Please check the role name and try again.",
                    ephemeral=True
                )
                return

            # Create the announcement
            announcement = await self.scheduler.create_announcement(
                announcement_type='custom',
                text=self.announcement_text.value,
                location=None,
                datetime_str=parsed_datetime.isoformat(),
                repeating=repeating_value,
                role_id=role.id,
                created_by=interaction.user.id
            )

            # Send confirmation
            repeat_text = "one-time" if repeating_value == 'none' else f"repeating {repeating_value}"
            await interaction.response.send_message(
                f"✅ Custom announcement scheduled for {parsed_datetime.strftime('%B %d, %Y at %I:%M %p')} ({repeat_text})\n"
                f"Will ping: {role.mention}",
                ephemeral=True
            )

        except Exception as e:
            logger.error(f'Error creating custom announcement: {e}', exc_info=True)
            await interaction.response.send_message(
                f"❌ Error creating announcement: {str(e)}",
                ephemeral=True
            )


class PracticeAnnouncementModal(discord.ui.Modal, title='Schedule Practice Announcement'):
    """Modal for collecting practice announcement details."""

    location = discord.ui.TextInput(
        label='Practice Location',
        placeholder='Enter the practice location...',
        required=True,
        max_length=200
    )

    practice_time = discord.ui.TextInput(
        label='Practice Time',
        placeholder='e.g., "7pm-10pm"',
        required=True,
        max_length=50
    )

    datetime_input = discord.ui.TextInput(
        label='Announcement Date and Time',
        placeholder='When to send announcement (e.g., "Feb 15 4pm")',
        required=True,
        max_length=100
    )

    repeating = discord.ui.TextInput(
        label='Repeating',
        placeholder='none or weekly',
        required=True,
        max_length=20,
        default='none'
    )

    role_name = discord.ui.TextInput(
        label='Role to Ping',
        placeholder='Enter role name (e.g., @everyone)',
        required=True,
        max_length=100
    )

    def __init__(self, scheduler):
        super().__init__()
        self.scheduler = scheduler

    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        try:
            # Parse datetime
            try:
                parsed_datetime = date_parser.parse(self.datetime_input.value)
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Invalid date/time format. Please use formats like 'Feb 15 6pm' or '2026-02-15 18:00'.",
                    ephemeral=True
                )
                return

            # Validate datetime is in the future
            if parsed_datetime <= datetime.now():
                await interaction.response.send_message(
                    "❌ The date and time must be in the future.",
                    ephemeral=True
                )
                return

            # Validate repeating value
            repeating_value = self.repeating.value.lower().strip()
            if repeating_value not in ['none', 'weekly']:
                await interaction.response.send_message(
                    "❌ Invalid repeating value. Must be: none or weekly",
                    ephemeral=True
                )
                return

            # Find the role
            role_input = self.role_name.value.strip()
            if role_input.lower() == '@everyone':
                role = interaction.guild.default_role
            else:
                # Remove @ if present
                role_input = role_input.lstrip('@')
                role = discord.utils.get(interaction.guild.roles, name=role_input)

            if not role:
                await interaction.response.send_message(
                    f"❌ Role '{self.role_name.value}' not found. Please check the role name and try again.",
                    ephemeral=True
                )
                return

            # Create the announcement
            announcement = await self.scheduler.create_announcement(
                announcement_type='practice',
                text='',
                location=self.location.value,
                practice_time=self.practice_time.value,
                datetime_str=parsed_datetime.isoformat(),
                repeating=repeating_value,
                role_id=role.id,
                created_by=interaction.user.id
            )

            # Send confirmation
            repeat_text = "one-time" if repeating_value == 'none' else f"repeating {repeating_value}"
            await interaction.response.send_message(
                f"✅ Practice announcement scheduled\n"
                f"**Practice Time:** {self.practice_time.value}\n"
                f"**Location:** {self.location.value}\n"
                f"**Announcement will be sent:** {parsed_datetime.strftime('%B %d, %Y at %I:%M %p')} ({repeat_text})\n"
                f"**Will ping:** {role.mention}",
                ephemeral=True
            )

        except Exception as e:
            logger.error(f'Error creating practice announcement: {e}', exc_info=True)
            await interaction.response.send_message(
                f"❌ Error creating announcement: {str(e)}",
                ephemeral=True
            )


class SchedulerCommands(commands.Cog):
    """Scheduler commands for announcements."""

    def __init__(self, bot, scheduler):
        self.bot = bot
        self.scheduler = scheduler

    schedule_group = app_commands.Group(name="schedule", description="Manage scheduled announcements")

    @schedule_group.command(name="custom", description="Schedule a custom announcement")
    async def schedule_custom(self, interaction: discord.Interaction):
        """Schedule a custom announcement."""
        if not is_admin(interaction):
            await interaction.response.send_message(
                "❌ You need Administrator permissions to use this command.",
                ephemeral=True
            )
            return

        modal = CustomAnnouncementModal(self.scheduler)
        await interaction.response.send_modal(modal)

    @schedule_group.command(name="practice", description="Schedule a practice announcement")
    async def schedule_practice(self, interaction: discord.Interaction):
        """Schedule a practice announcement."""
        if not is_admin(interaction):
            await interaction.response.send_message(
                "❌ You need Administrator permissions to use this command.",
                ephemeral=True
            )
            return

        modal = PracticeAnnouncementModal(self.scheduler)
        await interaction.response.send_modal(modal)

    @schedule_group.command(name="delete", description="Delete a scheduled announcement")
    async def schedule_delete(self, interaction: discord.Interaction):
        """Delete a scheduled announcement."""
        if not is_admin(interaction):
            await interaction.response.send_message(
                "❌ You need Administrator permissions to use this command.",
                ephemeral=True
            )
            return

        # Get all announcements
        announcements = await self.scheduler.get_all_announcements()

        if not announcements:
            await interaction.response.send_message(
                "📭 There are no scheduled announcements.",
                ephemeral=True
            )
            return

        # Create embed with announcement list
        embed = discord.Embed(
            title="Scheduled Announcements",
            description="Select an announcement to delete:",
            color=discord.Color.blue()
        )

        # Build select menu options (max 25)
        options = []
        for idx, announcement in enumerate(announcements[:25], start=1):
            announcement_time = datetime.fromisoformat(announcement['datetime'])
            repeating_text = "One-time" if announcement['repeating'] == 'none' else f"Repeating {announcement['repeating']}"

            # Format the announcement preview
            if announcement['type'] == 'practice':
                label = f"{idx}. Practice at {announcement['location']}"
                description = f"{announcement_time.strftime('%b %d, %I:%M %p')} - {repeating_text}"
            else:
                text_preview = announcement['text'][:50] + '...' if len(announcement['text']) > 50 else announcement['text']
                label = f"{idx}. {text_preview}"
                description = f"{announcement_time.strftime('%b %d, %I:%M %p')} - {repeating_text}"

            options.append(discord.SelectOption(
                label=label[:100],  # Discord limit
                description=description[:100],  # Discord limit
                value=announcement['id']
            ))

            # Add to embed
            embed.add_field(
                name=f"{idx}. [{announcement['type'].title()}] {repeating_text}",
                value=f"Time: {announcement_time.strftime('%B %d, %Y at %I:%M %p')}\n"
                      f"Text: {announcement.get('text', announcement.get('location', 'N/A'))[:100]}",
                inline=False
            )

        # Create select menu
        select = discord.ui.Select(
            placeholder="Choose an announcement to delete...",
            options=options
        )

        async def select_callback(select_interaction: discord.Interaction):
            """Handle announcement selection."""
            announcement_id = select.values[0]
            success = await self.scheduler.delete_announcement(announcement_id)

            if success:
                await select_interaction.response.send_message(
                    f"✅ Announcement deleted successfully.",
                    ephemeral=True
                )
            else:
                await select_interaction.response.send_message(
                    f"❌ Failed to delete announcement.",
                    ephemeral=True
                )

        select.callback = select_callback

        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    """Load the SchedulerCommands cog."""
    # Get the scheduler from the bot
    scheduler = getattr(bot, 'scheduler', None)
    if not scheduler:
        logger.error('Scheduler not found on bot instance')
        return

    await bot.add_cog(SchedulerCommands(bot, scheduler))
