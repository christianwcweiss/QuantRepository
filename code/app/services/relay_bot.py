import threading
import asyncio
from typing import Any
import boto3

import discord
import json
from quant_core.services.core_logger import CoreLogger
from services.trade_parser import TradeMessageParser
from services.trade_router import TradeRouter

intents = discord.Intents.default()
intents.message_content = True


ALPHA_RAI_CHANNEL_IDS = ["1341053733446090753", "1341053733060087961", "1341053686217965779"]
ALPHA_RAI_WEBHOOKS_USER_IDS = ["116820183460347905", "1376589114417352774"]  # admin  # bot


class DiscordRelayBot:
    """Singleton class for managing a Discord bot that relays messages to the local app."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DiscordRelayBot, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        self._token = json.loads(self._get_credentials_from_secrets_manager("DISCORD_BOT_TOKEN"))["DISCORD_BOT_TOKEN"]

        self._thread = None
        self._loop = None
        self._client = None
        self._running = False

    def _get_credentials_from_secrets_manager(self, secret_name: str) -> str:
        secretsmanager_client = boto3.client("secretsmanager")
        secret_value = secretsmanager_client.get_secret_value(SecretId=secret_name)
        if "SecretString" in secret_value:
            return secret_value["SecretString"]
        raise ValueError(f"Secret {secret_name} not found.")

    def _build_client(self):
        client = discord.Client(intents=intents)

        @client.event
        async def on_ready():
            """Event handler for when the bot is ready and connected to Discord."""
            CoreLogger().info(f"Logged in as {client.user}")
            CoreLogger().info(f"Connected to {len(client.guilds)} server(s):")

            for guild in client.guilds:
                CoreLogger().info(f"Guild: {guild.name} (ID: {guild.id})")
                for channel in guild.text_channels:
                    CoreLogger().info(f"Channel: {channel.name} (ID: {channel.id})")

        @client.event
        async def on_message(message: Any) -> None:
            """Handle incoming messages and forward them to the local app."""

            CoreLogger().info(
                f"Received message from {message.author.name}/{message.author.id} in {message.channel.name}: {message.content}"  # noqa: E501
            )

            if str(message.author.id) not in ALPHA_RAI_WEBHOOKS_USER_IDS:
                return

            if str(message.channel.id) in ALPHA_RAI_CHANNEL_IDS:
                CoreLogger().info(f"Signal: {message.content}")

                trade = TradeMessageParser().parse(message.content)

                CoreLogger().info(f"Parsed trade {trade} successfully received from Discord.")

                TradeRouter(trade=trade).route()

        return client

    def run(self):
        """Start the Discord bot in a separate thread."""
        if self._running:
            CoreLogger().debug("Bot already running.")
            return

        def start_bot():
            try:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

                self._client = self._build_client()
                self._running = True

                self._loop.run_until_complete(self._client.start(self._token))
            except Exception as e:  # pylint: disable=broad-exception-caught
                CoreLogger().error(f"Bot crashed: {e}")
            finally:
                self._running = False
                if self._loop and not self._loop.is_closed():
                    self._loop.run_until_complete(self._client.close())
                    self._loop.close()

        self._thread = threading.Thread(target=start_bot, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the Discord bot if it is running."""
        if not self._running or not self._loop:
            CoreLogger().info("Bot is not running or no loop.")
            return

        CoreLogger().info("Stopping Discord bot...")
        asyncio.run_coroutine_threadsafe(self._client.close(), self._loop)

    def is_running(self) -> bool:
        """Check if the bot is currently running."""
        return self._running
