import logging

from pylons import url, request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from sis.lib.base import BaseController, render

log = logging.getLogger(__name__)

class AuthController(BaseController):

    def login(self):
        c.came_from = str(request.params.get('came_from', '')) or url('/')
        return render('auth/login_form.xml')
