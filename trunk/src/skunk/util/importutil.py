def import_from_string(s):
    """
    import and return something specified in "package.module:thing.attribute" notation.
    
    >>> import_from_string('skunk.util') # doctest: +ELLIPSIS
    <module 'skunk.util' ...
    >>> import_from_string('skunk.util.importutil') # doctest: +ELLIPSIS
    <module 'skunk.util.importutil' ...
    >>> import_from_string('skunk.util.importutil:import_from_string') # doctest: +ELLIPSIS
    <function import_from_string ...
    """
    if ':' in s:
        modname, rest=s.split(':')
        names=rest.split('.')
        firstname=names[0]
        thing=__import__(modname, globals(), locals(), [firstname])
        for n in names:
            thing= getattr(thing, n)
        return thing
    else:
        thing=__import__(s)
        names=s.split('.')
        for name in names[1:]:
            thing=getattr(thing, name)
        return thing
            

