import logging
import datetime

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from sqlalchemy.exceptions import IntegrityError

from school.lib.base import BaseController, render

from school.model.meta import Session
from school.model import LuckyNumber

from pylons.decorators import validate
from school.forms import AddWeekLuckyNumbersForm

log = logging.getLogger(__name__)


class LuckyController(BaseController):

    def all(self):
        all = Session.query(LuckyNumber).all()
        response.headers['content-type'] = 'text/plain'
        return ['%s - %s\n' % (lucky.date, lucky.number) for lucky in all]

    def current(self):
        now = datetime.datetime.now()
        weekday = datetime.datetime.weekday(now)
        change_hour = 15
        if weekday < 5 and now.time() < datetime.time(hour=change_hour):
            day = now.date()
        else:
            day = self._closest_working_day(now)
        response.headers['content-type'] = 'text/plain'
        current = Session.query(LuckyNumber).filter_by(date=day).first()
        if current is None:
            return "No lucky number set! Kill the school leader ;]"
        else:
            return str(current.number)

    def week(self):
        now = datetime.datetime.now()
        weekday = datetime.datetime.weekday(now)
        change_hour = datetime.time(hour=15)
        if weekday < 4 or (weekday == 4 and now.time() < change_hour):
            start_week = now - datetime.timedelta(weekday)
        else:
            start_week = self._closest_working_day(now)
        end_week = start_week + datetime.timedelta(4)

        week = Session.query(LuckyNumber).\
                       filter(LuckyNumber.date >= start_week).\
                       filter(LuckyNumber.date <= end_week).\
                       all()

        response.headers['content-type'] = 'text/plain'
        return ['%s - %s\n' % (lucky.date, lucky.number) for lucky in week]

    def draw(self):
        response.headers['content-type'] = 'text/plain'
        return '\n'.join([str(x) for x in LuckyNumber.draw()])

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

    def add_week_form(self):
        last = LuckyNumber.last()
        c.numbers = LuckyNumber.draw()
        c.datetime = datetime
        c.first_date = self._closest_working_day(last.date)
        return render('lucky/add_week_form.xml')

    @validate(schema=AddWeekLuckyNumbersForm(), form='add_week_form')
    def add_week(self):
        for lucky in self.form_result['lucky']:
            if lucky['date'] and lucky['number']:
                Session.add(LuckyNumber(lucky['date'], lucky['number']))

        try:
            Session.commit()
        except IntegrityError as e:
            return "There is already lucky number for %s!" % e.params[0]
        else:
            return "Added!"
