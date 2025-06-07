import os
import discord
import csv
from discord.ext import commands, tasks
import asyncio
from ascii_art_functions import get_isac_banner,get_boot_art
from CommandGroup import CommandGroup
class ISAC_Console(commands.Bot):
    """A class to manage a Reddit Bot that interacts with a Discord server."""

    def __init__(self):
        """Initializes the RedditBotManager with Discord intents and settings.

        Args:
            Supabase (bool): Whether to initialize Supabase connector.
        """
        intents = discord.Intents.default()
        intents.messages = True
        intents.typing = True
        intents.message_content = True
        self.auto_post = True  # Automatically post updates
        self.post_channel = int(
            os.getenv("DISCORD_POST_CHANNEL")
        )  # Channel ID for posting in the spirit of the bot this is the "Approved" SHD channel
        self.command_group = None  # Command group placeholder
        
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Runs before the bot is ready. Override to implement custom setup."""
        pass

    async def on_ready(self):
        """Triggered when the bot has successfully connected and is ready.

        This function sets up the command group, initializes the Reddit monitor,
        and starts scheduled tasks for automatic posting.
        """
        print(f"We have logged in as {self.user}")
        # Updating class defaults after the bot initiates
        self.post_channel = self.get_channel(self.post_channel)
        self.command_group = CommandGroup(self.post_channel)
        await self.add_cog(self.command_group)  # Add command group to the bot

        print(f"Logged in as {self.user} | SHD Network Online")

        # Initial boot message
        await self.isac_initilize(self.post_channel)
        # # Start automatic updates if enabled
        # if self.auto_post:
        #     self.checknow_task.change_interval(seconds=self.check_interval)
        #     self.checknow_task.start()

    async def on_message(self, message):
        """Handles incoming messages in the monitored channel.

        Args:
            message (discord.Message): The received message object.
        """
        if message.channel.id == self.post_channel.id:
            # Ensure other commands still work
            await super().on_message(message)

    # @tasks.loop(seconds=20)
    # async def checknow_task(self):
    #     """Scheduled task to execute checks every specified interval."""
    #     if self.post_channel:
    #         await self.command_group.execute_checknow(self.post_channel)
    #     else:
    #         print("Channel not found.")

    # checknow_task.before_loop

    # async def before_checknow_task(self):
    #     """Waits until the bot is ready before executing the checknow task."""
    #     await self.wait_until_ready()

    async def close(self):
        """Closes the bot and stops scheduled tasks."""
        await super().close()  # Close the bot



    async def isac_initilize(self,post_channel):
        # Initial boot message
        boot_msg = await post_channel.send("```diff\n[ISAC] SHD Network Initialization Sequence Started...\n[▒▒▒▒▒▒▒▒▒▒] 0%```")
        
        # Boot sequence stages with descriptions and durations
        boot_sequence = [
            ("Loading tactical subsystems", 0.7),
            ("Decrypting SHD protocols", 0.9),
            ("Establishing satellite uplink", 1.1),
            ("Calibrating threat sensors", 0.8),
            ("Initializing biometric database", 1.2),
            ("Synchronizing field agent comms", 1.0),
            ("Encrypting secure channels", 0.6),
            ("Verifying Division protocols", 0.9),
        ]
        
        # Execute boot sequence
        for i, (stage, delay) in enumerate(boot_sequence):
            progress = int((i + 1) / len(boot_sequence) * 100)
            progress_bar = f"[{'█' * (progress//5)}{'▒' * (20 - progress//5)}] {progress}%"
            
            await boot_msg.edit(content=f"```diff\n[ISAC] {stage}\n{progress_bar}\n{get_boot_art(i)}```")
            await asyncio.sleep(delay)
        
        # Final ISAC banner
        await boot_msg.edit(content=get_isac_banner())        
        
        
if __name__ == '__main__':
    bot = ISAC_Console()
    # Run the bot using the provided Discord token from the environment variables
    bot.run(os.getenv("DISCORD_TOKEN"))