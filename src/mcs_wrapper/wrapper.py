# main class for the wrapper
# handles server stdin/stdout and manages other modules

import os
import subprocess
import threading
import time
import re
import datetime
import argparse
from .utils.config import KVConfig, get_data_root
from .extensions.updater import get_last_version, download_server_jar, find_version
from .extensions.listener import Listener, AbstractWrapper, Message
from dataclasses import dataclass
from .utils.server_parser import player_message, is_server_ready
from .utils.cyclic_list import CyclicList
from .extensions.discord_hook import DiscordHook
from .extensions.herobrine import Herobrine

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
    use_herobrine: bool = False


class Wrapper(AbstractWrapper):

    def __init__(self, directory="default"):
        self.directory: str = directory
        self._load_config()

        self.running = False
        self._server_running = False
        self._process = None
        self._stdout = None
        self._stdin = None
        self._stdout_thread = None
        self._stdin_thread = None

        self._listeners: list[Listener] = []
        self._next_message_id = 0

        self.raw_messages = CyclicList(100)
        self.messages = CyclicList(100)
        #self.player_messages = CyclicList(100)
        self.player_messages = []

        self._restart_scheduler = None
        self._running_lock = threading.Lock()
        self._server_ready_lock = threading.Lock()
        self._server_ready_lock_acquired = False


    def add_listener(self, listener: Listener):
        self._listeners.append(listener)

    def remove_listener(self, listener: Listener):
        self._listeners.remove(listener)

    def sleep(self, seconds: float):
        if not self._server_running:
            raise Exception("You can't sleep using this method when the server is not running")

        finished_sleeping = False
        finished_sleeping = not self._running_lock.acquire(blocking=True, timeout=seconds)
        if not finished_sleeping:
            self._running_lock.release()
        return finished_sleeping
    
    def wait_for_server_ready(self):
        if not self._server_running:
            raise Exception("You can't wait for server ready when the server is not running")

        self._server_ready_lock.acquire()
        # if we can acquire the lock, it means the server is ready
        self._server_ready_lock.release()

    def get_current_directory(self):
        return self.full_directory

    def _load_config(self):
        directory = self.directory  # directory of server
        data_root = get_data_root()  # data root directory


        self.full_directory = os.path.join(data_root, directory)

        # ensure that directory exists
        if not os.path.exists(self.full_directory):
            os.makedirs(self.full_directory)

        # load default config
        def_config_name = os.path.join(data_root, "default.cfg")
        if not os.path.exists(def_config_name):
            def_config = WrapperConfig()
            def_config.set_path(def_config_name)
        else:
            def_config = WrapperConfig()
            def_config.set_path(def_config_name)
            def_config.load_config()

        def_config.save_config()

        self.config = WrapperConfig()
        self.config.set_path(os.path.join(self.full_directory, CONFIG_FILE))

        # check if config exists
        if not os.path.exists(self.config.get_path()):
            # copy default config to server directory
            self.config = def_config
            self.config.set_path(os.path.join(self.full_directory, CONFIG_FILE))
        else:
            self.config.load_config()

        self.config.save_config()

    def _get_start_command(self):
        return ["java", "-Xmx4096M", "-Xms1024M", "-jar", "server.jar", "nogui"]
    
    def _handle_line(self, line):
        # remove [Not Secure]
        line = line.replace("[Not Secure]", "")
        print(line)

        line_raw = line

        # remove time and server thread info prefix: eg. [22:58:59] [Server thread/INFO]:
        line_start = line.find("] ") + 2
        line_start = line.find("]: ", line_start) + 3

        if line_start != -1:
            line = line[line_start:]
            if self._server_ready_lock_acquired and is_server_ready(line):
                self._server_ready_lock.release()
                self._server_ready_lock_acquired = False
        else:
            line = None

        message = Message(self._next_message_id, line, line_raw)
        self.raw_messages.append(message)

        # check if it was a player message
        if line is not None:
            self.messages.append(message)
            pm = player_message(line)
            if pm:
                message.author = pm[0]
                message.user_message = pm[1]
                self.player_messages.append(message)

        self._next_message_id += 1

        for listener in self._listeners:
            listener.handle_message(message)


    def _read_stdout(self):
        while self._server_running:
            line = self._stdout.readline()
            if line:
                line = line.strip()
                self._handle_line(line)

        print("stdout thread stopped")

    def send_command(self, command: str):
        if self._stdin and self._stdin.writable():
            self._stdin.write(command + "\n")
            self._stdin.flush()

    def get_chat_history(self, n=10) -> list[Message]:
        n = min(n, len(self.player_messages))
        if n == 0:
            return []
        
        
        return self.player_messages[-n:]
    


    def stop(self):
        self.running = False
        self.send_command("stop")

    def _read_stdin(self):
        print("Type 'stop' to stop the server")
        while self.running:
            try:
                input_str = input()
                if input_str and self._server_running and self._stdin and self._stdin.writable():
                    self._stdin.write(input_str + "\n")
                    self._stdin.flush()

                    # special case:
                    # if input_str is "stop", stop server even if auto_restart is True
                    if input_str.lower() == "stop":
                        self.running = False

            except EOFError:
                return

    def _accept_eula(self):
        eula_file = os.path.join(self.full_directory, "eula.txt")
        with open(eula_file, "w") as f:
            f.write("#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA)." + "\n")
            f.write("#Thu Jan 01 00:00:00 UTC 1970" + "\n")
            f.write("eula=true\n")

    def _load_builtin_extensions(self):
        # load built-in extensions
        if self.config.use_webhook:
            self.add_listener(DiscordHook(self))

        if self.config.use_herobrine:
            self.add_listener(Herobrine(self))


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
        print(f"Downloading server.jar for version {use_version}")
        if download_server_jar(use_version, directory):
            print(f"Downloaded server.jar for version {use_version}")
            self.config.server_version = use_version
            self.config.save_config()
            return True
        else:    
            print(f"Failed to download server.jar for version {use_version}")
        
        return False


    def _server_stopped(self):
        # when the server stops, decide whether to restart it
        # if not, set running to False
        if self.config.auto_restart and self.running:
            print("Restarting server...")
        else:
            self.running = False

    def _start_restart_scheduler(self):
        interval = self.config.scheduled_restart

        if interval <= 0:
            return
        

        warnings = [10, 20, 30, 60, 5*60]

        warnings = sorted(warnings, reverse=True)
        def sec_to_hms_str(seconds):
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60

            hours = int(hours)
            minutes = int(minutes)
            seconds = int(seconds)

            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"

        def scheduler_task():
            seconds_until_restart = interval * 3600
            self.wait_for_server_ready()
            self.send_command(f"say Server will restart in {sec_to_hms_str(seconds_until_restart)}")
            while self._server_running and seconds_until_restart > 0:
                next_warning = 0
                warning_index = 0
                while warning_index < len(warnings):
                    if warnings[warning_index] < seconds_until_restart:
                        next_warning = warnings[warning_index]
                        break
                    warning_index += 1
                
                if next_warning == 0:
                    warning_index = -1

                sleep_time = seconds_until_restart - next_warning
                if sleep_time > 0:
                    sleep_completed = self.sleep(sleep_time)
                    if sleep_completed:
                        seconds_until_restart -= sleep_time
                    else:
                        return
                    
                if seconds_until_restart <= 1:
                    self.send_command("say Server is restarting...")
                    self.send_command("stop")
                    return
                    
                if warning_index > -1 and warning_index < len(warnings):
                    self.send_command(f"say Server will restart in {sec_to_hms_str(seconds_until_restart)}")


        self._restart_scheduler = threading.Thread(target=scheduler_task, daemon=True, name="restart_scheduler")
        self._restart_scheduler.start()

    def _run_server(self):
        print("Starting server...")
        command = self._get_start_command()

        if self._process is not None:
            self._clean_server_services()
            self._stdout_thread.join()

        # aquire lock
        lock_aquired = self._running_lock.acquire()
        self._server_ready_lock_acquired = self._server_ready_lock.acquire()

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

        self._server_running = True

        self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._stdout_thread.start()

        if self.config.scheduled_restart > 0:
            self._start_restart_scheduler()

        self._process.wait()
        self._server_running = False
        if lock_aquired:
            self._running_lock.release()
        self._clean_server_services()
        print("Server closed")


        self._server_stopped()

    def _clean_server_services(self):
        self._server_running = False
        # close pipes
        if self._stdin:
            self._stdin.close()
        if self._stdout:
            self._stdout.close()

        self._stdout_thread.join()
        self._stdin = None
        self._stdout = None

        # wait for restart scheduler
        if self._restart_scheduler:
            self._restart_scheduler.join()
            self._restart_scheduler = None


    def run(self):
        if self.running:
            return

        self.running = True

        # update server
        ready_to_start = self._update_server()
        if not ready_to_start:
            print("Failed to acquire server.jar")
            self.running = False
            return
        
        # load built-in extensions
        self._load_builtin_extensions()

        self._stdin_thread = threading.Thread(target=self._read_stdin, daemon=True, name="stdin_thread")
        self._stdin_thread.start()

        self._accept_eula() # TODO: actually ask user to accept eula
        while self.running:
            self._run_server()


        # save config
        self.config.save_config()
        print("Shutting down...")


class ListenerTester(Listener):
    def handle_message(self, message: Message) -> None:
        if "ping" in message.content:
            self.wrapper.send_command("say pong")

        if message.is_user_message():
            self.wrapper.send_command(f"say Hello, {message.author}!")

def main():
    parser = argparse.ArgumentParser(description="Wrapper for Minecraft server")
    parser.add_argument("--directory", "-d", help="Server directory", default="default")
    args = parser.parse_args()

    wrapper = Wrapper(args.directory)
    wrapper.run()

if __name__ == "__main__":
    main()
