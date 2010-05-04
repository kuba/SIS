import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from school.lib.base import BaseController, render

log = logging.getLogger(__name__)

class AuthController(BaseController):

    def index(self):
        # Return a rendered template
        #return render('/auth.mako')
        # or, return a response
        return 'Hello World'

    def login(self):
        came_from = str(request.params.get('came_from', '')) or '/'
        return '<form method="post" action="/login_handler?came_from=%s"><input type="text" name="login" /><input type="pasword" name="password" /><input type="submit" /></form>' % came_from
