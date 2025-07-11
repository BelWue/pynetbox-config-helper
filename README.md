# pynetbox-config-helper

A command argument, Environment variable and config file parser wrapper for
[pynetbox](https://github.com/netbox-community/pynetbox) and GraphQL endpoints.

pynetbox-config-helper allows you to easily read the config parameters needed for
pynetbox (a URL and a token) from command arguments, environment variables
and a config file, so that you dont have to repeat that code for every script
you write and get a uniform interface for all your scripts.

## Usage

Your code could look like this

```python

from pynetbox_config_helper import build_argparser, resolve_config
import pynetbox

parser = build_argparser()  # this returns an ArgumentParser which you can extend further
settings = resolve_config(parser.parse_args())  # you get your config settings

nb = pynetbox.api(**settings)  # you get your pynetbox API instance
# ... you do your things
```

Alternativly you can use this library to return the settings for a GraphQL API:


```python

from pynetbox_config_helper import build_argparser, resolve_graphql_config
import pynetbox

parser = build_argparser()  # this returns an ArgumentParser which you can extend further
endpoint, headers = resolve_graphql_config(parser.parse_args())  # you get your endpoint and headers

# ... you do your things
```


Now you place a config file in your config directory
(`~/.config/pynetbox_config_helper/config.ini` on Linux,
other paths on other systems, see
[Section Location of the config file](#location-of-the-config-file).
That config may contain multiple NetBox instances:

```ini
[Main]
Instance=prod

[prod]
URL=https://prod.example.com/api
Token=1234567890abcdef

[test]
URL=https://test.example.com/api
Token=testtoken123456
```

The instances in this example are called `prod` and `test`.
The `[Main]` section specifies the default instance.
In this case `prod`.

When you call your script it will automatically search for your config file,
find your default instance and take the URL and Token from that instance.
Alternativly you can also overwrite the `Instance` setting via the `--instance`
command argument or the `NETBOX_INSTANCE` environment variable.

```
./script.py --instance "test"
NETBOX_INSTANCE="test" ./script.py
```

You can overwrite the Token and URL with the `--token` and `--url` arguments
or `NETBOX_TOKEN` and `NETBOX_URL` environment variables.

Finally you can also specify a different config file with `--config` or
`NETBOX_CONFIG`.

Generally commandline arguments are preferred over environment variables which
are preferred over configuration settings.
You can even specify the URL and Token via commandline arguments or environment
variables and don't even need a config file.

## Location of the config file

The default config file location is OS dependant.
Internally we use [platformdirs](https://pypi.org/project/platformdirs/)
to find the `user_config_dir`.

On different systems this resolves to:

### Linux
```
~/.config/pynetbox_config_helper/config.ini
```

### MacOS
```
/Users/youruser/Library/pynetbox_config_helper/config.ini
```

### Windows
```
C:\Users\youruser\AppData\Local\pynetbox_config_helper\config.ini
```

# Development

## Setup

This project uses [poetry](https://python-poetry.org/) for development.
Clone this repository and run `poetry install --with=dev` to create a virtual environment and install the dependencies, including development dependencies

## Testing

To  run the tests, execute `poetry run pytest`.

To generate code coverage reports, run `poetry run coverage run` to generate coverage reports and `poetry run coverage html`to render them to HTML.
The resulting report is stored in `htmlcov/index.html`
