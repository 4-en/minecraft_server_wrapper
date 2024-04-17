import os

# get data root directory
def get_data_root():
    if os.name == "nt":
        return os.path.join(os.getenv("APPDATA"), "mcs_wrapper")
    else:
        return os.path.join(os.getenv("HOME"), ".mcs_wrapper")


class KVConfig:

    def set_path(self, path):
        self._path = path

    def get_path(self):
        return self._path

    def _get_value_type(self, key, value):
        # check if key is already defined in this class
        if hasattr(self, key):
            t = type(getattr(self, key))
            # if t is None, then we check manually
            if t is not None:
                return t
        
        # check if value is a boolean
        if value.lower() in ["true", "false"]:
            return bool
        
        # check if value is an integer
        try:
            int(value)
            return int
        except ValueError:
            pass

        # check if value is a float
        try:
            float(value)
            return float
        except ValueError:
            pass

        # default to string
        return str

    def _parse_line(self, line):
        # raise Exception if line starts with # or has no = sign
        # comment should be sorted out before this function is called
        if line.startswith("#") or "=" not in line:
            raise Exception("Invalid line: " + line)
        
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        value_type = self._get_value_type(key, value)

        # try to convert value to value_type
        try:
            value = value_type(value)
        except ValueError:
            raise Exception(f"Failed to convert {value} to {value_type}")
        
        return key, value
    
    def _parse_file(self, path):
        # read file and parse lines
        with open(self._path, "r") as f:
            lines = f.readlines()
        
        # remove comments and empty lines
        lines = [line for line in lines if not line.startswith("#") and line.strip() != ""]
        
        # parse lines
        config = {}
        for line in lines:
            key, value = self._parse_line(line)
            config[key] = value

        return config
    
    def save_config(self, config=None, path=None):
        if config is None:
            config = self.__dict__

        if path is None:
            path = self._path

        with open(path, "w") as f:
            for key, value in config.items():
                # skip keys that start with underscore
                if key.startswith("_"):
                    continue
                
                print(f"key={key}, value={value}")
                # if value is callable, call it
                if callable(value):
                    value = value()

                # if value starts with #, treat it as a comment
                if str(value).startswith("#"):
                    f.write(f"{value}\n")
                    continue

                f.write(f"{key} = {value}\n")

    def load_config(self, path=None):

        if path is None:
            path = self._path

        # check if file exists
        if not os.path.exists(path):
            print(f"Config file {self.path} does not exist. Using default values.")
            return

        config = self._parse_file(path)
        for key, value in config.items():
            if hasattr(self, key):
                setattr(self, key, value)