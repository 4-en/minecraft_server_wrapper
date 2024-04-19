from utils.config import KVConfig
from dataclasses import dataclass
from typing import List
from extensions.listener import Listener, Message, Logger
from utils.server_parser import is_server_ready, is_server_stopped, player_joined, player_left, player_message
import requests
import os

CONFIG_NAME = "discord_hook.cfg"

@dataclass
class DiscordHookConfig(KVConfig):
    webhook_url: str = "None"
    log_all_messages: bool = False
    log_player_messages: bool = True
    log_player_joins: bool = True
    log_player_leaves: bool = True
    log_death_messages: bool = True
    log_server_start: bool = True
    log_server_stop: bool = True


class DiscordHook(Logger):
    def __init__(self, wrapper):
        super().__init__(wrapper)
        self.config = DiscordHookConfig()
        root = wrapper.get_current_directory()
        self.config.set_path(os.path.join(root, CONFIG_NAME))
        self.config.load_config()
        self.config.save_config()

        self.log_all_messages = self.config.log_all_messages
        self.log_player_messages = self.config.log_player_messages
        self.log_player_joins = self.config.log_player_joins
        self.log_player_leaves = self.config.log_player_leaves
        self.log_death_messages = self.config.log_death_messages
        self.log_server_start = self.config.log_server_start
        self.log_server_stop = self.config.log_server_stop

        self.enabled = self.config.webhook_url != "None"
        if not self.enabled:
            print("Discord hook is disabled. No webhook URL provided.")
        self.fails = 0

    def send_server_start(self):
        requests.post(self.config.webhook_url, json={"content": "*Server started*"})

    def send_server_stop(self):
        requests.post(self.config.webhook_url, json={"content": "*Server stopped*"})

    def send_player_join(self, player: str):
        requests.post(self.config.webhook_url, json={"content": f"**{player}** joined the server"})

    def send_player_leave(self, player: str):
        requests.post(self.config.webhook_url, json={"content": f"**{player}** left the server"})

    def send_player_message(self, player: str, message: str):
        requests.post(self.config.webhook_url, json={"content": f"<**{player}**> {message}"})

    def log(self, message: Message) -> None:
        if not self.enabled:
            return
        try:
            if is_server_ready(message.content):
                self.send_server_start()
            elif is_server_stopped(message.content):
                self.send_server_stop()
            elif player_joined(message.content):
                player = player_joined(message.content)
                if player is not None:
                    self.send_player_join(player)
            elif player_left(message.content):
                player = player_left(message.content)
                if player is not None:
                    self.send_player_leave(player)
            elif self.log_player_messages and message.is_user_message():
                player, msg = player_message(message.content)
                self.send_player_message(player, msg)
            else:
                requests.post(self.config.webhook_url, json={"content": message.content})
            self.fails = 0

        except Exception as e:
            print("Error sending message to discord webhook")
            print(e)
            self.fails += 1
            if self.fails >= 5:
                self.enabled = False
                print("Disabling discord hook")

    

    


