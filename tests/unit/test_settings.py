from pynetbox_config_helper import (
    resolve_config,
    build_argparser,
    ConfigError,
    get_instance_name,
    load_from_config_file,
    overload_with_env,
    overload_with_cmdline,
    resolve_graphql_config,
)
from configparser import ConfigParser
from os import environ
from pytest import fixture
import pytest
from configparser import NoSectionError, NoOptionError


@fixture
def config_file(tmp_path):
    config = """[Main]
Instance=prod

[prod]
URL=https://prod.example.com/api
Token=1234567890abcdef

[test]
URL=https://test.example.com/api
Token=qwertyqwertz12345
"""
    config_file_path = tmp_path / "test_config.ini"
    config_file_path.write_text(config)

    yield config_file_path

    pass


@fixture
def no_instance_config_file(tmp_path):
    config = """[Main]
dummy=yes
"""
    config_file_path = tmp_path / "test_no_instance_config.ini"
    config_file_path.write_text(config)

    yield config_file_path

    pass


@fixture
def parser():
    return build_argparser()


@fixture
def clear_env():
    """
    Removes all keys that are used from the environment to not interfere with
    the tests.
    """
    for key in (
        "NETBOX_URL",
        "NETBOX_TOKEN",
        "NETBOX_CONFIG",
        "NETBOX_INSTANCE",
        "NETBOX_GRAPHQL_URL",
    ):
        try:
            del environ[key]
        except KeyError:
            pass


def test_commandline_args_only(parser):
    args = parser.parse_args([
        "--url",
        "https://test.example.com/api",
        "--token",
        "1234567890abcdef",
    ])
    config = resolve_config(args)
    assert config == {
        "url": "https://test.example.com/api",
        "token": "1234567890abcdef",
    }


def test_environment_args_only():
    parser = build_argparser()
    args = parser.parse_args([])
    environ["NETBOX_URL"] = "https://test.example.com/api"
    environ["NETBOX_TOKEN"] = "1234567890abcdef"
    config = resolve_config(args)
    assert config == {
        "url": "https://test.example.com/api",
        "token": "1234567890abcdef",
    }


def test_commandline_environment_args_1():
    parser = build_argparser()
    args = parser.parse_args(["--url", "https://test.example.com/api"])
    environ["NETBOX_TOKEN"] = "1234567890abcdef"
    config = resolve_config(args)
    assert config == {
        "url": "https://test.example.com/api",
        "token": "1234567890abcdef",
    }


def test_commandline_environment_args_2():
    parser = build_argparser()
    args = parser.parse_args(["--token", "1234567890abcdef"])
    environ["NETBOX_URL"] = "https://test.example.com/api"
    config = resolve_config(args)
    assert config == {
        "url": "https://test.example.com/api",
        "token": "1234567890abcdef",
    }


def test_config_file_default(clear_env, config_file, parser):
    args = parser.parse_args(["--config", str(config_file)])
    config = resolve_config(args)

    assert config == {
        "url": "https://prod.example.com/api",
        "token": "1234567890abcdef",
    }


def test_config_file_from_env(clear_env, config_file, parser):
    args = parser.parse_args([])
    environ["NETBOX_CONFIG"] = str(config_file)
    config = resolve_config(args)

    assert config == {
        "url": "https://prod.example.com/api",
        "token": "1234567890abcdef",
    }


def test_config_file_instance_from_cli(clear_env, config_file, parser):
    args = parser.parse_args(["--config", str(config_file), "--instance", "test"])
    config = resolve_config(args)

    assert config == {
        "url": "https://test.example.com/api",
        "token": "qwertyqwertz12345",
    }


def test_config_file_instance_from_env(clear_env, config_file, parser):
    args = parser.parse_args(["--config", str(config_file)])
    environ["NETBOX_INSTANCE"] = "test"
    config = resolve_config(args)

    assert config == {
        "url": "https://test.example.com/api",
        "token": "qwertyqwertz12345",
    }


def test_config_file_overwrite_token_from_cli(clear_env, config_file, parser):
    args = parser.parse_args(["--config", str(config_file), "--token", "test"])
    config = resolve_config(args)

    assert config == {"url": "https://prod.example.com/api", "token": "test"}


def test_config_file_overwrite_token_from_env(clear_env, config_file, parser):
    args = parser.parse_args(["--config", str(config_file)])
    environ["NETBOX_TOKEN"] = "test"
    config = resolve_config(args)

    assert config == {"url": "https://prod.example.com/api", "token": "test"}


def test_config_file_overwrite_token(clear_env, config_file, parser):
    args = parser.parse_args(["--config", str(config_file)])
    environ["NETBOX_TOKEN"] = "test"
    config = resolve_config(args)

    assert config == {"url": "https://prod.example.com/api", "token": "test"}


def test_config_file_overwrite_url(clear_env, config_file, parser):
    args = parser.parse_args(["--config", str(config_file)])
    environ["NETBOX_URL"] = "https://overwrite.example.com/api"
    config = resolve_config(args)

    assert config == {
        "url": "https://overwrite.example.com/api",
        "token": "1234567890abcdef",
    }


