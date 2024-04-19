from extensions.listener import Listener, Message
from utils.config import KVConfig
import requests
import openai
import os
from dataclasses import dataclass
import time
import random

_INSTRUCTION = """You are Herobrine, a mysterious entity that haunts the world of Minecraft. You have the power to manipulate the world around you and send messages to the other players.
Your goal is to cause chaos and confusion, and most importantly, to scare the other players. Try to be as spooky as possible. Act like a mixture of Pennywise and Jigsaw.
If the players try to speak to you, you can reply to them with spooky messages. Don't help them, but try to trick them into doing your dark biddings. Reply in plain text only."""

@dataclass
class HerobrineConfig(KVConfig):
    api_key: str = "None"
    trigger_word: str = "None"
    send_messages: bool = True
    hurt_players: bool = True
    break_blocks: bool = True
    reply_chance: float = 0.2

class Herobrine(Listener):
    
    def __init__(self, wrapper, instruction=_INSTRUCTION):
        super().__init__(wrapper)
        self.config = HerobrineConfig()
        root = wrapper.get_current_directory()
        self.config.set_path(os.path.join(root, "herobrine.cfg"))
        self.config.load_config()
        self.config.save_config()
        self.instruction = instruction
        
        self.enabled = self.config.api_key != "None"
        self.client = None
        if self.enabled:
            self.client = openai.OpenAI(api_key=self.config.api_key)
        else:
            print("Herobrine extension is disabled. No API key provided.")

    def handle_message(self, message: Message) -> None:
        if not self.enabled:
            return
        if not message.is_user_message() or "<Herobrine>" in message.content:
            return
        if self.config.trigger_word != "None" and self.config.trigger_word not in message.content:
            return
        
        reply_chance = self.config.reply_chance
        if self.config.trigger_word in message.content:
            reply_chance = 1.0

        do_reply = random.random() < reply_chance
        if not do_reply:
            return

        messages = self.wrapper.get_chat_history(5)
        if len(messages) == 0:
            print("No messages to generate text from")
            return
        
        do_action = random.random() < 0.5
        if do_action:
            player = "@a"
            if random.random() < 0.5 and messages[-1].is_user_message():
                player = messages[-1].author
            self.random_action(player)
            return

        response = self.generate_spooky_text(messages)
        if response:
            self.send_message(response)

    def play_spooky_sound(self, player: str = "@a") -> None:
        sounds = [
            "minecraft:entity.enderman.stare",
            "minecraft:entity.ghast.scream",
            "minecraft:entity.illusioner.ambient",
            "minecraft:entity.vex.ambient",
            "minecraft:entity.witch.ambient",
            "minecraft:entity.zombie_villager.ambient"
        ]
        sound = random.choice(sounds)
        self.wrapper.send_command(f"execute at {player} run playsound {sound} hostile {player}")

    def give_spooky_effect(self, player: str = "@a") -> None:
        effects = [
            "minecraft:glowing",
            "minecraft:blindness",
            "minecraft:nausea",
            "minecraft:levitation",
            "minecraft:slowness",
            "minecraft:poison",
            "minecraft:wither"
        ]
        effect = random.choice(effects)
        self.wrapper.send_command(f"effect give {player} {effect} 10 1")

    def strike_lightning(self, player: str = "@a") -> None:
        self.wrapper.send_command(f"execute at {player} run summon minecraft:lightning_bolt")

    def spawn_minion(self, player: str = "@a") -> None:
        minion_of_the_dark = [
            "minecraft:zombie",
            "minecraft:skeleton",
            "minecraft:spider",
            "minecraft:cave_spider",
            "minecraft:witch",
            "minecraft:vex",
            "minecraft:phantom",
            "minecraft:enderman"
        ]
        minion = random.choice(minion_of_the_dark)
        self.wrapper.send_command(f"execute at {player} run summon {minion}")

    def send_title(self, title: str, player: str = "@a") -> None:
        self.wrapper.send_command(f"title {player} title {title}")

    def random_action(self, player: str = "@a") -> None:
        actions = [
            self.play_spooky_sound,
            self.give_spooky_effect,
            self.strike_lightning,
            self.spawn_minion
        ]
        action = random.choice(actions)
        action(player)

    def generate_spooky_text(self, messages: list[Message]) -> str | None:
        try:
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.instruction},
                    *[
                        {
                            "role": "assistant" if "Herobrine" in message.author else "user",
                            "content": message.content,
                            "name": message.author
                        } for message in messages
                    ]
                ],
                max_tokens=64,
                temperature=1.3
            )
            if completion.choices[0].message.content.startswith("<Herobrine> "):
                return completion.choices[0].message.content[12:]
            return completion.choices[0].message.content
        except Exception as e:
            print("Failed to generate text")
            return None

    def send_message(self, message: str) -> None:
        if message == None or message == "":
            return
        # remove all non ascii characters
        message = "".join(i for i in message if ord(i) < 128)

        if message.startswith("/"):
            self.wrapper.send_command(message[1:])
            return
        
        # add this message to the log[22:58:59] [Server thread/INFO]:
        fake_log = f"[{time.strftime('%H:%M:%S')}] [Server thread/INFO]: <Herobrine> {message}"
        self.wrapper._handle_line(fake_log)
        
        self.wrapper.send_command(f"tellraw @a \"<Herobrine> {message}\"")