import discord
from discord.ext import commands
from discord import app_commands
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
GUILD_ID = 1403064541637640212  # Replace with your actual guild ID
CHANNEL_ID = 1403065398689005648  # Replace with your actual channel ID for applications

class ApplicationModal(discord.ui.Modal, title='Guild Application'):
    def __init__(self):
        super().__init__()

    # Minecraft Username input
    minecraft_username = discord.ui.TextInput(
        label='Minecraft Username',
        placeholder='Enter your Minecraft username...',
        required=True,
        max_length=16,
        min_length=3
    )

    # Experience input
    experience = discord.ui.TextInput(
        label='Experience',
        style=discord.TextStyle.paragraph,
        placeholder='Tell us about your Minecraft/gaming experience...',
        required=True,
        max_length=300,
        min_length=10
    )

    # Reason for joining input
    reason = discord.ui.TextInput(
        label='Reason for Joining',
        style=discord.TextStyle.paragraph,
        placeholder='Why do you want to join our guild?',
        required=True,
        max_length=300,
        min_length=10
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission"""
        try:
            # Get the application channel
            channel = interaction.client.get_channel(CHANNEL_ID)
            
            if not channel:
                await interaction.response.send_message(
                    "❌ Application channel not found. Please contact an administrator.",
                    ephemeral=True
                )
                logger.error(f"Channel with ID {CHANNEL_ID} not found")
                return
            
            # Check if channel supports sending messages
            if not hasattr(channel, 'send'):
                await interaction.response.send_message(
                    "❌ Cannot send messages to this channel type. Please contact an administrator.",
                    ephemeral=True
                )
                logger.error(f"Channel {CHANNEL_ID} does not support sending messages")
                return

            # Create embedded message
            embed = discord.Embed(
                title="🎮 New Guild Application",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="👤 Applicant",
                value=interaction.user.mention,
                inline=True
            )
            
            embed.add_field(
                name="⛏️ Minecraft Username",
                value=f"`{self.minecraft_username.value}`",
                inline=True
            )
            
            embed.add_field(
                name="📊 Experience",
                value=self.experience.value,
                inline=False
            )
            
            embed.add_field(
                name="💭 Reason for Joining",
                value=self.reason.value,
                inline=False
            )
            
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.set_footer(
                text=f"Application ID: {interaction.user.id}",
                icon_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None
            )

            # Send application to designated channel (cast to text channel for type safety)
            if isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel)):
                await channel.send(embed=embed)
            else:
                await interaction.response.send_message(
                    "❌ Application channel must be a text channel. Please contact an administrator.",
                    ephemeral=True
                )
                logger.error(f"Channel {CHANNEL_ID} is not a text channel")
                return
            
            # Confirm submission to user
            await interaction.response.send_message(
                "✅ Your application has been submitted successfully! "
                "Our staff will review it and get back to you soon.",
                ephemeral=True
            )
            
            logger.info(f"Application submitted by {interaction.user} ({interaction.user.id})")
            
        except discord.HTTPException as e:
            await interaction.response.send_message(
                "❌ Failed to submit application due to a network error. Please try again later.",
                ephemeral=True
            )
            logger.error(f"HTTP error while submitting application: {e}")
            
        except Exception as e:
            await interaction.response.send_message(
                "❌ An unexpected error occurred. Please contact an administrator.",
                ephemeral=True
            )
            logger.error(f"Unexpected error in application submission: {e}")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """Handle modal errors"""
        await interaction.response.send_message(
            "❌ An error occurred while processing your application. Please try again.",
            ephemeral=True
        )
        logger.error(f"Modal error: {error}")


class ApplicationBot(commands.Bot):
    def __init__(self):
        # Define intents - only use non-privileged intents
        intents = discord.Intents.default()
        # Remove privileged intents to avoid permission errors
        intents.message_content = False
        
        super().__init__(
            command_prefix='!',  # Prefix for text commands (not used for slash commands)
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Setting up bot...")
        
        # Only sync commands if SYNC_COMMANDS environment variable is set to 'true'
        # This prevents rate limiting on every restart
        should_sync = os.getenv("SYNC_COMMANDS", "false").lower() == "true"
        
        if should_sync:
            try:
                print("🔄 Syncing slash commands...")
                logger.info("Syncing slash commands (SYNC_COMMANDS=true)")
                synced = await self.tree.sync()
                print(f"✅ Successfully synced {len(synced)} command(s)")
                logger.info(f"Synced {len(synced)} command(s)")
            except Exception as e:
                print(f"❌ Failed to sync commands: {e}")
                logger.error(f"Failed to sync commands: {e}")
        else:
            print("⏭️ Skipping command sync (SYNC_COMMANDS not set to 'true')")
            logger.info("Skipping command sync - set SYNC_COMMANDS=true to sync commands")

    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guild(s)')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for new guild applications"
            )
        )

    async def on_command_error(self, ctx, error):
        """Global error handler for text commands"""
        logger.error(f"Command error: {error}")


# Initialize bot
bot = ApplicationBot()


@bot.tree.command(name="apply", description="Submit an application to join the guild")
async def apply(interaction: discord.Interaction):
    """Slash command to open application modal"""
    try:
        # Check if user is already in a guild (optional check)
        # You can add additional checks here like cooldowns, role requirements, etc.
        
        # Create and send modal
        modal = ApplicationModal()
        await interaction.response.send_modal(modal)
        
        logger.info(f"Application modal opened by {interaction.user} ({interaction.user.id})")
        
    except discord.HTTPException as e:
        await interaction.response.send_message(
            "❌ Failed to open application form. Please try again later.",
            ephemeral=True
        )
        logger.error(f"HTTP error while opening modal: {e}")
        
    except Exception as e:
        await interaction.response.send_message(
            "❌ An unexpected error occurred. Please contact an administrator.",
            ephemeral=True
        )
        logger.error(f"Unexpected error in apply command: {e}")


@bot.tree.command(name="ping", description="Check if the bot is responsive")
async def ping(interaction: discord.Interaction):
    """Simple ping command for testing"""
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(
        f"🏓 Pong! Latency: {latency}ms",
        ephemeral=True
    )


@bot.tree.command(name="sync", description="Manually sync slash commands (Admin only)")
@app_commands.describe(
    guild_only="Whether to sync only to this guild (faster) or globally (slower)"
)
async def sync_commands(interaction: discord.Interaction, guild_only: bool = True):
    """Manual command sync for admins"""
    # Check if user has administrator permissions
    if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ You need administrator permissions to use this command.",
            ephemeral=True
        )
        return
    
    # Ensure we're in a guild
    if not interaction.guild:
        await interaction.response.send_message(
            "❌ This command can only be used in a server.",
            ephemeral=True
        )
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        if guild_only:
            # Sync to current guild only (faster, no rate limits)
            bot.tree.copy_global_to(guild=interaction.guild)
            synced = await bot.tree.sync(guild=interaction.guild)
            await interaction.followup.send(
                f"✅ Successfully synced {len(synced)} command(s) to this server only.",
                ephemeral=True
            )
            logger.info(f"Commands synced to guild {interaction.guild.id} by {interaction.user}")
        else:
            # Global sync (slower, may hit rate limits)
            synced = await bot.tree.sync()
            await interaction.followup.send(
                f"✅ Successfully synced {len(synced)} command(s) globally. May take up to 1 hour to appear everywhere.",
                ephemeral=True
            )
            logger.info(f"Commands synced globally by {interaction.user}")
            
    except Exception as e:
        await interaction.followup.send(
            f"❌ Failed to sync commands: {str(e)}",
            ephemeral=True
        )
        logger.error(f"Command sync failed: {e}")


# Error handler for slash commands
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Global error handler for slash commands"""
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"⏰ Command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
            ephemeral=True
        )
    elif isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ An error occurred while executing this command.",
            ephemeral=True
        )
        logger.error(f"App command error: {error}")


def main():
    """Main function to start the bot"""
    # Get bot token from environment
    token = os.getenv("TOKEN")
    
    if not token:
        logger.error("No bot token found! Please set the TOKEN environment variable.")
        print("ERROR: No bot token found!")
        print("Please create a .env file with your bot token:")
        print("TOKEN=your_bot_token_here")
        return
    
    # Validate configuration
    if GUILD_ID == 123456789012345678:
        logger.warning("Using default GUILD_ID. Please update it in the code.")
    
    if CHANNEL_ID == 987654321098765432:
        logger.warning("Using default CHANNEL_ID. Please update it in the code.")
    
    # Start the bot
    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Invalid bot token!")
        print("ERROR: Invalid bot token! Please check your TOKEN environment variable.")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")


if __name__ == "__main__":
    main()
