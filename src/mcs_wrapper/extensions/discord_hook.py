from ..utils.config import KVConfig
from dataclasses import dataclass
from typing import List
from listener import Listener, Message
import requests

CONFIG_NAME = "discord_hook.cfg"

@dataclass
class DiscordHookConfig(KVConfig):
    webhook_url: str = "None"
    log_all_messages: bool = False
    log_player_messages: bool = False
    log_player_joins: bool = False
    log_player_leaves: bool = False
    log_server_start: bool = False
    log_server_stop: bool = False


class DiscordHook(Listener):
    def __init__(self):
        self.config = DiscordHookConfig(CONFIG_NAME)
        self.config.load_config()

    def handle_message(self, message: Message) -> None:
        if self.config.log_all_messages:
            self.send_discord_message(message.content)
        elif message.is_user_message():
            if self.config.log_player_messages:
                self.send_discord_message(message.content)
        else:
            if self.config.log_server_start and message.content == "Server started!":
                self.send_discord_message("Server has finished starting!")
            elif self.config.log_player_joins and "joined the server!" in message.content:
                self.send_discord_message(message.content)
            elif self.config.log_player_leaves and "left the server!" in message.content:
                self.send_discord_message(message.content)
            elif self.config.log_server_stop and message.content == "Server stopped!":
                self.send_discord_message("Server has stopped!")

    def send_discord_message(self, message: str) -> None:
        pass

    


