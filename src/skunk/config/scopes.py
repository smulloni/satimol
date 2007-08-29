"""
The implementation of the scopeable config object.
"""

import fnmatch
import os
import re
from threading import local

class ScopeManager(object):

    def __init__(self):
        # the attributes accessed by the __getattr__ hook
        self._data = local()
        # the defaults
        self._defaults = {}
        # user configuration 
        self._userconfig = {}
        # the context
        self._context = local().__dict__
        # functions that manipulate the environment according to the scope
        self._matchers = []
        # overrides added by scoping
        self._overlay = local().__dict__

    def setDefaults(self, **kw):
        """
        set default values
        """
        self._defaults.update(kw)
        self._mash()

    def _mash(self):
        """
        merge the different layers of configuration data
        (defaults, userconfig, overlay) into self._data
        """
        adict = self._defaults.copy()
        adict.update(self._userconfig)
        adict.update(self._overlay)
        self._data.__dict__.clear()
        self._data.__dict__.update(adict)

    def trim(self):
        """
        reset the context dictionary to empty
        """
        self._overlay.clear()
        self._context.clear()
        self._mash()

    def scope(self, context):
        """
        set the user configuration according to a context dictionary.
        """
        self._context.update(context)
        self._overlay.clear()
        for m in self._matchers:
            self._process_matcher(m)
        self._mash()

    def load(self, *files, **kw):
        """
        load user configuration from files
        """
        if len(kw)==1 and 'globals' in kw:
            ourglobals = kw['globals']
        else:
            ourglobals = {}
        for f in files:
            f = os.path.abspath(f)
            fp = open(f)
            stuff = fp.read()
            self._load_string(stuff, ourglobals, f)
        self._mash()

    def loads(self, astring, namespace=None):
        """
        load user configuration from a Python string
        """
        self._load_string(astring, namespace)
        self._mash()

    def load_kw(self, **kw):
        """
        loads user configuration by keyword
        """
        self.load_dict(kw)

    def keys(self):
        return self._data.__dict__.keys()

    def items(self):
        return self._data.__dict__.items()

    def __iter__(self):
        return self._data.__dict__.__iter__()

    def iteritems(self):
        return self._data.__dict__.iteritems()

    def load_dict(self, d):
        """
        load a dictionary of user configuration
        """
        for k in d:
            if not k.startswith('_'):
                self._userconfig[k] = d[k]
        self._mash()

    def _load_string(self, astring, namespace=None, filename='<config>'):
        code_obj = compile(astring, filename, 'exec')
        if namespace is None:
            namespace = {}
        # suppress any keys that begin with an underscore            
        env = {}
        exec code_obj in namespace, env
        for key in (k for k in env if not k.startswith('_')):
            self._userconfig[key] = env[key]

    def reset(self):
        """
        set the config object back to defaults, discarding
        all user-specified values
        """
        self._userconfig.clear()
        self.trim()

    def _process_matcher(self, matcher):
        overlay = self._overlay
        scopes = self._context

        if matcher.match(scopes):
            overlay.update(matcher.overlay)
            for kid in matcher.children:
                self._process_matcher(kid)

    def __getattr__(self, k):
        return getattr(self._data, k)

            
class ScopeMatcher(object):
    
    def __init__(self, param, match_obj, *children, **overlay):
        self.param = param
        self.match_obj = match_obj
        self.overlay = overlay
        self.children = list(children)

    def match(self, context):
        try:
            thing = context[self.param]
        except KeyError:
            return None
        else:
            return self._match(thing)

    def _match(self, thing):
        """
        subclasses should implement this.
        """
        raise NotImplementedError

class StrictMatcher(ScopeMatcher):

    def _match(self, other):
        return self.match_obj==other

class SimpleStringMatcher(ScopeMatcher):
    
    def _match(self, other):
        return (isinstance(other, basestring)
                and other.startswith(self.match_obj))

class GlobMatcher(ScopeMatcher):
    
    def _match(self, other):
        return (isinstance(other, basestring)
                and fnmatch.fnmatchcase(other, self.match_obj))

class RegexMatcher(ScopeMatcher):

    def __init__(self, match_obj, *children, **overlay):
        # OK to pass regex flags as (pattern, re.I)
        if isinstance(match_obj, (list, tuple)):
            match_obj = re.compile(*match_obj)
        else:
            match_obj = re.compile(match_obj)
        ScopeMatcher.__init__(self, match_obj, *children, **overlay)


    def _match(self, other):
        return (isinstance(other, basestring) 
                and self.match_obj.match(other))


