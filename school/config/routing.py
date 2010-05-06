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

    # CUSTOM ROUTES HERE

    # Lucky number routes
    with map.submapper(path_prefix=r'/lucky', controller='lucky') as m:
        m.connect('lucky_home', r'', action='index')
        m.connect('lucky_search', r'/search', action='search')
        m.connect('lucky_draw', r'/draw', action='draw')
        m.connect('lucky_all', r'/all', action='all')
        m.connect('lucky_add_form', r'/add', action='add',
                  conditions={'method':'POST'})
        m.connect('lucky_add', r'/add', action='add_week_form')
        m.connect('lucky_date', r'/{date:\d\d\d\d-\d\d-\d\d}', action='date')

    # Substitutions routes
    with map.submapper(controller='substitutions') as m:
        m.connect(r'', action='index')

        # substitutions table
        with m.submapper(path_prefix='/z', action='table') as table_m:
            table_m.connect('substitutions_table', r'')
            table_m.connect('substitutions_table_date',
                    r'/{date:\d\d\d\d-\d\d-\d\d}')
    # substitutions RESTful mapping
    map.resource('substitution', 'substitutions')

    # Now! routes
    with map.submapper(path_prefix='/now', controller='now') as m:
        m.connect('now_home', r'', action='index')
        m.connect('now_id', '/{id:\d+}', action='now_id')
        m.connect('now_name', '/{surname}', action='now')

    # Schedule routes
    with map.submapper(path_prefix='/schedule', controller='schedule') as m:
        m.connect('schedule_home', r'', action='index')

        # full schedules
        m.connect('schedule_teachers', r'/teachers', action='get_teachers')
        m.connect('schedule_groups', r'/groups', action='get_groups')

        # weekly schedules
        with m.submapper(path_prefix='/week') as week_m:
            with week_m.submapper(path_prefix='/{group_name:\d\w+}',
                    action='group_week') as group_m:
                group_m.connect('schedule_group_week', r'')
                group_m.connect('schedule_group_course_week', r'+{course_name}')
            week_m.connect('schedule_teacher_week', r'/{teacher_name}',
                action='teacher_week')

        # group daily schedule
        with m.submapper(path_prefix='/{group_name:\d\w+}',
                         action='get_group') as group_m:
            group_m.connect('schedule_group', r'/{day_name}')
            group_m.connect('schedule_group_today', r'')

            # course daily schedule
            with group_m.submapper(path_prefix='+{course}') as course_m:
                course_m.connect('schedule_group_course_today', r'')
                course_m.connect('schedule_group_course', r'/{day_name}')
        
        # teacher daily schedule
        with m.submapper(path_prefix='/{teacher_name}',
                         action='get_teacher') as teacher_m:
            teacher_m.connect('schedule_teacher_today', r'')
            teacher_m.connect('schedule_teacher', r'/{day_name}')

    # Pages routes
    with map.submapper(controller='pages') as m:
        m.connect('home', r'/', action='index')
        m.connect('about', r'/about', action='about')

    # Auth routes
    map.connect('login', r'/login', controller='auth', action='login')

    # DEFAULT routes
    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')

    return map
