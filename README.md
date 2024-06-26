# Minecraft Server Wrapper

This Minecraft Server Wrapper is a Python script designed to manage Minecraft server operations and enhance functionality with various extensions and automation. The wrapper handles server input/output, manages configurations, automates updates, restarts, and integrates with Discord through webhooks. Additionally, it can summon Herobrine, providing a unique twist for players.

## Features

- **Auto-update**: Automatically updates the server to the latest or preferred Minecraft server version.
- **Auto-restart**: Automatically restarts the server when it closes unexpectedly.
- **Scheduled Restarts**: Configurable to restart the server at scheduled intervals.
- **Discord Integration**: Sends server events to a configured Discord channel.
- **Herobrine Integration**: Adds a spooky Herobrine experience to your server.
- **Configurable Settings**: Customizable settings through a configuration file.

## TODOs

- **Custom Commands**: Extension to create custom commands in python by listening to player chat.
- **Ask Command**: Use LLM to ask Minecraft specific questions.
- **Backups**: Automatically backup world.

## Requirements

- `requests` for discord_hook extension
- `openai` for herobrine extension

## Installation

1. Install Module:
   ```bash
   pip install git+https://github.com/yourgithubusername/minecraft-server-wrapper.git
   ```
2. Run the Program:
   ```bash
   mcs-wrapper
   ```
   or
   ```bash
   mcsw
   ```

## Configuration

1. Modify `wrapper.cfg` in the project root to set up your preferences:
   - Set server version, enable auto-updates, and configure webhook URLs.
   - Adjust auto-restart behaviors and Herobrine settings as desired.

## Usage

1. Start the wrapper with the specified server directory:
   ```bash
   mcsw -d directory_name
   ```
  Directory_name is a directory in the .mcs_wrapper directory

2. After the first start, you can edit the config files in your directory.
