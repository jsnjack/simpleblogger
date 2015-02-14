import os
import pickle


CONFIG_PATH = "./config/config.sb"


def load_config():
    """
    Reads config from file
    """
    try:
        with open(os.path.abspath(CONFIG_PATH), 'rb') as config_file:
            config = pickle.load(config_file)
    except IOError:
        # Create new empty config file
        with open(os.path.abspath(CONFIG_PATH), 'wb') as config_file:
            config = {"blogs": []}
            pickle.dump(config, config_file)
    return config


def save_config(config):
    """
    Save config to file
    """
    with open(os.path.abspath(CONFIG_PATH), 'wb') as config_file:
        pickle.dump(config, config_file)
    return config
