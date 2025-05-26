import os
import configparser
import datetime
import logging # Added for logging
import twitchio
from twitchio.ext import commands
from twitchio.errors import AuthenticationError # Specific import for the error

# Import custom modules
from audio_input import AudioRecorder
from screen_capture import ScreenCapture

class Bot(commands.Bot):

    def __init__(self):
        # Setup logging first
        self.logger = logging.getLogger('TwitchBot')
        self.logger.setLevel(logging.INFO)
        # Create logs directory if it doesn't exist
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        # File handler
        fh = logging.FileHandler(os.path.join(log_dir, 'bot_activity.log'))
        fh.setLevel(logging.INFO)
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # Add handlers to the logger
        if not self.logger.handlers: # Avoid adding multiple handlers on re-init if any
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

        self.config = configparser.ConfigParser()
        config_path = "config.ini" # Define path for easy reuse

        # Check if config.ini exists, create a template if not
        if not os.path.exists(config_path):
            self.logger.info(f"'{config_path}' not found. A template will be created.")
            self.config['Twitch'] = {
                'token': 'YOUR_OAUTH_TOKEN_HERE',
                'prefix': '!',
                'channel': 'YOUR_CHANNEL_NAME_HERE'
            }
            self.config['Personality'] = {
                'description': 'Your AI\'s personality description (e.g., friendly, witty, helpful)'
            }
            self.config['Rules'] = {
                'avoid_politics': 'true',
                'max_response_length': '150',
                'custom_greeting': 'Hello streamer! I\'m ready to assist.'
            }
            try:
                with open(config_path, 'w') as configfile:
                    self.config.write(configfile)
                self.logger.info(f"A template '{config_path}' has been created. "
                      "Please fill in your Twitch OAuth token and channel name, then restart the bot.")
            except IOError as e:
                self.logger.error(f"Could not create '{config_path}': {e}")
            exit() # Exit after attempting to create template or if creation fails

        # Read configuration from config.ini
        try:
            self.config.read(config_path)
            if not self.config.has_section('Twitch'):
                self.logger.error(f"Section [Twitch] not found in '{config_path}'.")
                self.logger.error("Please ensure your config.ini has a [Twitch] section with 'token', 'prefix', and 'channel' keys.")
                exit()
        except configparser.Error as e:
            self.logger.error(f"Could not parse '{config_path}': {e}")
            exit()

        twitch_config = self.config['Twitch']
        token = twitch_config.get('token')
        # Use a default prefix if not specified in config.ini or if it's empty
        prefix_from_config = twitch_config.get('prefix')
        # Ensure prefix is a string and not None; default to '!' if empty or missing
        self.prefix = prefix_from_config if prefix_from_config and prefix_from_config.strip() else '!'

        channel = twitch_config.get('channel')

        # Validate essential configuration
        if not token or token == 'YOUR_OAUTH_TOKEN_HERE':
            self.logger.error(f"Twitch token is missing or is still the placeholder in '{config_path}'.")
            self.logger.error("Please update it with your OAuth token (e.g., from twitchtokengenerator.com).")
            exit()
        if not channel or channel == 'YOUR_CHANNEL_NAME_HERE':
            self.logger.error(f"Twitch channel is missing or is still the placeholder in '{config_path}'. Please update it.")
            exit()

        # Initialize the Bot (parent class)
        super().__init__(token=token, prefix=self.prefix, initial_channels=[channel])
        self.chat_messages = []  # Initialize list for storing chat messages
        
        # Initialize custom modules
        try:
            self.audio_recorder = AudioRecorder()
            self.logger.info("AudioRecorder initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize AudioRecorder: {e}", exc_info=True)
            self.audio_recorder = None # Ensure it's None if failed
        
        try:
            self.screen_capturer = ScreenCapture()
            self.logger.info("ScreenCapture initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize ScreenCapture: {e}", exc_info=True)
            self.screen_capturer = None # Ensure it's None if failed

        self.logger.info(f"Bot core initialized. Prefix: '{self.prefix}', Channel: '{channel}'")
        
        # Load extended configuration for personality and rules
        self.load_extended_config()


    def load_extended_config(self):
        """Loads personality and rules settings from config.ini."""
        self.logger.info("Loading extended configuration (Personality & Rules)...")
        self.personality_description = self.config.get('Personality', 'description', 
                                                       fallback='Default AI Personality: Helpful and friendly.')
        if self.personality_description == 'Default AI Personality: Helpful and friendly.':
            self.logger.info("Personality description not found or default. Using fallback.")
        
        self.rules_config = {}
        if self.config.has_section('Rules'):
            # Load boolean values
            self.rules_config['avoid_politics'] = self.config.getboolean('Rules', 'avoid_politics', fallback=False)
            
            # Load integer values
            try:
                self.rules_config['max_response_length'] = self.config.getint('Rules', 'max_response_length', fallback=150)
            except ValueError:
                self.logger.warning("'max_response_length' in [Rules] is not a valid integer. Using fallback 150.")
                self.rules_config['max_response_length'] = 150
            
            # Load string values
            self.rules_config['custom_greeting'] = self.config.get('Rules', 'custom_greeting', 
                                                                   fallback='Hello! How can I help?')
            # Example for loading any other rule as a string if present
            for key in self.config['Rules']:
                if key not in self.rules_config: # Avoid overwriting explicitly typed ones
                    self.rules_config[key] = self.config.get('Rules', key)
            self.logger.info("Successfully loaded [Rules] section.")
        else:
            self.logger.info("[Rules] section not found in config.ini. Using default rules.")
            self.rules_config = {
                'avoid_politics': False,
                'max_response_length': 150,
                'custom_greeting': 'Hello! How can I help?'
            }
        
        self.logger.info("Extended configuration loaded.")

    async def event_ready(self):
        # Called once the bot is successfully connected to Twitch
        self.logger.info(f"Logged in as | {self.nick}")
        self.logger.info(f"User ID is | {self.user_id}")
        if self.initial_channels:
             self.logger.info(f"Successfully joined channel | {self.initial_channels[0]}")
        else:
            # This case should ideally not be reached if __init__ validation is correct
            self.logger.warning("No initial channel was joined. Check config.ini.")
        
        # Print loaded personality and rules for verification
        self.logger.info("-" * 30)
        self.logger.info("Loaded Bot Configuration:")
        self.logger.info(f"  Personality: {self.personality_description}")
        self.logger.info(f"  Rules Config: {self.rules_config}")
        self.logger.info("-" * 30)


    async def event_message(self, message: twitchio.Message):
        # Handles messages sent in chat
        if message.echo: # message.echo is True if the message is from the bot itself
            return

        # Log message for real-time visibility and storage
        mod_status = "(Mod)" if message.author.is_mod else ""
        sub_status = "(Sub)" if message.author.is_subscriber else ""
        timestamp_str = datetime.datetime.utcnow().isoformat() + 'Z'
        channel_name = message.channel.name if message.channel else "UnknownChannel"

        log_message_content = f"#{channel_name} | {message.author.name} {mod_status}{sub_status}: {message.content}"
        self.logger.info(log_message_content) # Log to console and file

        # Store message details (limited to last N messages for feedback commands)
        MAX_STORED_MESSAGES = 20 
        self.chat_messages.append({
            'author': message.author.name,
            'content': message.content,
            'timestamp': timestamp_str,
            'channel': channel_name,
            'is_mod': message.author.is_mod,
            'is_subscriber': message.author.is_subscriber,
            'raw_log_message': log_message_content # Store the formatted log message for context
        })
        if len(self.chat_messages) > MAX_STORED_MESSAGES:
            self.chat_messages.pop(0) # Remove the oldest message

        # Handle commands using the bot's prefix
        if message.content and message.content.startswith(self.prefix):
            # Updated log to include channel name
            self.logger.info(f"Attempting to handle command: {message.content} from {message.author.name} in channel {channel_name}")
            await self.handle_commands(message)

    @commands.command(name='hello')
    async def hello_command(self, ctx: commands.Context):
        self.logger.info(f"'!hello' command invoked by {ctx.author.name} in #{ctx.channel.name}.")
        try:
            await ctx.send(f"Hello {ctx.author.name}!")
            self.logger.info(f"Successfully sent hello response to {ctx.author.name} in #{ctx.channel.name}.")
        except Exception as e:
            self.logger.error(f"Error processing '!hello' command for {ctx.author.name} in #{ctx.channel.name}: {e}")

    # Broadcaster only commands decorator
    def is_broadcaster():
        async def predicate(ctx: commands.Context) -> bool:
            if not ctx.author.is_broadcaster:
                await ctx.send(f"Sorry {ctx.author.name}, this command is for the broadcaster only.")
                return False
            return True
        return commands.check(predicate)

    @commands.command(name='screenshot')
    @is_broadcaster()
    async def screenshot_command(self, ctx: commands.Context):
        self.logger.info(f"'!screenshot' command invoked by broadcaster {ctx.author.name} in #{ctx.channel.name}.")
        if not self.screen_capturer:
            self.logger.error("ScreenCapturer not initialized. Cannot take screenshot.")
            await ctx.send("Sorry, the screenshot module is not available at the moment.")
            return
            
        try:
            filepath = self.screen_capturer.capture_screen() # This method logs success/failure internally too
            if filepath:
                # Log specific to Twitch command success
                self.logger.info(f"Screenshot successfully taken and saved via Twitch command: {filepath}")
                await ctx.send(f"Screenshot saved to {filepath}")
            else:
                # Log specific to Twitch command failure if capture_screen returned None
                self.logger.error("Failed to take screenshot via Twitch command (capture_screen returned None or empty).")
                await ctx.send("Sorry, failed to take a screenshot. Please check bot logs for more details.")
        except Exception as e:
            self.logger.error(f"Exception during !screenshot command execution: {e}", exc_info=True)
            await ctx.send("An error occurred while taking the screenshot. Please check bot logs.")

    @commands.command(name='startaudio')
    @is_broadcaster()
    async def start_audio_command(self, ctx: commands.Context):
        self.logger.info(f"'!startaudio' command invoked by broadcaster {ctx.author.name} in #{ctx.channel.name}.")
        if not self.audio_recorder:
            self.logger.error("AudioRecorder not initialized. Cannot start recording.")
            await ctx.send("Sorry, the audio recording module is not available at the moment.")
            return

        if self.audio_recorder.is_recording:
            self.logger.info("Audio recording already in progress when !startaudio was called by broadcaster.")
            await ctx.send("Audio recording is already in progress.")
            return
        
        try:
            # AudioRecorder's start_recording method should handle its own internal logging
            self.audio_recorder.start_recording() 
            self.logger.info("Audio recording process initiated by broadcaster via Twitch command.")
            await ctx.send("Audio recording started.")
        except Exception as e: 
            self.logger.error(f"Exception during !startaudio command execution: {e}", exc_info=True)
            await ctx.send("An error occurred while trying to start audio recording. Please check bot logs.")

    @commands.command(name='stopaudio')
    @is_broadcaster()
    async def stop_audio_command(self, ctx: commands.Context):
        self.logger.info(f"'!stopaudio' command invoked by broadcaster {ctx.author.name} in #{ctx.channel.name}.")
        if not self.audio_recorder:
            self.logger.error("AudioRecorder not initialized. Cannot stop recording.")
            await ctx.send("Sorry, the audio recording module is not available at the moment.")
            return

        if not self.audio_recorder.is_recording:
            self.logger.info("Audio recording was not active when !stopaudio was called by broadcaster.")
            await ctx.send("Audio recording was not active.")
            return

        try:
            # AudioRecorder's stop_recording method should handle its own internal logging regarding file saving
            filepath = self.audio_recorder.stop_recording() 
            if filepath:
                self.logger.info(f"Audio recording stopped and saved via Twitch command by broadcaster. File: {filepath}")
                await ctx.send(f"Audio recording stopped. Saved to {filepath}")
            else:
                self.logger.warning("Stop audio command by broadcaster processed, but no filepath returned (e.g., no frames captured or save failed).")
                await ctx.send("Audio recording stopped. No audio was captured or file could not be saved. Check logs.")
        except Exception as e:
            self.logger.error(f"Exception during !stopaudio command execution: {e}", exc_info=True)
            await ctx.send("An error occurred while trying to stop audio recording. Please check bot logs.")
            
    @commands.command(name='showconfig')
    @is_broadcaster()
    async def show_config_command(self, ctx: commands.Context):
        self.logger.info(f"'!showconfig' command invoked by broadcaster {ctx.author.name} in #{ctx.channel.name}.")
        
        async def send_chunked_message(chat_context, prefix, data_to_send):
            """ Helper to send potentially long messages in chunks. """
            MAX_MSG_LEN = 450 # Twitch char limit is 500, this provides buffer
            
            if isinstance(data_to_send, dict):
                content_str = ", ".join([f"{k}='{v}'" for k, v in data_to_send.items()])
                if not content_str: content_str = "Not set or empty."
            elif isinstance(data_to_send, str):
                content_str = data_to_send.strip() if data_to_send and data_to_send.strip() else "Not set or empty."
            else:
                content_str = str(data_to_send)

            full_message = f"{prefix}: {content_str}"
            
            for i in range(0, len(full_message), MAX_MSG_LEN):
                chunk = full_message[i:i+MAX_MSG_LEN]
                await chat_context.send(chunk)
                # Optional: small delay if sending multiple chunks rapidly, though usually not needed for a few.
                # await asyncio.sleep(0.1) 

        try:
            # Twitch Config
            twitch_details = {
                "Bot Username": self.nick if self.nick else "N/A",
                "Command Prefix": f"'{self.prefix}'",
                "Target Channel": f"'{self.initial_channels[0] if self.initial_channels else 'N/A'}'"
            }
            await send_chunked_message(ctx, "Twitch Config", twitch_details)
            
            # Personality Config
            await send_chunked_message(ctx, "Personality", self.personality_description)
            
            # Rules Config
            await send_chunked_message(ctx, "Rules", self.rules_config)
            
            self.logger.info("Configuration details successfully sent to chat via !showconfig by broadcaster.")
            
        except Exception as e:
            self.logger.error(f"Error displaying configuration via !showconfig: {e}", exc_info=True)
            await ctx.send("Sorry, an error occurred while trying to display the configuration. Check logs.")

    @commands.command(name='goodbotresponse')
    async def good_bot_response_command(self, ctx: commands.Context):
        self.logger.info(f"User {ctx.author.name} in #{ctx.channel.name} marked a recent interaction as GOOD.")
        await ctx.send(f"Thanks for the feedback, {ctx.author.name}! Glad I could help. :)")
        
        # Log recent chat messages for context
        if self.chat_messages:
            self.logger.info("Recent chat context for GOOD response:")
            # Log last N messages, or fewer if not that many exist
            num_messages_to_log = min(len(self.chat_messages), 5) 
            for msg_idx in range(len(self.chat_messages) - num_messages_to_log, len(self.chat_messages)):
                chat_msg = self.chat_messages[msg_idx]
                self.logger.info(f"  Context: {chat_msg.get('raw_log_message', f'{chat_msg['author']}: {chat_msg['content']}')}")
        else:
            self.logger.info("No recent chat messages in buffer to log for context.")

    @commands.command(name='badbotresponse')
    async def bad_bot_response_command(self, ctx: commands.Context, *, reason: str = "No reason provided"):
        self.logger.warning(f"User {ctx.author.name} in #{ctx.channel.name} marked a recent interaction as BAD. Reason: {reason}")
        await ctx.send(f"Thanks for the feedback, {ctx.author.name}. I'll try to do better. Your reason: '{reason}' has been noted.")

        # Log recent chat messages for context
        if self.chat_messages:
            self.logger.info("Recent chat context for BAD response:")
            num_messages_to_log = min(len(self.chat_messages), 5)
            for msg_idx in range(len(self.chat_messages) - num_messages_to_log, len(self.chat_messages)):
                chat_msg = self.chat_messages[msg_idx]
                self.logger.info(f"  Context: {chat_msg.get('raw_log_message', f'{chat_msg['author']}: {chat_msg['content']}')}")
        else:
            self.logger.info("No recent chat messages in buffer to log for context.")


