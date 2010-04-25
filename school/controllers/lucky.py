import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from school.lib.base import BaseController, render

from school.model.meta import Session
from school.model import LuckyNumber

log = logging.getLogger(__name__)


class LuckyController(BaseController):

    def all(self):
        all = Session.query(LuckyNumber).all()
        response.headers['content-type'] = 'text/plain'
        return ['%s - %s\n' % (lucky.date, lucky.number) for lucky in all]

    def draw(self):
        response.headers['content-type'] = 'text/plain'
        return '\n'.join([str(x) for x in LuckyNumber.draw()])
