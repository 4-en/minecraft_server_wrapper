# main class for the wrapper
# handles server stdin/stdout and manages other modules

import os
import subprocess
import threading
import re
import datetime
import argparse
from utils.config import KVConfig, get_data_root
from components.updater import get_last_version, download_server_jar, find_version
from dataclasses import dataclass

CONFIG_FILE = "wrapper.cfg"


@dataclass
class WrapperConfig(KVConfig):
    """Wrapper configuration class"""

    comment1: str = "# Wrapper configuration"
    comment2: str = "# Format: key = value"
    comment3: str = "# Comments start with #"
    commentTimestamp: callable = lambda: "# Last updated: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    comment4: str = "#"
    comment7: str = "# server_version: current server version"
    server_version: str = "0.0"
    comment77: str = "# preferred_version: preferred server version"
    preferred_version: str = "latest"
    comment8: str = "# auto_update: automatically update server"
    auto_update: bool = False
    comment9: str = "# use_snapshot: True to use snapshot server"
    use_snapshot: bool = False
    comment10: str = "# auto_restart: automatically restart server when it closes without \"stop\" command"
    auto_restart: bool = True
    comment101: str = "# restart_delay: delay in seconds before restarting server"
    restart_delay: int = 5
    comment102: str = "# restart_attempts: number of restart attempts before giving up"
    restart_attempts: int = 5
    comment103: str = "# scheduled_restart: interval in hours to restart server"
    scheduled_restart: float = 0.0
    comment11: str = "# use_webhook: True to use discord webhook"
    use_webhook: bool = False


class Wrapper:

    def __init__(self, directory="default"):
        self.directory = directory
        self._load_config()

        self.running = False
        self._server_running = False
        self._process = None
        self._stdout = None
        self._stdin = None
        self._stdout_thread = None
        self._stdin_thread = None

    def _load_config(self):
        directory = self.directory  # directory of server
        data_root = get_data_root()  # data root directory

        self.full_directory = os.path.join(data_root, directory)

        # ensure that directory exists
        if not os.path.exists(self.full_directory):
            os.makedirs(self.full_directory)

        self.config = WrapperConfig()
        self.config.set_path(os.path.join(self.full_directory, CONFIG_FILE))
        self.config.load_config()
        self.config.save_config()

    def _get_start_command(self):
        return ["java", "-Xmx4096M", "-Xms1024M", "-jar", "server.jar", "nogui"]

    def _read_stdout(self):
        while self._server_running:
            line = self._stdout.readline()
            if line:
                print(line, end="")
                # Simulated process_line
                # self._process_line(line)
        print("stdout thread stopped")

    def _read_stdin(self):
        print("Type 'stop' to stop the server")
        while self.running:
            try:
                input_str = input()
                if input_str and self._server_running and self._stdin and self._stdin.writable():
                    self._stdin.write(input_str + "\n")
                    self._stdin.flush()
            except EOFError:
                return

    def _accept_eula(self):
        eula_file = os.path.join(self.full_directory, "eula.txt")
        with open(eula_file, "w") as f:
            f.write("#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA)." + "\n")
            f.write("#Thu Jan 01 00:00:00 UTC 1970" + "\n")
            f.write("eula=true\n")

    def _update_server(self) -> bool:
        version = self.config.server_version
        snapshot = self.config.use_snapshot
        directory = self.full_directory
        auto_update = self.config.auto_update
        preferred_version = self.config.preferred_version

        # check if server.jar exists
        server_jar = os.path.join(directory, "server.jar")
        jar_exists = os.path.exists(server_jar)
        
        # if no server.jar, update no matter what
        if not jar_exists:
            auto_update = True

        if not auto_update:
            return True
        
        # check if preferred version same as version
        if jar_exists:
            if version == preferred_version:
                return True
            
        # try to get version
        use_version = find_version(preferred_version, snapshot)

        if use_version and use_version != preferred_version:
            # probably a typo, change preferred version to use_version
            self.config.preferred_version = use_version

        # if no version found and no server.jar, use latest version
        if use_version is None and not jar_exists:
            use_version = get_last_version(snapshot)
        elif use_version is None:
            return True
        
        
        if use_version == version:
            return True
        
        # download server jar
        if download_server_jar(use_version, directory):
            self.config.server_version = use_version
            self.config.save_config()
            return True
        
        return False


    def _run_server(self):
        print("Starting server...")
        command = self._get_start_command()

        if self._process is not None:
            self._stop_threads()
            self._stdout_thread.join()

        # Here, subprocess.Popen creates new pipes for stdin, stdout, stderr
        self._process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            stdin=subprocess.PIPE, 
            text=True,
            bufsize=1, 
            cwd=self.full_directory
        )

        self._stdin = self._process.stdin
        self._stdout = self._process.stdout
        self._stderr = self._process.stderr

        print("Server process started...")
        self._server_running = True

        self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._stdout_thread.start()
        print("Server listener started...")

        self._process.wait()
        self._server_running = False
        self._stop_threads()
        print("Server closed")

        print("Waiting for threads to finish...")
        self._stdout_thread.join()
        self._stdin = None
        self._stdout = None
        print("Server fully stopped")

    def _stop_threads(self):
        self._server_running = False
        
        # close pipes
        if self._stdin:
            self._stdin.close()
        if self._stdout:
            self._stdout.close()


    def run(self):
        if self.running:
            return

        self.running = True

        # update server
        self._update_server()

        self._stdin_thread = threading.Thread(target=self._read_stdin, daemon=True, name="stdin_thread")
        self._stdin_thread.start()

        self._accept_eula() # TODO: actually ask user to accept eula
        while self.running:
            self._run_server()


        # save config
        self.config.save_config()
        print("Shutting down...")


def main():
    parser = argparse.ArgumentParser(description="Wrapper for Minecraft server")
    parser.add_argument("--directory", "-d", help="Server directory", default="default")
    args = parser.parse_args()

    wrapper = Wrapper(args.directory)
    wrapper.run()

if __name__ == "__main__":
    main()
