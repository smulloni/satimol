from skunk.config import Configuration
from skunk.components import call_component

class BuffetPlugin(object):
    def __init__(self, extra_vars_func=None, options=None):
        self.extra_vars_func=extra_vars_func
        self.options=options or {}


    def load_template(self, templatename):
        "Find a template specified in python 'dot' notation."
        # we don't need to do anything here.
        pass

    def render(self,
               info,
               format=None, #ignored
               fragment=None, #ignored
               template=None):
        "Renders the template to a string using the provided info."
        info=info.copy()
        if template is None:
            template=Configuration.defaultTemplateFilename
        if self.get_extra_vars_func:
            info.update(self.get_extra_vars_func())
        return call_component(template,
                              info,
                              'string',
                              **self.options)
                          
    

__all__=['BuffetPlugin']
