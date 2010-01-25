import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from school.lib.base import BaseController, render

log = logging.getLogger(__name__)

import datetime

from sqlalchemy import desc

from school.model.meta import Session
from school.model import Substitution, Educator, Group, SchoolYear

class SubstitutionsController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('substitution', 'substitutions')

    def index(self, format='html'):
        """GET /substitutions: All items in the collection"""
        # url('substitutions')
        c.year = SchoolYear.current()
        c.subs = Session.query(Substitution).order_by(Substitution.date).all()
        return render('substitutions/list.xml')

    def table(self):
        date = datetime.datetime.now() + datetime.timedelta(days=1)
        q = Session.query(Substitution).filter_by(date=date)
        teachers = {}
        subs = {}
        for sub in q:
            if not subs.has_key(sub.teacher):
                subs[sub.teacher] = {}
            subs[sub.teacher][sub.order] = sub

            for lesson in sub.lesson():
                if not teachers.has_key(lesson.teacher):
                    teachers[lesson.teacher] = {}
                teachers[lesson.teacher][lesson.order] = lesson
        c.teachers = teachers
        c.subs = subs
        return render('substitutions/table.xml')

    def create(self):
        """POST /substitutions: Create a new item"""
        # url('substitutions')
        date = datetime.datetime.strptime(request.params['date'], '%Y-%m-%d')
        order = int(request.params['order'])
        group = Session.query(Group).get(int(request.params['group']))
        part = int(request.params['part'])
        teacher = Session.query(Educator).get(request.params['educator'])
        comment = request.params['comment']

        s = Substitution(date, order, group, teacher, part, comment)
        Session.add(s)
        Session.commit()
        redirect_to(action="index")

    def new(self, format='html'):
        """GET /substitutions/new: Form to create a new item"""
        # url('new_substitution')
        c.today = datetime.date.today()
        c.groups = Session.query(Group).join(Group.year).\
                order_by(desc(SchoolYear.start), Group.name).all()
        c.educators = Session.query(Educator).\
                order_by(Educator.last_name).all()
        c.year = SchoolYear.current()
        return render('substitutions/new.xml')

    def update(self, id):
        """PUT /substitutions/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('substitution', id=ID),
        #           method='put')
        # url('substitution', id=ID)

    def delete(self, id):
        """DELETE /substitutions/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('substitution', id=ID),
        #           method='delete')
        # url('substitution', id=ID)
        s = Session.query(Substitution).get(id)
        Session.delete(s)
        Session.commit()
        redirect_to('substitutions')

    def show(self, id, format='html'):
        """GET /substitutions/id: Show a specific item"""
        # url('substitution', id=ID)

    def edit(self, id, format='html'):
        """GET /substitutions/id/edit: Form to edit an existing item"""
        # url('edit_substitution', id=ID)
