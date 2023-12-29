from pynetbox_argparse import resolve_config, build_argparser, ConfigError
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
    for key in ("NETBOX_URL", "NETBOX_TOKEN", "NETBOX_CONFIG", "NETBOX_INSTANCE"):
        try:
            del environ[key]
        except KeyError:
            pass


def test_commandline_args_only(parser):
    args = parser.parse_args(
        ["--url", "https://test.example.com/api", "--token", "1234567890abcdef"]
    )
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
    args = parser.parse_args()
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
        "token": "qwertyqwertz12345"
    }

def test_config_file_instance_from_env(clear_env, config_file, parser):
    args = parser.parse_args(["--config", str(config_file)])
    environ["NETBOX_INSTANCE"] = "test"
    config = resolve_config(args)

    assert config == {
        "url": "https://test.example.com/api",
        "token": "qwertyqwertz12345"
    }

def test_config_file_overwrite_token_from_cli(clear_env, config_file, parser):
    args = parser.parse_args(["--config", str(config_file), "--token", "test"])
    config = resolve_config(args)

    assert config == {
        "url": "https://prod.example.com/api",
        "token": "test"
    }

def test_config_file_overwrite_token_from_env(clear_env, config_file, parser):
    args = parser.parse_args(["--config", str(config_file)])
    environ["NETBOX_TOKEN"] = "test"
    config = resolve_config(args)

    assert config == {
        "url": "https://prod.example.com/api",
        "token": "test"
    }

def test_config_file_overwrite_token(clear_env, config_file, parser):
    args = parser.parse_args(["--config", str(config_file)])
    environ["NETBOX_TOKEN"] = "test"
    config = resolve_config(args)

    assert config == {
        "url": "https://prod.example.com/api",
        "token": "test"
    }

def test_config_file_overwrite_url(clear_env, config_file, parser):
    args = parser.parse_args(["--config", str(config_file)])
    environ["NETBOX_URL"] = "https://overwrite.example.com/api"
    config = resolve_config(args)

    assert config == {
        "url": "https://overwrite.example.com/api",
        "token": "1234567890abcdef"
    }

def test_config_file_instance_not_found(clear_env, config_file, parser):
    args = parser.parse_args(["--config", str(config_file), "--instance", "doesnotexist"])
    with pytest.raises(NoSectionError):
        resolve_config(args)

def test_config_file_no_instance_given(clear_env, no_instance_config_file, parser):
    args = parser.parse_args(["--config", str(no_instance_config_file)])
    with pytest.raises(NoOptionError):
        resolve_config(args)
