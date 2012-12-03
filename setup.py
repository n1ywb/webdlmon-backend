#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name = "webdlmon-backend",
    version = "0.1",
    packages = find_packages(),
    scripts = ['pywebdlmond'],


    install_requires = [
                        'kudu', # High level Antelope API
                       ],

    # metadata for upload to PyPI
    author = "UCSD",
    author_email = "jeff@jefflaughlinconsulting.com",
    description = "Python Web DLMON Daemon",
    license = "MIT",
    keywords = "antelope brtt dlmon webdlmon",
    url = "https://github.com/n1ywb/webdlmon-backend",

)

