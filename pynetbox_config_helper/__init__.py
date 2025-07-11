import argparse
from os import environ
from typing import Dict, Tuple
from configparser import ConfigParser
from pathlib import Path

from platformdirs import user_config_dir

__version__ = "0.2.0"

__all__ = (
    "expand_argparser",
    "build_argparser",
    "resolve_config",
    "ConfigError",
    "resolve_graphql_config",
)


class ConfigError(Exception):
    pass


def expand_argparser(parser: argparse.ArgumentParser):
    """
    Adds the "--instance", "--config", "--url", "--graphql-url" and "--token" options to `parser`.
    """

    parser.add_argument("--instance", help="the name of the instance to use")
    parser.add_argument("--config", help="the config file to use")
    parser.add_argument("--url", help="the URL of the NetBox API endpoint")
    parser.add_argument("--token", help="the token for the NetBox REST API")
    parser.add_argument("--graphql-url", help="The URL for the GraphQL endpoint")


def build_argparser() -> argparse.ArgumentParser:
    """
    Returns a ArgumentParser including all settings from *expand_argparser()*.
    """

    parser = argparse.ArgumentParser()
    expand_argparser(parser)
    return parser


def get_instance_name(args: argparse.Namespace, config: ConfigParser) -> str | None:
    """
    Returns the instance name that should be used, depending on arguments, environment variables and the config file.

    Returns *None* if the instance name could not be resolved.
    """
    if args.instance is not None:
        return args.instance

    env_instance = environ.get("NETBOX_INSTANCE")
    if env_instance:
        return env_instance

    config_instance = config.get("Main", "Instance", fallback=None)
    return config_instance


def load_from_config_file(args: argparse.Namespace) -> Dict[str, str]:
    """
    Loads settings from the config file.

    The config file itself is resolved from command line and environment variables.
    If no instance is specified, the default instance is selected.

    If the config could not be found or the instance does not exist an empty dictionary is returned.
    """
    config_file = args.config
    if not config_file:
        config_file = environ.get(
            "NETBOX_CONFIG", Path(user_config_dir(__name__)) / "config.ini"
        )

    config = ConfigParser()

    config.read(config_file)

    settings = dict()

    instance = get_instance_name(args, config)
    # Load from config if possible
    if instance is not None and config.has_section(instance):
        settings["url"] = config.get(instance, "URL", fallback=None)
        settings["token"] = config.get(instance, "Token", fallback=None)
        settings["graphql_url"] = config.get(instance, "GraphQL-URL", fallback=None)

    return settings


def overload_with_env(settings: Dict[str, str]):
    """
    Replaces the values in *settings* with those from environment variables, if they are present.
    """
    for key, varname in [
        ("url", "NETBOX_URL"),
        ("token", "NETBOX_TOKEN"),
        ("graphql_url", "NETBOX_GRAPHQL_URL"),
    ]:
        varvalue = environ.get(varname)
        if varvalue is not None:
            settings[key] = varvalue


def overload_with_cmdline(args, settings: Dict[str, str]):
    """
    Replaces the values in *settings* with those from args, if they are present.
    """
    for key, varvalue in [
        ("url", args.url),
        ("token", args.token),
        ("graphql_url", args.graphql_url),
    ]:
        if varvalue is not None:
            settings[key] = varvalue

    return settings


def resolve_settings(args: argparse.Namespace) -> Dict[str, str]:
    """
    Resolves the settings for the chosen instance based on commandline arguments,
    environment variables and the config file.

    Returns a dictionary containing the resolved settings.
    """

    settings = load_from_config_file(args)
    overload_with_env(settings)
    overload_with_cmdline(args, settings)

    return settings


def resolve_graphql_config(args: argparse.Namespace) -> Tuple[str, Dict[str, str]]:
    """
    Returns the URL of the graphql endpoint and a headers dictionary containing authentication header.

    Raises an exception if the required settings could not be found.
    """

    settings = resolve_settings(args)
    endpoint = settings.get("graphql_url")
    if endpoint is None:
        raise ConfigError("GraphQL endpoint could not be found in the configuration")

    token = settings.get("token")
    if token is None:
        raise ConfigError("API token could not be found in the configuration")

    return endpoint, {"Authorization": f"Token {token}"}


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
