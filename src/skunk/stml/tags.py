import webob.exc

from skunk.config import Configuration
from skunk.stml.exceptions import STMLSyntaxError
from skunk.stml.parser import Expr, Node
from skunk.stml.signature import Signature
from skunk.stml.valformat import ValFormatRegistry
from skunk.stml.log import debug
from skunk.stml.tagutils import get_temp_name

def _redirect_func(location, status):
    raise webob.exc.status_map(status, location=location)()

Configuration.setDefaults(redirectFunc=_redirect_func)

class BlockTag(Node):
    """
    Base class for block tags, that need to be closed
    with a second tag.
    """
    isBlock=True
    localTagDict={}
    _top=False

class EmptyTag(Node):
    _top=False

class CommentTag(BlockTag):
    """
    a tag that emits no code.
    """
    tagName='comment'
    _top=True

    def genCode(self, codeStream):
        pass

class BriefCommentTag(CommentTag):
    """
    equivalent to <:comment:>, but written <:#:>
    """
    tagName='#'
    _top=True

class ValTag(EmptyTag):
    """
    Implementation of the <:val `expr` fmt=`None`:> tag, which
    outputs a stringified value of its expr argument, formatted
    by the formatter fmt, if not None.
    """
    signature=Signature(('expr', ('fmt', None)))
    modules=[('skunk.stml', 'stml')]
    tagName='val'
    _top=True

    def genCode(self, codeStream):
        expr=self._parsed_args['expr']
        fmt=self._parsed_args['fmt']
        codeStream.writeln('__h.stml.write_val(%r, OUTPUT, %r)' % (expr, fmt))

class ElseTag(EmptyTag):
    tagName='else'
    
    def genCode(self, codeStream):
        codeStream.dedent()
        codeStream.writeln('else:')
        codeStream.indent()
        # in case no other code is generated for the block
        codeStream.writeln('pass')
                 
class ElifTag(EmptyTag):
    tagName='elif'
    signature=Signature(('expr',))
    
    def genCode(self, codeStream):
        codeStream.dedent()
        codeStream.writeln('elif %r:' % self._parsed_args['expr'])
        codeStream.indent()
        # in case no other code is generated for the block
        codeStream.writeln('pass')


class IfTag(BlockTag):
    localTagDict={'else' : ElseTag,
                  'elif' : ElifTag}
    signature=Signature(('expr',))
    tagName='if'
    _top=True
    
    def genCode(self, codeStream):
        codeStream.writeln('if %r:' % self._parsed_args['expr'])
        codeStream.indent()
        codeStream.writeln('pass')
        for k in self.children:
            if isinstance(k, basestring):
                codeStream.writeln('OUTPUT.write(%r)' % k)
            else:
                k.genCode(codeStream)
        codeStream.dedent()


class BreakTag(EmptyTag):
    tagName='break'

    def genCode(self, codeStream):
        codeStream.writeln('break')


class ContinueTag(EmptyTag):
    tagName='continue'
    
    def genCode(self, codeStream):
        codeStream.writeln('continue')

class WhileTag(BlockTag):
    localTagDict={'else' : ElseTag,
                  'break' : BreakTag,
                  'continue' : ContinueTag}
    signature=Signature(('expr',))
    tagName='while'
    _top=True
    
    def genCode(self, codeStream):
        codeStream.writeln('while %r:' % self._parsed_args['expr'])
        codeStream.indent()
        codeStream.writeln('pass')
        for k in self.children:
            if isinstance(k, basestring):
                codeStream.writeln('OUTPUT.write(%r)' % k)
            else:
                k.genCode(codeStream)
        codeStream.dedent()

class CallTag(EmptyTag):
    signature=Signature(('expr',))
    tagName='call'
    _top=True

    def genCode(self, codeStream):
        tocall=self._parsed_args['expr']
        if not isinstance(tocall, Expr):
            raise STMLSyntaxError, "argument to call must be an expression"
        s=tocall.text
        for l in s.splitlines():
            codeStream.writeln(l)

class SetTag(EmptyTag):
    signature=Signature(('name', 'value'))
    tagName='set'
    _top=True

                          
    def genCode(self, codeStream):
        codeStream.writeln("%s=(%r)" % (self._parsed_args['name'],
                                        self._parsed_args['value']))

class DelTag(EmptyTag):
    signature=Signature(('name',))
    tagName='del'
    _top=True

    def genCode(self, codeStream):
        codeStream.writeln('del %s' % self._parsed_args['name'])


