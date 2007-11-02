"""
manages logging configuration.

To configure logging, you set Configuration.logConfig to a data structure like the following:

{'' : [{'handler' : None,
        'filter' : None,
        'filename' : None,
        'stream' : None,
        'level' : logging.WARN,
        'format' : '%(name)s %(asctime)s %(levelname)s %(message)s'
        'datefmt' : None}]}

the same logger can have multiple handlers.  Each handler has a level
(can be inherited), a formatter.

"""
import logging

from skunk.config import Configuration

Configuration.setDefaults(logConfig={'' : dict(
    level=logging.WARN,
    format='%(name)s %(asctime)s %(levelname)s %(message)s',
    datefmt=None)})


def _setup_logging(logconfig):
    if all(isinstance(d, (list, tuple, dict)) for d in logconfig.itervalues()):
        for logname, configs in logconfig.iteritems():
            logger=logging.getLogger(logname)
            if isinstance(configs, dict):
                configs=[configs]
            for config in configs:
                handler=_get_handler(config, logname)
                logger.addHandler(handler)
    else:
        logging.basicConfig(**logconfig)

def _get_handler(config, logname):
    handler=config.get('handler')
    if not handler:
        stream=config.get('stream')
        if stream:
            handler=logging.StreamHandler(stream)
        else:
            filename=config.get('filename')
            if filename:
                handler=logging.FileHandler(filename)
    if not handler:
        handler=logging.StreamHandler()
    level=config.get('level')
    if level:
        handler.setLevel(level)
    format=config.get('format')
    datefmt=config.get('datefmt')
    if format or datefmt:
        formatter=logging.Formatter(format, datefmt)
        handler.setFormatter(formatter)
    filter=config.get('filter')
    if filter:
        handler.addFilter(filter)
    return handler

def init_service():
    _setup_logging(Configuration.logConfig)
    

            
    

