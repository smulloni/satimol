import logging

from skunk.config import Configuration

Configuration.setDefaults(userLogger='USER')

def getUserLogger():
    """returns the logger used for user logging in STML"""
    return logging.getLogger(Configuration.userLogger)

def debug(msg, *args, **kwargs):
    getUserLogger().debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    getUserLogger().info(msg, *args, **kwargs)

def warn(msg, *args, **kwargs):
    getUserLogger().warn(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    getUserLogger().error(msg, *args, **kwargs)

def exception(msg, *args, **kwargs):
    getUserLogger().exception(msg, *args, **kwargs)    

__all__=['debug', 'info', 'warn', 'error', 'exception']
