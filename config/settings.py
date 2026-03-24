#!/usr/bin/env python3
"""
Config module for loading settings
"""

import configparser


def load_config(config_path='config/settings.ini'):
    """Load configuration file"""
    config = configparser.ConfigParser()
    config.read(config_path)
    return config