class DefaultTag(EmptyTag):
    signature=Signature(('name', ('value', '')))
    tagName='default'
    _top=True
                          
    def genCode(self, codeStream):
        name=self._parsed_args['name']
        value=self._parsed_args['value']
        codeStream.writeln('try:')
        codeStream.indent()
        codeStream.writeln(name)
        codeStream.dedent()
        codeStream.writeln('except (NameError, AttributeError):')
        codeStream.indent()
        codeStream.writeln('%s=%r' % (name, value))
        codeStream.dedent()
        

class ImportTag(EmptyTag):
    signature=Signature(('module', ('items', None), ('as', None)))
    tagName='import'
    _top=True
                         
    def genCode(self, codeStream):
        """
        This supports eight kinds of import:
        
        1. import M                     :==   <:import M:>
        2. import M as C                :==   <:import M as=C:> or <:import "M as C":>
        3. from M import X              :==   <:import M X:>
        4. from M import X, Y           :==   <:import M "X, Y":>
        5. from M import X as C         :==   <:import M X as=C:>
        6. from M import *              :==   <:import M *:>
        7. import M1, M2                :==   <:import "M1, M2":>
        8. import M1 as C, M2, M3 as D  :==   <:import "M1 as C, M2, M3 as D":>

        Note that case 6. cannot have an "as" clause.

        """
        module=self._parsed_args['module']
        items=self._parsed_args['items']
        asClause=self._parsed_args['as']

        if items=='*' and asClause is not None:
            raise STMLSyntaxError, "cannot use 'as' clause with from <module> import *"

        if items:
            codeStream.write('from %s import %s ' % (module, items))
        else:
            codeStream.write('import %s' % module)
        if asClause:
            codeStream.write('as %s' % asClause)
        codeStream.write('\n')


class ExceptTag(EmptyTag):
    signature=Signature((('exc', None),))
    tagName='except'

    def genCode(self, codeStream):
        exc=self._parsed_args['exc']
        codeStream.dedent()
        if exc is not None:
            codeStream.writeln('except %s:' % exc)
        else:
            codeStream.writeln('except:')
        codeStream.indent()
        codeStream.writeln('pass')

class FinallyTag(EmptyTag):
    tagName='finally'

    def genCode(self, codeStream):
        codeStream.dedent()
        codeStream.writeln('finally:')
        codeStream.indent()
        codeStream.writeln('pass')        


class TryTag(BlockTag):
    localTagDict={'finally' : FinallyTag,
                  'except' : ExceptTag,
                  'else' : ElseTag}
    tagName='try'
    _top=True

    def genCode(self, codeStream):
        codeStream.writeln('try:')
        codeStream.indent()
        codeStream.writeln('pass')
        for k in self.children:
            if isinstance(k, basestring):
                codeStream.writeln('OUTPUT.write(%r)' % k)
            else:
                k.genCode(codeStream)
        codeStream.dedent()                 


class RaiseTag(EmptyTag):
    signature=Signature((('exc', None),))
    tagName='raise'
    _top=True
    
    def genCode(self, codeStream):
        exc=self._parsed_args['exc']
        if exc is None:
            codeStream.writeln('raise')
        else:
            codeStream.writeln('raise (%r)' % exc)

class ForTag(BlockTag):
    localTagDict={'else' : ElseTag,
                  'break' : BreakTag,
                  'continue' : ContinueTag}
    signature=Signature(('expr', ('name', 'sequence_item')))
    tagName='for'
    _top=True
    
    def genCode(self, codeStream):
        codeStream.writeln('for %s in %s:'% \
                           (self._parsed_args['name'],
                            self._parsed_args['expr']))
        codeStream.indent()
        codeStream.writeln('pass')
        for k in self.children:
            if isinstance(k, basestring):
                codeStream.writeln('OUTPUT.write(%r)' % k)
            else:
                k.genCode(codeStream)
        codeStream.dedent()


