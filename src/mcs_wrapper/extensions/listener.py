# base class that can listen to server messages

from abc import ABC, abstractmethod


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
