import logging
import datetime

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from sqlalchemy.exceptions import IntegrityError

from school.lib.base import BaseController, render

from school.model.meta import Session
from school.model import LuckyNumber

from pylons.decorators import validate
from pylons.decorators.rest import restrict

from repoze.what.predicates import not_anonymous
from repoze.what.plugins.pylonshq import ActionProtector

import webhelpers.paginate as paginate

from school.forms import AddLuckyNumbersForm

log = logging.getLogger(__name__)


class LuckyController(BaseController):

    def index(self):
        change_hour = 15
        c.current = LuckyNumber.current(change_hour)
        c.week = LuckyNumber.current_week(change_hour)
        c.left = LuckyNumber.left()
        return render('lucky/index.xml')

    def all(self):
        c.numbers = Session.query(LuckyNumber).order_by(LuckyNumber.date).all()
        return render('lucky/list.xml')

    def search(self):
        number = int(request.params.get('number'))
        c.numbers = Session.query(LuckyNumber).order_by(LuckyNumber.date).\
                            filter_by(number=number)
        return render('lucky/list.xml')

    def current(self):
        # TODO This could be set in the settings file
        change_hour = 15
        c.lucky = LuckyNumber.current(change_hour)
        return render('lucky/current.xml')

    def date(self, date):
        """
        Lucky number for the given date.

        :param date: Date in format: %Y-%m-%d

        """
        date = date = datetime.datetime.strptime(date, '%Y-%m-%d')
        c.lucky = Session.query(LuckyNumber).filter_by(date=date).first()
        return render('lucky/current.xml')

    def current_week(self):
        """
        Lucky numbers for current or next week.

        """
        change_hour = 15
        c.numbers = LuckyNumber.current_week(change_hour)
        return render('lucky/list.xml')

    def draw(self):
        c.numbers = LuckyNumber.draw()
        return render('lucky/draw.xml')

    def _closest_working_day(self, date):
        """
        Return closest working day but never the same day!

        """
        weekday = datetime.datetime.weekday(date)
        if weekday < 4:
            td = 1
        else:
            td = 7 - weekday
        return date + datetime.timedelta(td)

    @ActionProtector(not_anonymous())
    def add_week_form(self):
        """
        Display the form to input numbers only for one week.

        """
        last = LuckyNumber.last()

        remain_this_week = 4-datetime.date.weekday(last.date)
        if remain_this_week < 1:
            c.first_date = last.date + datetime.timedelta(-remain_this_week + 3)
            c.count = 5
        else:
            c.first_date = last.date + datetime.timedelta(1)
            c.count = remain_this_week

        c.numbers = LuckyNumber.draw()
        if len(c.numbers) < c.count:
            c.count = len(c.numbers)

        c.datetime = datetime

        return render('lucky/add_form.xml')

    @ActionProtector(not_anonymous())
    @restrict('POST')
    @validate(schema=AddLuckyNumbersForm(), form='add_week_form')
    def add(self):
        numbers = self.form_result['lucky']
        added = False
        for lucky in numbers:
            if lucky['date'] and lucky['number']:
                added = True
                Session.add(LuckyNumber(lucky['date'], lucky['number']))

        try:
            Session.commit()
        except IntegrityError as e:
            session['flash'] = 'There is already lucky number for %s' % e.params[0]
            session.save()
            return redirect_to('lucky_add')
        else:
            if not added:
                session['flash'] = 'No lucky number has been added!'
            else:
                session['flash'] = 'Lucky numbers have been added!'
            session.save()
            redirect_to('lucky_home')
