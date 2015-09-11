"""
Config looks like:
{
    "blogs": [
        {
            "id": 12345,
            "name": "My blog",
            "email": "jsnjack@gmail.com",
            "link": "myblog.blogspot.com",
            "tags": [
                "banana",
                "zorro"
            ]
        }
    ],
    "active_blog": 12345
}
"""

import os
import pickle

from simpleblogger import CONFIG_DIRECTORY

CONFIG_PATH = os.path.join(CONFIG_DIRECTORY, "config.sb")
IMAGE_WRAP_TEMPLATE_PATH = os.path.join(CONFIG_DIRECTORY, "image_insertion_template.html")


def config_check():
    """
    Creates necessary config files if they are empty
    """
    # Check that config directory exist and create it if it doesn't
    if not os.path.exists(CONFIG_DIRECTORY):
        os.makedirs(CONFIG_DIRECTORY)
    if not os.path.exists(IMAGE_WRAP_TEMPLATE_PATH):
        with open(os.path.abspath(IMAGE_WRAP_TEMPLATE_PATH), 'wb') as template_file:
            template_file.write(
                """<div class="separator" style="clear: both; text-align: center;">
    <a href="{image_url}" imageanchor="1" style="margin-left:1em; margin-right:1em">
        <img border="0" src="{thumbnail_url}"/>
    </a>
</div>
"""
            )


def load_config():
    """
    Reads config from file
    """
    config_check()
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
