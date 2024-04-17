
class KVConfig:
    def __init__(self, path):
        self._path = path

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
    
    def _parse_file(self):
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
    
    def save_config(self, config):
        with open(self._path, "w") as f:
            for key, value in config.items():
                # skip keys that start with underscore
                if key.startswith("_"):
                    continue

                # if value is callable, call it
                if callable(value):
                    value = value()

                # if value starts with #, treat it as a comment
                if str(value).startswith("#"):
                    f.write(f"{value}\n")
                    continue

                f.write(f"{key} = {value}\n")

    def load_config(self):
        config = self._parse_file()
        for key, value in config.items():
            setattr(self, key, value)