def test_config_file_instance_not_found(clear_env, config_file, parser):
    args = parser.parse_args([
        "--config",
        str(config_file),
        "--instance",
        "doesnotexist",
    ])
    with pytest.raises(NoSectionError):
        resolve_config(args)


def test_config_file_no_instance_given(clear_env, no_instance_config_file, parser):
    args = parser.parse_args(["--config", str(no_instance_config_file)])
    with pytest.raises(NoOptionError):
        resolve_config(args)


def test_get_instance_name_cmdline_instance(clear_env, parser, config_file):
    args = parser.parse_args(["--instance", "cmdline_instance"])
    config = ConfigParser()
    config.read_file(config_file.open())
    environ["NETBOX_INSTANCE"] = "env_instance"
    assert get_instance_name(args, config) == "cmdline_instance"


def test_get_instance_name_env_instance(clear_env, parser, config_file):
    args = parser.parse_args([])
    environ["NETBOX_INSTANCE"] = "env_instance"
    config = ConfigParser()
    config.read_file(config_file.open())
    assert get_instance_name(args, config) == "env_instance"


def test_get_instance_name_config_instance(clear_env, parser, config_file):
    args = parser.parse_args([])
    config = ConfigParser()
    config.read_file(config_file.open())
    assert get_instance_name(args, config) == "prod"


def test_load_from_config_file(clear_env, parser, config_file):
    args = parser.parse_args(["--config", str(config_file)])
    assert load_from_config_file(args) == {
        "url": "https://prod.example.com/api",
        "token": "1234567890abcdef",
        "graphql_url": None,
    }


def test_load_from_config_file_no_instance_config(
    clear_env, parser, no_instance_config_file
):
    args = parser.parse_args(["--config", str(no_instance_config_file)])
    assert load_from_config_file(args) == dict()

    args = parser.parse_args([])
    environ["NETBOX_CONFIG"] = str(no_instance_config_file)
    assert load_from_config_file(args) == dict()


def test_overload_with_env(clear_env):
    settings = {
        "url": "https://settings.example/api",
        "token": "1234settings",
        "graphql_url": "https://settings.example/graphql",
    }

    # first test omits setting the token
    settings_copy = settings.copy()

    environ["NETBOX_URL"] = "https://env.example/api"
    environ["NETBOX_GRAPHQL_URL"] = "https://env.example/graphql"

    overload_with_env(settings_copy)

    assert settings_copy == {
        "url": "https://env.example/api",
        "token": "1234settings",
        "graphql_url": "https://env.example/graphql",
    }

    # second test witht he token
    settings_copy = settings.copy()
    environ["NETBOX_TOKEN"] = "1234env"

    overload_with_env(settings_copy)

    assert settings_copy == {
        "url": "https://env.example/api",
        "token": "1234env",
        "graphql_url": "https://env.example/graphql",
    }


def test_overload_with_cmdline(clear_env, parser):
    settings = {
        "url": "https://env.example/api",
        "token": "1234env",
        "graphql_url": "https://env.example/graphql",
    }

    # no overload
    args = parser.parse_args([])

    assert overload_with_cmdline(args, settings.copy()) == {
        "url": "https://env.example/api",
        "token": "1234env",
        "graphql_url": "https://env.example/graphql",
    }

    # add URL overload
    args = parser.parse_args(["--url", "https://cmdline.example/api"])

    assert overload_with_cmdline(args, settings.copy()) == {
        "url": "https://cmdline.example/api",
        "token": "1234env",
        "graphql_url": "https://env.example/graphql",
    }

    # add token overload
    args = parser.parse_args([
        "--url",
        "https://cmdline.example/api",
        "--token",
        "1234cmdline",
    ])

    assert overload_with_cmdline(args, settings.copy()) == {
        "url": "https://cmdline.example/api",
        "token": "1234cmdline",
        "graphql_url": "https://env.example/graphql",
    }

    # add graphql overload
    args = parser.parse_args([
        "--url",
        "https://cmdline.example/api",
        "--token",
        "1234cmdline",
        "--graphql-url",
        "https://cmdline.example/graphql",
    ])

    assert overload_with_cmdline(args, settings.copy()) == {
        "url": "https://cmdline.example/api",
        "token": "1234cmdline",
        "graphql_url": "https://cmdline.example/graphql",
    }


def test_resolve_graphql_config(clear_env, no_instance_config_file, parser):
    args = parser.parse_args([
        "--graphql-url",
        "https://cmdline.example/graphql",
        "--token",
        "1234cmdline",
    ])
    endpoint, headers = resolve_graphql_config(args)

    assert endpoint == "https://cmdline.example/graphql"
    assert headers == {"Authorization": "Token 1234cmdline"}


def test_resolve_graphql_config_no_endpoint(clear_env, no_instance_config_file, parser):
    args = parser.parse_args([
        "--token",
        "1234cmdline",
        "--config",
        str(no_instance_config_file),
    ])

    with pytest.raises(ConfigError):
        resolve_graphql_config(args)


def test_resolve_graphql_config_no_token(clear_env, no_instance_config_file, parser):
    args = parser.parse_args([
        "--graphql-url",
        "https://cmdline.example/graphql",
        "--config",
        str(no_instance_config_file),
    ])

    with pytest.raises(ConfigError):
        resolve_graphql_config(args)
