from bokeh.core.properties import Instance, String, Dict
from bokeh.models import ColumnDataSource, LayoutDOM
from bokeh.util.compiler import TypeScript
from os import path
import hashlib
import json
import bokeh.util.compiler

directory = path.dirname(path.realpath(__file__))
with open(path.join(directory, 'jsmol.ts'), 'r') as f:
    TS_CODE = f.read()


# This custom extension model will have a DOM view that should layout-able in
# Bokeh layouts, so use ``LayoutDOM`` as the base class. If you wanted to create
# a custom tool, you could inherit from ``Tool``, or from ``Glyph`` if you
# wanted to create a custom glyph, etc.
class JSMol(LayoutDOM):

    # The special class attribute ``__implementation__`` should contain a string
    # of JavaScript (or CoffeeScript) code that implements the JavaScript side
    # of the custom extension model.
    __implementation__ = TypeScript(TS_CODE)

    # Below are all the "properties" for this model. Bokeh properties are
    # class attributes that define the fields (and their types) that can be
    # communicated automatically between Python and the browser. Properties
    # also support type validation. More information about properties in
    # can be found here:
    #
    #    https://bokeh.pydata.org/en/latest/docs/reference/core.html#bokeh-core-properties

    # This is a Bokeh Dict providing the JSMol "Info variable"
    # See http://wiki.jmol.org/index.php/Jmol_JavaScript_Object/Info
    info = Dict(String, String)

    # Currently (mis)using this to pass a script to be executed since there
    # doesn't seem to be a better solution (?)
    # https://groups.google.com/a/continuum.io/forum/#!topic/bokeh/0m17mNMnTys
    script_source = Instance(ColumnDataSource)

    # Path to JSMol javascript file (can be full or relative URL), e.g.
    # e.g. https://chemapps.stolaf.edu/jmol/jsmol/JSmol.min.js
    # or jsmol/JSmol.min.js
    js_url = String

### DGR, Aug2021
def use_cached_model(model,implementation):
    '''Function to employ a pre-cached model, skipping the NodeJS dependency of jsmol_bokeh_extension. Shall be passed
    to set_cache_hook(). The model should be stored at the same folder as the modules. Adapted from
    https://github.com/emerald-geomodelling/BokehGarden/blob/149909faa86fd31428e9974e533c3a3d1c3ab295/bokeh_garden/compiler_cache.py
    with some modifications on how hashes are obtained: here, the module name is used instead of the full code.
    '''
    cached_model = None
    full_name = model.full_name 
    # Use this name to hash & to control json files, replacing dots by underscores
    hashval = hashlib.sha256(full_name.encode("utf-8")).hexdigest()
    json_fname = full_name.replace(".","_") + ".json"
    json_route = path.join(directory,json_fname)
    # Load the cached model from file when it is present and check whether the hash matches the hash computed here
    if (path.isfile(json_route)):
        with open(json_route,"r") as fjson:
            try:
                cached_model = json.load(fjson)
            except:
                pass
        if (hashval != cached_model["hash"]):
            cached_model = None

    # Fallback: if the pre-compiled model is not available, and thus cached_model is None, 
    # compile it via .nodejs_compile() and dump to file for further use, so it is only compiled at first run
    if (not cached_model):
        compiled_code = bokeh.util.compiler.nodejs_compile(implementation.code,lang=implementation.lang,file=implementation.file)
        cached_model = {"hash":hashval,"code":dict(compiled_code)}
        with open(json_route,"w") as fjson:
            json.dump(cached_model,fjson)
    # And now transform the "code" to AttrDict so it can be accessed by .attr syntax
    cached_model["code"] = bokeh.util.compiler.AttrDict(cached_model["code"])
    return cached_model["code"]

bokeh.util.compiler.set_cache_hook(use_cached_model)