class FilterTag(BlockTag):
    """
    A block tag that gathers the output inside the block
    and can:
       1. store it in a variable rather than output it directly;
       2. apply a filter to it;
       3. both;
       4. neither.
    """
    signature=Signature((('name', None),
                         ('filter', None)))
    tagName='filter'
    modules=['cStringIO',
             ('skunk.stml', 'stml')]
    _top=True

    def _init_temporary_namespace(cls, nsObj):
        # add the filter stack
        nsObj._filter_stack=[]
    _init_temporary_namespace=classmethod(_init_temporary_namespace)

    def genCode(self, codeStream):
        name=self._parsed_args.get('name')
        filter=self._parsed_args.get('filter')
        if not (name or filter):
            # just process the intervening tags
            codeStream.writeln('pass')
            for k in self.children:
                if isinstance(k, basestring):
                    codeStream.writeln('OUTPUT.write(%r)' % k)
                else:
                    k.genCode(codeStream)
        else:
            # replace the output stream with a temporary one,
            # putting the existing stream on a stack
            codeStream.writeln('__t._filter_stack.append(OUTPUT)')
            codeStream.writeln('OUTPUT=__h.cStringIO.StringIO()')
            # process the intervening tags in a try/finally block
            codeStream.writeln('try:')
            codeStream.indent()
            codeStream.writeln('pass')
            for k in self.children:
                if isinstance(k, basestring):
                    codeStream.writeln('OUTPUT.write(%r)' % k)
                else:
                    k.genCode(codeStream)
            codeStream.dedent()
            codeStream.writeln('finally:')
            codeStream.indent()
            if name is not None:
                # we have a name, so store the string in a variable
                # and replace the output stream.
                codeStream.writeln('%s=OUTPUT.getvalue()' % name)
                codeStream.writeln('OUTPUT=__t._filter_stack.pop()')
                codeStream.dedent()
                # apply filter, if any
                if filter:
                    codeStream.writeln('%s=__h.stml.get_formatter(%s)(%s)' % \
                                       (name, filter, name))
            else:
                assert filter
                # fancy switching with the stack to replace the original output stream
                # and write the formatted value of the temporary output stream to it
                codeStream.writeln('__t._filter_stack.append(OUTPUT.getvalue())')
                codeStream.writeln('OUTPUT=__t._filter_stack.pop(-2)')
                s='OUTPUT.write(__h.stml.get_formatter(%s)(__t._filter_stack.pop()))'
                codeStream.writeln(s % filter)
                codeStream.dedent()
                 

class SpoolTag(FilterTag):
    """
    This is a trivial subclass of FilterTag; the only
    difference is that the name parameter is required.
    """
    signature=Signature(('name', ('filter', None)))
    tagName='spool'


class UseTag(EmptyTag):
    """
    A tag which imports a tag vocabulary into a single STML component,
    optionally with a tag prefix.

    This tag does not generate code, but affects the effective tag
    vocabulary.  The tagdict therefore cannot be a Python expression,
    but a string indicating the complete __name__ of the tag
    dictionary, which must be defined in a Python module.
    """
    tagName='use'
    signature=Signature(('tagdict', ('prefix', None)))
    _top=True

    def parse(self, lexer):
        EmptyTag.parse(self, lexer)
        tagdict=self._parsed_args['tagdict']
        if not isinstance(tagdict, basestring):
            raise STMLSyntaxError, \
                  ("tagdict must be a string")
        prefix=self._parsed_args['prefix']
        i=tagdict.rfind('.')
        if i == -1:
            raise ValueError, \
                  "not an importable name"
        
        modname=tagdict[:i]
        objname=tagdict[i+1:]
        # let ImportError propagate
        mod=__import__(modname)
        moremods=modname.split('.')[1:]
        for m in moremods:
            mod=getattr(mod, m)
        # let AttributeError propagate
        obj=getattr(mod, objname)
        self.root.useTagLibrary(obj, prefix)

    def genCode(self, codeStream):
        pass
        

class ComponentTagBase(EmptyTag):
    modules=[('skunk.stml', 'stml'),
             ('skunk.cache', 'cache'),
             ('skunk.components', 'components')]
    _top=True

    def _marshal_args(self):
        args=self._parsed_args['__args__']
        if args is None:
            args={}
        else:
            if isinstance(args, dict):
                args=args.copy()
            else:
                raise ValueError, \
                      "__args__ must be a dict, got %r" % type(args)
            
        args.update(self._parsed_args['compArgs'])
        return args
        
class StringComponentTag(ComponentTagBase):
    tagName='component'
    signature=Signature(('name',
                         ('cache', 'no'),
                         ('namespace', None),
                         ('expiration', None),
                         ('__args__', None)),
                        None,
                        'compArgs')

    def genCode(self, codeStream):
        handle=self._parsed_args['name']
        cachePolicy=self._parsed_args['cache']
        compArgs=self._marshal_args()
        namespace=self._parsed_args['namespace']
        expiration=self._parsed_args['expiration']
        s=('OUTPUT.write(__h.components.call_component('
           '%r, %r, "string", __h.cache.decode(%r), '
           'expiration=%r, namespace=%r))') % \
           (handle, compArgs, cachePolicy, expiration, namespace)
        codeStream.writeln(s)
        

class DataComponentTag(ComponentTagBase):
    tagName='datacomp'
    signature=Signature(('var',
                         'name',
                         ('cache', 'no'),
                         ('namespace', None),
                         ('expiration', None),
                         ('__args__', None)),
                        None,
                        'compArgs')    

    def genCode(self, codeStream):
        varname=self._parsed_args['var']
        handle=self._parsed_args['name']
        cachePolicy=self._parsed_args['cache']
        compArgs=self._marshal_args()
        namespace=self._parsed_args['namespace']
        expiration=self._parsed_args['expiration']
        s=('%s=__h.components.call_component('
           '%r, %r, __h.cache.decode(%r), %r, %r)') % \
           (varname, handle, compArgs, cachePolicy, expiration, namespace)
        codeStream.writeln(s)