# Main entry point
if __name__ == "__main__":
    # Setup a basic logger for the main execution block, in case Bot init fails early
    # This logger won't have file output unless Bot's logger is successfully initialized and passed
    main_logger = logging.getLogger('main_startup')
    main_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main_ch = logging.StreamHandler()
    main_ch.setFormatter(main_formatter)
    main_logger.addHandler(main_ch)
    main_logger.setLevel(logging.INFO)

    if not os.path.exists("config.ini"):
        main_logger.info("'config.ini' not found. The bot will attempt to create a template during initialization.")
    
    bot_instance = None # Initialize bot_instance for access in finally block
    try:
        bot_instance = Bot() # Bot initialization now handles config loading and validation
        bot_instance.run()
    except AuthenticationError:
        # Use bot's logger if available, otherwise main_logger
        logger_to_use = bot_instance.logger if bot_instance and hasattr(bot_instance, 'logger') else main_logger
        logger_to_use.error("Fatal Error: Twitch authentication failed. This is likely due to an invalid or expired OAuth token.")
        logger_to_use.error("Please verify your 'token' in 'config.ini'. A new token can be generated from twitchtokengenerator.com.")
    except configparser.Error as e:
        logger_to_use = bot_instance.logger if bot_instance and hasattr(bot_instance, 'logger') else main_logger
        logger_to_use.error(f"Fatal Error: Problem processing 'config.ini': {e}")
    except FileNotFoundError:
        logger_to_use = bot_instance.logger if bot_instance and hasattr(bot_instance, 'logger') else main_logger
        logger_to_use.error("Fatal Error: 'config.ini' was not found during bot startup and template creation might have failed.")
    except Exception as e:
        logger_to_use = bot_instance.logger if bot_instance and hasattr(bot_instance, 'logger') else main_logger
        logger_to_use.error(f"An unexpected fatal error occurred during bot setup or run: {e}", exc_info=True)
    finally:
        logger_to_use = bot_instance.logger if bot_instance and hasattr(bot_instance, 'logger') else main_logger
        logger_to_use.info("Bot has shut down.")
