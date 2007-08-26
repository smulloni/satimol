from threading import local

class ScopeManager(object):

    def __init__(self):
        # the attributes accessed by the __getattr__ hook
        self._data=local()
        # the defaults
        self._defaults={}
        # user configuration 
        self._userconfig={}
        # the context
        self._context=local().__dict__
        # functions that manipulate the environment according to the scope
        self._matchers=[]
        # overrides added by scoping
        self._overlay=local().__dict__

    def setDefaults(self, **kw):
        """
        set default values
        """
        self._defaults.update(kw)
        self._mash()

    def _mash(self):
        d=self._defaults.copy()
        d.update(self._userconfig)
        d.update(self._overlay)
        self._data.__dict__.clear()
        self._data.__dict__.update(d)

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

    def load(self, *files, **globals):
        """
        load user configuration from files
        """
        if len(globals)==1 and 'globals' in globals:
            globals=globals['globals']
        for f in files:
            f=os.path.abspath(f)
            fp=open(f)
            stuff=fp.read()
            self._load_string(stuff, globals, f)
        self._mash()

    def loads(self, s, globals=None):
        """
        load user configuration from a Python string
        """
        self._load_string(s, globals)
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
                self._userconfig[k]=d[k]
        self._mash()

    def _load_string(s, globals=None, filename='<config>'):
        codeObj=compile(s, filename, 'exec')
        if globals is None:
            globals={}
        # suppress any keys that begin with an underscore            
        env={}
        exec codeObj in globals, env
        for key in (k for k in env if not k.startswith('_')):
            self._userconfig[key]=env[key]

    def reset(self):
        """
        set the config object back to defaults, discarding
        all user-specified values
        """
        self._userconfig.clear()
        self.trim()

    def _process_matcher(self, matcher):
        overlay=self._overlay
        scopes=self._context

        if matcher.match(scopes):
            overlay.update(matcher.overlay)
            for kid in matcher.children:
                self._process_matcher(kid)

    def __getattr__(self, k):
        return getattr(self._data, k)

            
class ScopeMatcher(object):
    
    def __init__(self, param, matchObj, *children, **overlay):
        self.param=param
        self.matchObj=matchObj
        self.overlay=overlay
        self.children=list(children)

    def match(self, context):
        try:
            thing=context[self.param]
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
        return self.matchObj==other

class SimpleStringMatcher(ScopeMatcher):
    
    def _match(self, other):
        return (isinstance(other, basestring)
                and other.startswith(self.matchObj))

class GlobMatcher(ScopeMatcher):
    
    def _match(self, other):
        return (isinstance(other, basestring)
                and fnmatch.fnmatchcase(other, self.matchObj))

class RegexMatcher(ScopeMatcher):

    def __init__(self, matchObj, *children, **overlay):
        # OK to pass regex flags as (pattern, re.I)
        if isinstance(matchObj, (list, tuple)):
            matchObj=re.compile(*matchObj)
        else:
            matchObj=re.compile(matchObj)
        ScopeMatcher.__init__(self, matchObj, *children, **overlay)


    def _match(self, other):
        return (isinstance(other, basestring) 
                and self.matchObj.match(other))


