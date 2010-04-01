"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper

def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    map.minimization = False

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    map.connect(r'/s', controller='substitutions', action='index')
    map.connect('substitutions_table', r'/z', controller='substitutions', action='table')
    map.resource('substitution', 'substitutions')

    # CUSTOM ROUTES HERE
    map.connect('now_home', r'/now', controller='now', action='index')
    with map.submapper(path_prefix='/now', controller='now') as m:
        m.connect('now_id', '/{id:\d+}', action='now_id')
        m.connect('now_name', '/{surname}', action='now')

    map.connect('schedule_home', r'/plan', controller='schedule', action='index')
    with map.submapper(path_prefix='/plan', controller='schedule') as m:
        m.connect('schedule_teachers', r'/teachers', action='get_teachers')
        m.connect('schedule_group_course', r'/{group_name:\d\w+}+{course}/{day_name}', action='get_group')
        m.connect('schedule_group_course_today', r'/{group_name:\d\w+}+{course}', action='get_group')
        m.connect('schedule_group', r'/{group_name:\d\w+}/{day_name}', action='get_group')
        m.connect('schedule_group_today', r'/{group_name:\d\w+}', action='get_group')
        m.connect('schedule_teacher', r'/{teacher_name}/{day_name}', action='get_teacher')
        m.connect('schedule_teacher_today', r'/{teacher_name}', action='get_teacher')

    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')

    return map
