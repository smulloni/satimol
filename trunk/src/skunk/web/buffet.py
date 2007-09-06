import logging

from pkg_resources import iter_entry_points

from skunk.config import Configuration
from skunk.util.decorators import rewrap

log=logging.getLogger(__name__)

Configuration.setDefaults(defaultTemplatingEngine='stml',
                          templateEngineOptions={},
                          defaultControllerTemplate=None)


def template(template=None,
             **template_opts):
    """
    a decorator which indicates that the function should use a
    template.
    """
    def wrapper(func):
        def newfunc(*args, **kwargs):
            data=func(*args, **kwargs)
            if not isinstance(data, dict):
                # you decided not to use a template, bye-bye
                return data
            tmpl=(template or
                  Configuration.defaultControllerTemplate or
                  Configuration.defaultTemplate)
            if not tmpl:
                raise ValueError('no template specified or found in configuration')
            t=tmpl.split(':', 1)
            if len(t)==1:
                enginename=Configuration.defaultTemplatingEngine
            else:
                enginename, tmpl=t
            del t
            log.debug("engine: %s, template: %s", enginename, tmpl)
            engineclass=TEMPLATING_ENGINES[enginename]
            extra_vars_func=template_opts.pop('extra_vars_func', None)
            format=template_opts.pop('format', None)
            fragment=template_opts.pop('fragment', None)
            tmplopts=Configuration.templateEngineOptions.get(enginename)
            if tmplopts:
                tmplopts=tmplopts.copy()
                tmplopts.update(template_opts)
            else:
                tmplopts=template_opts
            log.debug('template options: %s', tmplopts)
            engine=engineclass(extra_vars_func, **tmplopts)
            log.debug("engine instance attributes: %s", vars(engine))
            return engine.render(data, format, fragment, tmpl)
        return rewrap(func, newfunc)
    return wrapper

TEMPLATING_ENGINES={}
for x in iter_entry_points('python.templating.engines'):
    try:
        TEMPLATING_ENGINES[x.name] = x.load()
    except:
        log.warn("couldn't load templating engine %s", x.name)
del x    


__all__=['TEMPLATING_ENGINES', 'template']
