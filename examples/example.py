from pynetbox_config_helper import build_argparser, resolve_config

parser = build_argparser()

parser.add_argument("--my-args", help="foo")
args = parser.parse_args()

print(args)

settings = resolve_config(args)

print(settings)
