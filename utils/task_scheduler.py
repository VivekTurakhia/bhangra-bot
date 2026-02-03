import json
import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
import aiofiles

logger = logging.getLogger(__name__)

ANNOUNCEMENTS_FILE = 'data/announcements.json'
BACKUP_FILE = 'data/announcements.json.bak'


class TaskScheduler:
    """Manages scheduled announcements using APScheduler."""

    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.announcements_file = ANNOUNCEMENTS_FILE

    async def initialize(self):
        """Initialize the scheduler and load existing announcements."""
        self.scheduler.start()
        logger.info('APScheduler started')

        # Load and reschedule all pending announcements
        await self.load_and_reschedule_announcements()

    async def load_and_reschedule_announcements(self):
        """Load announcements from JSON and reschedule all pending jobs."""
        announcements = await self._load_announcements()
        now = datetime.now()
        rescheduled = 0
        skipped = 0

        for announcement in announcements:
            announcement_time = datetime.fromisoformat(announcement['datetime'])

            # Skip one-time announcements that are in the past
            if announcement['repeating'] == 'none' and announcement_time < now:
                skipped += 1
                logger.info(f"Skipping missed announcement: {announcement['id']}")
                continue

            # Schedule the announcement
            await self._schedule_job(announcement)
            rescheduled += 1

        logger.info(f'Rescheduled {rescheduled} announcements, skipped {skipped} missed announcements')

    async def create_announcement(self, announcement_type: str, text: str, location: Optional[str],
                                  datetime_str: str, repeating: str, role_id: int, created_by: int,
                                  practice_time: Optional[str] = None) -> Dict:
        """
        Create a new announcement and schedule it.

        Args:
            announcement_type: 'custom' or 'practice'
            text: Announcement text (for custom) or additional info (for practice)
            location: Practice location (for practice type only)
            datetime_str: ISO format datetime string
            repeating: 'none' or 'weekly'
            role_id: Discord role ID to ping
            created_by: User ID who created the announcement
            practice_time: Time of practice (for practice type only)

        Returns:
            The created announcement dictionary
        """
        announcement = {
            'id': str(uuid.uuid4()),
            'type': announcement_type,
            'text': text,
            'location': location,
            'practice_time': practice_time,
            'datetime': datetime_str,
            'repeating': repeating,
            'role_id': role_id,
            'created_by': created_by,
            'created_at': datetime.now().isoformat()
        }

        # Save to JSON
        await self._save_announcement(announcement)

        # Schedule the job
        await self._schedule_job(announcement)

        logger.info(f'Created announcement {announcement["id"]} for {datetime_str}')
        return announcement

    async def delete_announcement(self, announcement_id: str) -> bool:
        """
        Delete an announcement by ID.

        Args:
            announcement_id: The UUID of the announcement to delete

        Returns:
            True if deleted successfully, False if not found
        """
        announcements = await self._load_announcements()
        original_count = len(announcements)

        # Filter out the announcement to delete
        announcements = [a for a in announcements if a['id'] != announcement_id]

        if len(announcements) == original_count:
            return False  # Announcement not found

        # Save updated list
        await self._write_announcements(announcements)

        # Cancel the scheduled job
        try:
            self.scheduler.remove_job(announcement_id)
            logger.info(f'Cancelled job {announcement_id}')
        except Exception as e:
            logger.warning(f'Could not cancel job {announcement_id}: {e}')

        logger.info(f'Deleted announcement {announcement_id}')
        return True

    async def get_all_announcements(self) -> List[Dict]:
        """Get all pending announcements."""
        return await self._load_announcements()

    async def _schedule_job(self, announcement: Dict):
        """Schedule a job with APScheduler."""
        announcement_id = announcement['id']
        announcement_time = datetime.fromisoformat(announcement['datetime'])
        repeating = announcement['repeating']

        # Remove existing job if it exists
        try:
            self.scheduler.remove_job(announcement_id)
        except Exception:
            pass

        # Create trigger based on repeating type
        if repeating == 'none':
            trigger = DateTrigger(run_date=announcement_time)
        elif repeating == 'daily':
            trigger = CronTrigger(hour=announcement_time.hour, minute=announcement_time.minute)
        elif repeating == 'weekly':
            trigger = CronTrigger(day_of_week=announcement_time.weekday(),
                                  hour=announcement_time.hour,
                                  minute=announcement_time.minute)
        elif repeating == 'monthly':
            trigger = CronTrigger(day=announcement_time.day,
                                  hour=announcement_time.hour,
                                  minute=announcement_time.minute)
        else:
            logger.error(f'Unknown repeating type: {repeating}')
            return

        # Schedule the job
        self.scheduler.add_job(
            self._execute_announcement,
            trigger=trigger,
            id=announcement_id,
            args=[announcement_id],
            replace_existing=True
        )

        logger.info(f'Scheduled job {announcement_id} with trigger {repeating}')

    async def _execute_announcement(self, announcement_id: str):
        """Execute an announcement by sending it to the Discord channel."""
        try:
            # Load announcement data
            announcements = await self._load_announcements()
            announcement = next((a for a in announcements if a['id'] == announcement_id), None)

            if not announcement:
                logger.error(f'Announcement {announcement_id} not found')
                return

            # Get the announcement channel
            channel_id = int(os.getenv('ANNOUNCEMENT_CHANNEL_ID'))
            channel = self.bot.get_channel(channel_id)

            if not channel:
                logger.error(f'Channel {channel_id} not found')
                return

            # Get the role to ping
            guild = channel.guild
            role = guild.get_role(announcement['role_id'])
            role_mention = role.mention if role else ''

            # Format the message based on type
            if announcement['type'] == 'practice':
                practice_time = announcement.get('practice_time', 'TBD')
                message = f"{role_mention}\n\n**Practice Announcement**\n**Time:** {practice_time}\n**Location:** {announcement['location']}"
            else:
                message = f"{role_mention}\n\n{announcement['text']}"

            # Send the announcement
            await channel.send(message)
            logger.info(f'Sent announcement {announcement_id}')

            # If it's a one-time announcement, remove it from storage
            if announcement['repeating'] == 'none':
                await self.delete_announcement(announcement_id)
                logger.info(f'Removed one-time announcement {announcement_id}')

        except Exception as e:
            logger.error(f'Error executing announcement {announcement_id}: {e}', exc_info=True)

    async def _save_announcement(self, announcement: Dict):
        """Save a new announcement to the JSON file."""
        announcements = await self._load_announcements()
        announcements.append(announcement)
        await self._write_announcements(announcements)

    async def _load_announcements(self) -> List[Dict]:
        """Load announcements from JSON file."""
        try:
            if not os.path.exists(self.announcements_file):
                return []

            async with aiofiles.open(self.announcements_file, 'r') as f:
                content = await f.read()
                data = json.loads(content)
                return data.get('announcements', [])
        except Exception as e:
            logger.error(f'Error loading announcements: {e}')
            return []

    async def _write_announcements(self, announcements: List[Dict]):
        """Write announcements to JSON file with atomic write and backup."""
        try:
            # Create backup if file exists
            if os.path.exists(self.announcements_file):
                if os.path.exists(BACKUP_FILE):
                    os.remove(BACKUP_FILE)
                os.rename(self.announcements_file, BACKUP_FILE)

            # Write to file atomically
            data = {'announcements': announcements}
            temp_file = f'{self.announcements_file}.tmp'

            async with aiofiles.open(temp_file, 'w') as f:
                await f.write(json.dumps(data, indent=2))

            os.rename(temp_file, self.announcements_file)
            logger.debug('Saved announcements to file')

        except Exception as e:
            logger.error(f'Error writing announcements: {e}')
            # Restore from backup if write failed
            if os.path.exists(BACKUP_FILE):
                os.rename(BACKUP_FILE, self.announcements_file)
            raise
