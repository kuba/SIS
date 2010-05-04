"""
Configure auth middleware (repoze.what-quicstart).

This file is based on http://code.gustavonarea.net/
repoze.what-quickstart/index.html#how-to-set-it-up.

"""
from repoze.what.plugins.quickstart import setup_sql_auth
from repoze.who.plugins.formcookie import make_redirecting_plugin

from school.model.meta import Session
from school.model.auth import AuthUser, AuthGroup, AuthPermission


def add_auth(app, app_conf, prefix='auth.'):
    """
    Add authentication and authorization middleware to the ``app``.

    :param app_conf: The application's local configuration. Normally specified
                     in the [app:<name>] section of the Paste ini file
                     (where <name> defaults to main).

    :param prefix: Prefix for the config related to the auth.
    :type prefix: :class:`str`

    """
    # Cookie form plugin
    form_plugin = make_redirecting_plugin(
                    login_form_path='/login',
                    login_handler_path='/login_handler',
                    logout_handler_path='/logout',
                    rememberer_name='cookie',
            )

    cookie_secret = app_conf.get(prefix+'cookie_secret', None)
    cookie_timeout = app_conf.get(prefix+'cookie_timeout', None)
    cookie_reissue_time = app_conf.get(prefix+'cookie_reissue_time', None)

    # Perform type conversion, sice timeout and reisue_time must be int or None
    if cookie_timeout is not None:
        cookie_timeout = int(cookie_timeout)
    if cookie_reissue_time is not None:
        cookie_reissue_time = int(cookie_reissue_time)

    return setup_sql_auth(app, AuthUser, AuthGroup, AuthPermission, Session,
                          form_plugin=form_plugin,
                          cookie_secret=cookie_secret,
                          cookie_timeout=cookie_timeout,
                          cookie_reissue_time=cookie_reissue_time)
