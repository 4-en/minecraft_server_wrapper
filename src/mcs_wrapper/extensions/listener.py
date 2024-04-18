# base class that can listen to server messages

from abc import ABC, abstractmethod


class Message:
    def __init__(self, id:int, content:str, raw_content:str):
        self.id:int = id
        self.content:str = content
        self.raw_content:str = raw_content

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