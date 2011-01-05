# -*- coding: utf-8 -*-
import datetime

import logging
log = logging.getLogger(__name__)

from pkg_resources import Requirement, resource_filename

import StringIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from sqlalchemy.exceptions import IntegrityError

from pylons.decorators import validate
from pylons.decorators.rest import restrict

from repoze.what.predicates import not_anonymous
from repoze.what.plugins.pylonshq import ActionProtector

import formencode
from formencode import htmlfill

from sis.lib.base import BaseController, render
from sis.model.meta import Session
from sis.model import LuckyNumber

from sis.forms import AddLuckyNumbersForm, SearchLuckyForm


class LuckyController(BaseController):

    def index(self):
        change_hour = 15
        c.current = LuckyNumber.current(change_hour)
        c.week = LuckyNumber.current_week(change_hour)
        c.left = LuckyNumber.left()
        return render('lucky/index.xml')

    def all(self):
        """
        Render all lucky numbers.

        """
        c.numbers = Session.query(LuckyNumber).order_by(LuckyNumber.date).all()
        return render('lucky/list.xml')

    def left(self):
        """
        Render left lucky numbers.

        """
        c.numbers = LuckyNumber.left()
        return render('lucky/left.xml')

    def search_form(self):
        """
        Render search form.

        """
        number = request.params.get("number", None)
        if number is not None:
            redirect(url('lucky_search', number=number))
        return render('lucky/search.xml')

    def search(self, number):
        """
        Search lucky number. Redirect to form if invalid ``number``

        :param number: Number to search for.

        """
        schema = SearchLuckyForm()
        try:
            c.form_result = schema.to_python({'number' : number})
        except formencode.Invalid, error:
            c.form_result = error.value
            c.form_errors = error.error_dict or {}
            html = render('lucky/search.xml')
            return htmlfill.render(
                html,
                defaults=c.form_result,
                errors=c.form_errors
                )

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
        return render('lucky/week.xml')

    def current_week_pdf(self):
        """Lucky numbers for current or next week in pdf format."""
        change_hour = 15
        numbers = LuckyNumber.current_week(change_hour)

        if len(numbers) == 0:
            return redirect(url('lucky_week'))

        # Register fonts
        ubuntu_r = resource_filename(Requirement.parse("SIS"), "resources/Ubuntu-R.ttf")
        ubuntu_b = resource_filename(Requirement.parse("SIS"), "resources/Ubuntu-B.ttf")
        pdfmetrics.registerFont(TTFont('Ubuntu', ubuntu_r))
        pdfmetrics.registerFont(TTFont('Ubuntu Bold', ubuntu_b))

        numbers_pdf = StringIO.StringIO()
        doc = SimpleDocTemplate(numbers_pdf, pagesize=A4, topMargin=A4[1]*0.26)
        doc.author = 'SIS'
        doc.title = 'Szczęśliwy numerek'

        data = []
        for number in numbers:
            date = number.date.strftime("%d.%m.%y")
            data.append(('{0} -'.format(date), str(number.number)))

        table = Table(data)
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (0, -1), 'Ubuntu', 80),
            ('FONT', (1, 0), (1, -1), 'Ubuntu Bold', 80),
        ]))

        def header_and_footer(canvas, document):
            canvas.saveState()
            size = document.pagesize
            center = size[0] / 2

            canvas.setFont('Ubuntu', 80)
            canvas.drawCentredString(center,
                size[1] - document.topMargin / 2, "SZCZĘŚLIWY")
            canvas.drawCentredString(center, size[1] - document.topMargin + 20, 'NUMEREK')

            canvas.setFont('Ubuntu', 15)
            canvas.drawRightString(size[0] - document.rightMargin,
                document.bottomMargin - 20, "Samorząd Uczniowski")

            canvas.restoreState()

        doc.build([table], onFirstPage=header_and_footer,
            onLaterPages=header_and_footer)

        response.headers['Content-type'] = 'application/pdf'
        return numbers_pdf.getvalue()

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
        """Displays a form for adding lucky numbers
        for one week (at most).

        """
        today = datetime.date.today()
        weekday = datetime.date.weekday(today)
        monday = today - datetime.timedelta(weekday)

        # Find the first date a lucky number can be drown for
        last = LuckyNumber.last()
        if last.date < monday:
            c.first_date = monday
        else:
            c.first_date = self._closest_working_day(last.date)

        # Find the count of remaining days
        c.count = 5 - datetime.date.weekday(c.first_date)

        # Draw lucky numbers
        c.numbers = LuckyNumber.draw()

        # Not enough numbers to fill entire week
        if len(c.numbers) < c.count:
            c.count = len(c.numbers)

        c.datetime = datetime

        return render('lucky/add_form.xml')

    @ActionProtector(not_anonymous())
    @restrict('POST')
    @validate(schema=AddLuckyNumbersForm(), form='add_week_form')
    def add(self):
        form_numbers = self.form_result['lucky']
        numbers = []
        for lucky in form_numbers:
            if lucky['date'] and lucky['number']:
                ln = LuckyNumber(lucky['date'], lucky['number'])
                numbers.append(ln)

        Session.add_all(numbers)

        try:
            Session.commit()
        except IntegrityError as e:
            session['flash'] = 'There is already lucky number for %s' % e.params[0]
            session.save()
            return redirect(url('lucky_add'))
        else:
            if len(numbers) == 0:
                session['flash'] = 'No lucky number has been added!'
            else:
                session['flash'] = 'Lucky numbers have been added!'
            session.save()
            return redirect(url('lucky_home'))
