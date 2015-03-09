#!/usr/bin/env python2

from distutils.core import setup

setup(
    name="simpleblogger",
    version="2.0",
    description="blogger.com client written in Python and GTK+ 3",

    license='MIT',

    author="Yauhen Shulitski",
    author_email="jsnjack@gmail.com",

    url="https://github.com/e-shulitsky/simpleblogger",

    packages=["", "dialogs", "providers", "config", "application"],

    scripts=["simpleblogger.py"],
    package_data={
        "config": ["image_insertion_template.html"],
        "application": ["simpleblogger.png", "simpleblogger.desktop"]
    }
)
