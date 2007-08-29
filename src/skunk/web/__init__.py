SKUNK_VERSION="4.0a0"


from skunk.config import Configuration

Configuration.setDefaults(
    serverIdentification='Skunkweb %s' % SKUNK_VERSION,
    defaultCharset='utf-8',
    defaultContentType='text/html'
    )

del Configuration


