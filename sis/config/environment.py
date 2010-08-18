"""SIS environment configuration."""
import os

from genshi.template import TemplateLoader
from pylons.configuration import PylonsConfig
from sqlalchemy import engine_from_config

import sis.lib.app_globals as app_globals
import sis.lib.helpers
from sis.config.routing import make_map
from sis.model import init_model

def load_environment(global_conf, app_conf):
    """Configure the Pylons environment for SIS."""
    config = PylonsConfig()

    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package='sis', paths=paths)

    config['routes.map'] = make_map(config)
    config['pylons.app_globals'] = app_globals.Globals(config)
    config['pylons.h'] = sis.lib.helpers

    # Setup cache object as early as possible
    import pylons
    pylons.cache._push_object(config['pylons.app_globals'].cache)

    # Create the Genshi TemplateLoader
    config['pylons.app_globals'].genshi_loader = TemplateLoader(
        paths['templates'], auto_reload=True)

    # Setup the SQLAlchemy database engine
    engine = engine_from_config(config, 'sqlalchemy.')
    init_model(engine)

    # CONFIGURATION OPTIONS HERE (note: all config options will override
    # any Pylons config options)

    return config
