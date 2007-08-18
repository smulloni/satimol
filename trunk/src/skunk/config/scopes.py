from threading import local

class ScopeManager(object):

    def __init__(self):
        self.data=local()
        self.defaults={}
        self.userconfig={}
        self.scopes={}
        self.matchers=[]
        self.overlay={}

    def mergeDefaults(self, **kw):
        kw.update(self.defaults)
        self.defaults.update(kw)
        self._mash()

    def setDefaults(self, **kw):
        self.defaults.update(kw)
        self._mash()

    def _mash(self):
        d=self.defaults.copy()
        d.update(self.userconfig)
        d.update(self.overlay)
        self.data.__dict__.clear()
        self.data.__dict__.update(d)

    def trim(self):
        self.overlay.clear()
        self.scopes.clear()
        self._mash()

    def scope(self, context):
        self.scopes.update(context)
        self.overlay.clear()
        for m in self.matchers:
            self._process_matcher(m)
        self._mash()

    def load(self, *files, **globals):
        if len(globals)==1 and 'globals' in globals:
            globals=globals['globals']
        for f in files:
            f=os.path.abspath(f)
            fp=open(f)
            stuff=fp.read()
            self._load_string(stuff, globals, f)
        self._mash()

    def loads(self, s, globals=None):
        self._load_string(s, globals)
        self._mash()

    def load_dict(self, d):
        for k in d:
            if not k.startswith('_'):
                self.userconfig[k]=d[k]
        self._mash()

    def _load_string(s, globals=None, filename='<config>'):
        codeObj=compile(s, filename, 'exec')
        if globals is None:
            globals={}
        # suppress any keys that begin with an underscore            
        env={}
        exec codeObj in globals, env
        for key in (k for k in env if not k.startswith('_')):
            self.userconfig[key]=env[key]

    def reset(self):
        self.userconfig.clear()
        self.trim()

    def _process_matcher(self, matcher):
        overlay=self.overlay
        scopes=self.scopes

        if matcher.match(scopes):
            overlay.update(matcher.overlay)
            for kid in matcher.children:
                self._process_matcher(kid)

    def __getattr__(self, k):
        return getattr(self.data, k)

            
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


