from tornado.options import define, options
def parse_config_file(path):
    config = {}
    execfile(path, config, config)
    for name in config:
        if name in options:
            setattr(options, name, config[name])
        else:
            define(name, config[name])