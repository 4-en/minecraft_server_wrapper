# main class for the wrapper
# handles server stdin/stdout and manages other modules

import os
import subprocess
import threading
import re
import datetime
import argparse
from utils.config import KVConfig, get_data_root
from dataclasses import dataclass, field


CONFIG_FILE = "wrapper.cfg"


@dataclass
class WrapperConfig(KVConfig):
    """Wrapper configuration class"""

    comment1: str = "# Wrapper configuration"
    comment2: str = "# Format: key = value"
    comment3: str = "# Comments start with #"
    commentTimestamp: callable = lambda: "# Last updated: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    comment4: str = "#"
    comment5: str = "# Wrapper settings"
    comment6: str = "#"
    comment7: str = "# server_version: current server version"
    server_version: str = "0.0"
    comment8: str = "# auto_update: automatically update server"
    auto_update: bool = False
    comment9: str = "# use_snapshot: True to use snapshot server"
    use_snapshot: bool = False
    comment10: str = "# auto_restart: automatically restart server when it closes without \"stop\" command"
    auto_restart: bool = True
    comment11: str = "# use_webhook: True to use webhook"
    use_webhook: bool = False


class Wrapper:

    def __init__(self, directory="default"):
        self.directory = directory
        self._load_config()

    def _load_config(self):
        directory = self.directory # directory of server
        data_root = get_data_root() # data root directory

        full_directory = os.path.join(data_root, directory)

        # ensure that directory exists
        if not os.path.exists(full_directory):
            os.makedirs(full_directory)

        self.config = WrapperConfig()
        self.config.set_path(os.path.join(full_directory, CONFIG_FILE))
        self.config.load_config()
        self.config.save_config()


def main():
    parser = argparse.ArgumentParser(description="Wrapper for Minecraft server")
    parser.add_argument("--directory", "-d", help="Server directory", default="default")
    args = parser.parse_args()

    wrapper = Wrapper(args.directory)

if __name__ == "__main__":
    main()
