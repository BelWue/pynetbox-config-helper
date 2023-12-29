# pynetbox-argparse

A command argument, Environment variable and config file parser wrapper for
[pynetbox](https://github.com/netbox-community/pynetbox).

pynetbox-argparse allows you to easily read the config parameters needed for
pynetbox (a URL and a token) from command arguments, environment variables
and a config file, so that you dont have to repeat that code for every script
you write and get a uniform interface for all your scripts.

## Usage

Your code could look like this

```python

from pynetbox_argparse import build_argparser, resolve_config
import pynetbox

parser = build_argparser()  # this returns an ArgumentParser which you can extend further
settings = resolve_config(parser.parse_args())  # you get your config settings

nb = pynetbox.API(**settings)  # you get your pynetbox API instance
... you do your things
```

Now you place a config file in your config directory
(`~/.config/pynetbox/config.ini` on Linux, other paths on other systems).
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
