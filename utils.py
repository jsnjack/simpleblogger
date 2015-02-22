import os
import pickle


CONFIG_PATH = "./config/config.sb"
IMAGE_WRAP_TEMPLATE_PATH = "./config/image_insertion_template.html"


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
            config = {
                "blogs": [],
                "active_blog": None
            }
            pickle.dump(config, config_file)
    return config


def save_config(config):
    """
    Save config to file
    """
    with open(os.path.abspath(CONFIG_PATH), 'wb') as config_file:
        pickle.dump(config, config_file)
    return config


def get_blog_by_id(config, blog_id):
    """
    Find blog by id and return it
    """
    for item in config["blogs"]:
        if item["id"] == blog_id:
            return item


def wrap_image_url(url):
    """
    Wraps image url in html tags
    """
    with open(IMAGE_WRAP_TEMPLATE_PATH, 'rb') as wrap_template:
        content = wrap_template.read()
        filename = url.split("/")[-1]
        filename_with_size = "{image_size}/" + filename
        new_url = url.replace(filename, filename_with_size)
        return content.format(
            image_url=new_url.format(image_size="s0"),
            thumbnail_url=new_url.format(image_size="s450")
            )


def generate_filename(string):
    """
    Generate save filename from string
    """
    keepcharacters = (' ', '.', '_')
    return "".join(c for c in string if c.isalnum() or c in keepcharacters).rstrip()
