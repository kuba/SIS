import cgi

from paste.urlparser import PkgResourcesParser
from pylons import request, tmpl_context as c
from pylons.controllers.util import forward
from pylons.middleware import error_document_template
from webhelpers.html.builder import literal

from school.lib.base import BaseController, render

class ErrorController(BaseController):

    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.

    """

    def document(self):
        """Render the error document"""
        resp = request.environ.get('pylons.original_response')
        content = literal(resp.body) or cgi.escape(request.GET.get('message', ''))
        c.code=cgi.escape(request.GET.get('code', str(resp.status_int)))
        c.message=content
        return render('error.xml')
