from os.path import normpath, dirname, abspath, join

def translate_path(root, path):
    if (not path) or path=='/':
        return root
    if not path.startswith('/'):
        path='/%s' % path
    return normpath('%s%s' % (root, normpath(path)))


def untranslate_path(root, path):
    path=normpath(path)
    if not path.startswith(root):
        raise ValueError("path (%s) not under root (%s)" % (path, root))
    p=path[len(root):]
    if not p.startswith('/'):
        p='/%s' % p
    return p


def relpath(selfpath, path):
    return join(dirname(selfpath), path)
