# Entry point for cPanel / Passenger hosting (Truehost and similar).
#
# cPanel's "Setup Python App" overwrites this file with its own loader when the
# application is created or its settings are saved, so the contents below are
# deliberately identical to what cPanel generates. Keep them in step, otherwise
# a later "git pull" on the server fails with a local-changes conflict.
#
# In Setup Python App use:
#   Application startup file : app.py
#   Application Entry point  : app
# (pointing the startup file at passenger_wsgi.py makes this loader import
# itself over and over until the request dies with a 500.)
import importlib.machinery
import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


def load_source(modname, filename):
    loader = importlib.machinery.SourceFileLoader(modname, filename)
    spec = importlib.util.spec_from_file_location(modname, filename, loader=loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


wsgi = load_source('wsgi', 'app.py')
application = wsgi.app
