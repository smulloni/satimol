#! /usr/bin/env python

"""
This is a script for looking at the compiled Python form of STML templates.

  python -m skunk/stml/cc mycomponent.comp | less

will work nicely for you; or

  python -m skunk/stml/cc -o outfile.py mycomponent.comp

"""
import logging
import optparse
import os
import sys

logging.basicConfig(level=logging.CRITICAL)

from skunk.stml.comp import STMLFileComponent


def cc(file, fp):
    file=os.path.abspath(file)
    f=STMLFileComponent(file)
    fp.write(f.getCode())

def main(args=None):
    if args is None:
        args=sys.argv[1:]
    p=optparse.OptionParser(usage="usage: %prog [-o outfile] infile")
    p.add_option('-o', '--output',
                 dest='outfile',
                 help="file to which output will be written")
    opts, args=p.parse_args(args)
    if len(args)!=1:
        p.error('expected one argument')
    if opts.outfile:
        fp=open(opts.outfile, 'w')
    else:
        fp=sys.stdout
    cc(args[0], fp)
    if opts.outfile:
        fp.flush()
        fp.close()
    sys.exit(0)
        

if __name__=='__main__':
    main(sys.argv[1:])