class IncludeComponentTag(ComponentTagBase):
    tagName='include'
    signature=Signature(('name',))

    def genCode(self, codeStream):
        handle=self._parsed_args['name']
        s='OUTPUT.write(__h.components.include(%r))' % handle
        codeStream.writeln(s)


class HaltTag(EmptyTag):
    tagName='halt'
    signature=Signature(())
    _top=True

    def genCode(self, codeStream):
        codeStream.writeln('raise ReturnValue')

class CompargsTag(EmptyTag):
    tagName='compargs'
    signature=Signature((), 'args', 'kwargs')
    _top=True
    modules=[('skunk.components', 'components')]

    def genCode(self, codeStream):
        args=self._parsed_args['args']
        kwargs=self._parsed_args['kwargs']
        s="__h.components.getCurrentComponent().check_args(%r, %r)" % (args, kwargs)
        codeStream.writeln(s)


class ArgsTag(EmptyTag):
    tagName='args'
    signature=Signature((), 'args', 'kwargs')
    _top=True
    modules=[('skunk.util.argextract', '_argextract'),
             ('skunk.config', 'config')]

    def write_get_args(self, codeStream, argsvar):
        """
        do whatever is necessary to get form/querystring args
        out of the environment.  The default works for
        skunk.web.
        """
        codeStream.writeln('%s=REQUEST.params.mixed()' % argsvar)

    def genCode(self, codeStream):
        wl=codeStream.writeln
        indent=codeStream.indent
        dedent=codeStream.dedent
        
        argsrcvar=get_temp_name()
        argsvar=get_temp_name()
        kwargsvar=get_temp_name()
        
        args=self._parsed_args['args']
        kwargs=self._parsed_args['kwargs']
        wl('%s = %r' % (argsvar, args))
        wl('%s = %r' % (kwargsvar, kwargs))
        
        self.write_get_args(codeStream, argsrcvar)
        
        wl('try:')
        indent()
        wl('locals().update(__h._argextract.extract_args(%s, *%s, **%s))' \
           % (argsrcvar, argsvar, kwargsvar))
        dedent()
        wl('finally:')
        indent()
        wl('del %s, %s, %s' % (argsrcvar, argsvar, kwargsvar))
        dedent()

class RedirectTag(EmptyTag):
    tagName="redirect"
    signature=Signature(('location', ('status', 301)))
    _top=True

    modules=[('skunk.config', 'config')]
    
    def write_redirect(self, codeStream, location, status):
        codeStream.writeln('__h.config.Configuration.redirectFunc(%r, %r)' \
                           % (location, status))

    def genCode(self, codeStream):
        location=self._parsed_args['location']
        status=self._parsed_args['status']
        self.write_redirect(codeStream, location, status)
    
class CacheTag(EmptyTag):
    tagName="cache"
    signature=Signature(('when', None))
    modules=[('skunk.util.timeconvert', 'timeconvert'),
             ('skunk.config',  'config')]
    _top=True

    def genCode(self, codeStream):
        when=self._parsed_args['when']
        s=("__expiration=__h.timeconvert.convert("
           "%r or __h.config.Configuration.defaultCacheExpiration)") % when
        codeStream.writeln(s)

class _logTagMixin(object):

    signature=Signature(('msg',), 'args')
    modules=[('skunk.userlogger', 'userlogger')]
    _top=True

    def genCode(self, codeStream):
        msg=self._parsed_args['msg']
        args=self._parsed_args['args']
        codeStream.writeln('__h.userlogger.getUserLogger().%s(%r, *%r)' % \
                           (self.tagName, msg, args))


class DebugTag(_logTagMixin,EmptyTag):
    tagName='debug'

class InfoTag(_logTagMixin,EmptyTag):
    tagName='info'

class WarnTag(_logTagMixin,EmptyTag):
    tagName='warn'

class ErrorTag(_logTagMixin,EmptyTag):
    tagName='error'

class ExceptionTag(_logTagMixin,EmptyTag):
    tagName='exception'

    
def _gettagclasses():
    return [(k, v) for k, v in globals().items() if k.endswith('Tag') and v.tagName]

_alltags=_gettagclasses()
BaseTags=dict([(v.tagName, v) for k, v in _alltags if v._top])
__all__=[x[0] for x in _alltags] + ['BaseTags', 'EmptyTag', 'BlockTag']
del _alltags
