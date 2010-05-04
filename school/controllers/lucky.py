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

from school.forms import AddLuckyNumbersForm

log = logging.getLogger(__name__)


class LuckyController(BaseController):

    def all(self):
        all = Session.query(LuckyNumber).order_by(LuckyNumber.date).all()
        return ['%s - %s<br />' % (lucky.date, lucky.number) for lucky in all]

    def current(self):
        # TODO This could be set in the settings file
        change_hour = 15

        now = datetime.datetime.now()
        if now.hour >= change_hour:
            start_date = now + datetime.timedelta(1)
        else:
            start_date = now

        lucky = Session.query(LuckyNumber).\
                        filter(LuckyNumber.date >= start_date).\
                        order_by(LuckyNumber.date).first()
        if lucky is None:
            return "No lucky number set!"
        else:
            return "%s - %s" % (lucky.date, lucky.number)

    def week(self):
        change_hour = 15

        now = datetime.datetime.now()
        today = now.date()
        if now.hour >= change_hour:
            closest_day = today + datetime.timedelta(1)
        else:
            closest_day = today

        # We will fetch two weeks from the database
        start_date = today - datetime.timedelta(datetime.date.weekday(now))
        end_date = start_date + datetime.timedelta(13)

        numbers = Session.query(LuckyNumber).\
                          filter(LuckyNumber.date >= start_date).\
                          filter(LuckyNumber.date <= end_date).\
                          order_by(LuckyNumber.date).\
                          all()
        first_week = []
        second_week = []
        for number in numbers:
            if number.date < end_date - datetime.timedelta(7):
                first_week.append(number)
            else:
                second_week.append(number)

        def pretty_numbers(n):
            return ["%s - %s<br />" % (l.date, l.number) for l in n]

        if first_week[-1].date  >= closest_day:
            return pretty_numbers(first_week)
        elif len(second_week) > 0:
            return pretty_numbers(second_week)
        else:
            return "No lucky numbers for this or incoming week"

    def draw(self):
        return [str(x) + "<br />" for x in LuckyNumber.draw()]

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
        for lucky in self.form_result['lucky']:
            if lucky['date'] and lucky['number']:
                Session.add(LuckyNumber(lucky['date'], lucky['number']))

        try:
            Session.commit()
        except IntegrityError as e:
            return redirect_to('lucky_add')
            return "There is already lucky number for %s!" % e.params[0]
        else:
            redirect_to('lucky')
