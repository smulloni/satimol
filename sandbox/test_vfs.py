import skunk.vfs

def test_root1():
    class docroot(object):
        def __init__(self, r):
            self.root=r
    root=docroot('/tmp')
    fs=skunk.vfs.LocalFS(root=root)
    assert fs.root=='/tmp'
    root.root='/var'
    assert fs.root=='/var'
    root.root='/home'
    assert fs.root=='/home'
