import re

# Parse and extract data from the server output
# regex patterns and functions that can be imported by other modules

# Check if the server is ready
_SERVER_READY = re.compile(r"Done \(\d+\.\d+s\)! For help, type \"help\"")

def is_server_ready(message: str) -> bool:
    return _SERVER_READY.match(message) is not None

# Check if a player joined the server
_PLAYER_JOINED = re.compile(r"(\w+) joined the game")
def player_joined(message: str) -> str | None:
    match = _PLAYER_JOINED.match(message)
    if match is not None:
        return match.group(1)
    return None

# Check if a player left the server
_PLAYER_LEFT = re.compile(r"(\w+) left the game")
def player_left(message: str) -> str | None:
    match = _PLAYER_LEFT.match(message)
    if match is not None:
        return match.group(1)
    return None

# Player message
# returns (player, message) or None if message is not from a player
def player_message(message: str) -> tuple[str, str] | None:
    # check if message starts with player name
    if message.startswith("<") and ">" in message:
        player_end = message.find(">")
        player = message[1:player_end]
        return player, message[player_end+2:]
    return None

# Player death message
# there are many different variations of death messages
# so we will have to do multiple checks
# TODO: add more death messages
_DEATH_MESSAGES = [
    re.compile(r"(\w+) died"),
    re.compile(r"(\w+) tried to swim in lava"),
    re.compile(r"(\w+) was pricked to death"),
    re.compile(r"(\w+) walked into a cactus whilst trying to escape (\w+)"),
    re.compile(r"(\w+) drowned"),
    re.compile(r"(\w+) drowned whilst trying to escape (\w+)"),
    re.compile(r"(\w+) was shot by arrow"),
    re.compile(r"(\w+) was shot by (\w+)"),
    re.compile(r"(\w+) was shot off a ladder by (\w+)"),
    re.compile(r"(\w+) was shot off some vines by (\w+)"),
    re.compile(r"(\w+) was shot off some twisting vines by (\w+)"),
    re.compile(r"(\w+) was blown up by (\w+)"),
    re.compile(r"(\w+) was blown up by (\w+) using (\w+)"),
    re.compile(r"(\w+) was blown up by (\w+) using magic"),
    re.compile(r"(\w+) was blown up by (\w+) using (\w+)"),
    re.compile(r"(\w+) was blown up by (\w+)"),
    re.compile(r"(\w+) was blown up by (\w+) using (\w+)"),
    re.compile(r"(\w+) was blown up by (\w+) using magic"),
    re.compile(r"(\w+) was killed by magic"),
    re.compile(r"(\w+) was killed by (\w+) using magic"),
    re.compile(r"(\w+) was killed by (\w+)"),
    re.compile(r"(\w+) was killed by (\w+) using (\w+)"),
    re.compile(r"(\w+) was killed by (\w+) using magic"),
    re.compile(r"(\w+) was killed by (\w+)"),
    re.compile(r"(\w+) was killed by (\w+) using (\w+)"),
    re.compile(r"(\w+) was killed by (\w+) using magic"),
    re.compile(r"(\w+) hit the ground too hard"),
    re.compile(r"(\w+) fell from a high place")
]

def player_death(message: str) -> str | None:
    for pattern in _DEATH_MESSAGES:
        match = pattern.match(message)
        if match is not None:
            return match.group(1)
    return None







