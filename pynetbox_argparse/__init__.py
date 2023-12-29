import argparse
from os import environ
from typing import Dict
from configparser import ConfigParser
from pathlib import Path

from platformdirs import user_config_dir

__version__ = "0.1.0"

__all__ = ("expand_argparser", "build_argparser", "resolve_config", "ConfigError")


class ConfigError(Exception):
    pass


def expand_argparser(parser: argparse.ArgumentParser):
    """
    Adds the "--instance", "--config", "--url" and "--token" options to `parser`.
    """

    parser.add_argument("--instance", help="the name of the instance to use")
    parser.add_argument("--config", help="the config file to use")
    parser.add_argument("--url", help="the URL of the NetBox instance")
    parser.add_argument("--token", help="the token for the NetBox REST API")


def build_argparser() -> argparse.ArgumentParser:
    """
    Returns a ArgumentParser.
    """

    parser = argparse.ArgumentParser()
    expand_argparser(parser)
    return parser


def resolve_config(args: argparse.Namespace) -> Dict[str, str]:
    # get the config file
    config_file = args.config
    if not config_file:
        config_file = environ.get(
            "NETBOX_CONFIG", Path(user_config_dir(__name__)) / "config.ini"
        )

    # populate the settings for pynetbox
    settings = dict()
    # settings from command line arguments
    settings["url"] = args.url
    settings["token"] = args.token

    if settings["url"] and settings["token"]:
        return settings

    # settings from the environment variables
    if not settings["url"]:
        settings["url"] = environ.get("NETBOX_URL")
    if not settings["token"]:
        settings["token"] = environ.get("NETBOX_TOKEN")

    if settings["url"] and settings["token"]:
        return settings

    # parse the config file
    config = ConfigParser()

    config.read(config_file)

    # determine instance arg > env > config
    instance = None
    for option in [
        args.instance,
        environ.get("NETBOX_INSTANCE"),
        config.get("Main", "Instance"),
    ]:
        if option:
            instance = option
            break

    if not settings["url"]:
        settings["url"] = config.get(instance, "URL")
    if not settings["token"]:
        settings["token"] = config[instance].get("token")

    assert settings["url"], f"Could not determine URL for instance '{instance}'"
    assert settings["token"], f"Could not determine token for instance '{instance}'"

    return settings
