# base class that can listen to server messages

from abc import ABC, abstractmethod
from utils.server_parser import is_server_ready, player_joined, player_left, player_message, player_death, is_server_stopped


class Message:
    def __init__(self, id:int, content:str, raw_content:str, author:str="server", user_message:str|None=None):
        self.id:int = id
        self.content:str = content
        self.raw_content:str = raw_content
        self.author:str = author
        self.user_message:str|None = user_message

    def is_user_message(self) -> bool:
        return self.user_message is not None
    
    def __str__(self) -> str:
        return f"ServerMessage: {self.content}"
    
    def __repr__(self) -> str:
        return f"ServerMessage: {self.content}"
    

class AbstractWrapper(ABC):

    @abstractmethod
    def send_command(self, command:str) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass


class Listener:
    def __init__(self, wrapper:AbstractWrapper):
        self.wrapper:AbstractWrapper = wrapper

    def handle_message(self, message:Message) -> None:
        pass


class Logger(Listener):

    def __init__(self, wrapper:AbstractWrapper):
        super().__init__(wrapper)

        self.log_all_messages: bool = False
        self.log_player_messages: bool = False
        self.log_player_joins: bool = False
        self.log_player_leaves: bool = False
        self.log_server_start: bool = False
        self.log_server_stop: bool = False
        self.log_death_messages: bool = False

    def log(self, message:Message) -> None:
        pass

    def handle_message(self, message: Message) -> None:
        if self.log_all_messages:
            self.log(message)
            return
        
        if self.log_player_messages and message.is_user_message():
            self.log(message)
            return
        
        if self.log_server_start and is_server_ready(message.content):
            self.log(message)
            return
        
        if self.log_server_stop and is_server_stopped(message.content):
            self.log(message)
            return
        
        if self.log_player_joins:
            player = player_joined(message.content)
            if player is not None:
                self.log(message)
                return
            
        if self.log_player_leaves:
            player = player_left(message.content)
            if player is not None:
                self.log(message)
                return
            
        if self.log_death_messages:
            death = player_death(message.content)
            if death is not None:
                self.log(message)
                return
            
        print(message.content)





