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

    packages=["simpleblogger", "simpleblogger.dialogs", "simpleblogger.providers"],

    package_data={
        "simpleblogger": [
            "application/simpleblogger.png",
            "application/simpleblogger.desktop",
            "application/simpleblogger",
            ],
    }
)
