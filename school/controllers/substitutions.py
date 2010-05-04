import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from repoze.what.predicates import not_anonymous
from repoze.what.plugins.pylonshq import ActionProtector

from school.lib.base import BaseController, render

log = logging.getLogger(__name__)

import datetime

from sqlalchemy import desc, not_, and_

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
        c.subs = Session.query(Substitution).order_by(Substitution.date).all()
        return render('substitutions/list.xml')

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

    def table(self, date=None):
        """
        Create a table of substitutions.

        This action tries to recreate table view as based on
        http://www.staszic.edu.pl/zastepstwa/.

        It gathers following data:
        1. Which lessons do the group ussually have?
        2. Which lessons do groups have in substitution?
        3. Which groups (parts) are released (freed from the lesson)

        """
        if date is None:
            date = self._closest_working_day(datetime.datetime.today())
        else:
            date = datetime.datetime.strptime(date, '%Y-%m-%d')

        # Fetch substitutions from database
        q = Session.query(Substitution).filter_by(date=date)

        # Filter out pointless substitutions (those, which have both
        # parts set as False - no part is set)
        q = q.filter(not_(and_(Substitution.part1 == False,
                               Substitution.part2 == False)))
        subs = q.all()

        # Create a dictionary of educators and their lessons by schedule
        # (before) and the new ones which are substitutes (after).
        before = {}
        after = {}

        # Create released groups dict:
        # keys are lesson orders and value is the list of released groups
        released = {}

        def fill(d, educator, order, fill):
            """
            Helper function for filling the dict.

            It tries to fill as less data as possible so
            it merges parts intro groups.

            """
            if not d.has_key(educator):
                d[educator] = {}
            e = d[educator]
            if not e.has_key(order):
                e[order] = []
            o = e[order]
            g = fill[0]
            p = fill[1]

            if (g, None) in o:
                # We are trying to append part whereas entire group is present
                return
            if p is None:
                # We are appending entire group, delete "parted" entries
                for x in [1, 2]:
                    try:
                        o.remove((g, x))
                    except ValueError:
                        pass
            o.append(fill)

        def opposite_substituted(subs, sub):
            """
            Helper function for checking whether opposite group
            has been already substituted or the scheduled teacher
            is having a substituion which stops him from keeping
            the opposite group.

            It return True when both conditions are met:
            1. Opposite group doesn't have any substituion on that hour and,
            2. Scheduled teacher doesn't have any substition with other group.

            """
            SUBSTITUTED = False
            EDUCATOR_FREE = True
            opposite_part = sub.part % 2 + 1

            for s in subs:
                if s.order != sub.order:
                    # We want only the same lesson order
                    continue
                if s.group == sub.group and s.part == opposite_part:
                    SUBSTITUTED = True
                    break
                if s.teacher == lesson.teacher:
                    EDUCATOR_FREE = False

            if not SUBSTITUTED and EDUCATOR_FREE:
                return True
            else:
                return False

        class ReleasedGroup(Exception):
            pass

        # Loop the substitutions
        for sub in subs:
            if sub.teacher is None:
                # Group is released
                for lesson in sub.group_lesson():
                    fill(before, lesson.teacher, lesson.order,
                            (lesson.group, lesson.part))
                    if sub.part is not None and \
                            opposite_substituted(subs, sub):
                        fill(after, lesson.teacher, lesson.order,
                                (lesson.group, sub.part % 2 + 1))
                if not released.has_key(sub.order):
                    released[sub.order] = []
                released[sub.order].append((sub.group, sub.part))
                continue

            # What lesson does the group have normally?
            # And with which educator it is?
            for lesson in sub.group_lesson():
                fill(before, lesson.teacher, lesson.order,
                        (lesson.group, lesson.part))
                if lesson.part is None and sub.part is not None:
                    if opposite_substituted(subs, sub):
                        fill(after, lesson.teacher, lesson.order,
                                (lesson.group, sub.part % 2 + 1))

            for lesson in sub.teacher_lesson():
                fill(after, lesson.teacher, lesson.order,
                        (lesson.group, lesson.part))

            fill(after, sub.teacher, sub.order, (sub.group, sub.part))

        c.debug = ("Substitutions for %s:\nbefore:\t\t%r\nafter:\t\t%r\n" + \
                 "released:\t%r") % (date.date(), before, after, released)

        c.year = SchoolYear.current()
        c.date = date
        c.before = before
        c.after = after
        c.released = released

        return render('substitutions/table.xml')

    @ActionProtector(not_anonymous())
    def create(self):
        """POST /substitutions: Create a new item"""
        # url('substitutions')
        date = datetime.datetime.strptime(request.params['date'], '%Y-%m-%d')
        order = int(request.params['order'])
        group = Session.query(Group).get(int(request.params['group']))
        part = int(request.params['part'])
        raw_educator = request.params['educator']
        if raw_educator == 0:
            teacher = None
        else:
            teacher = Session.query(Educator).get(raw_educator)
        comment = request.params['comment']

        s = Substitution(date, order, group, teacher, part, comment)
        Session.add(s)
        Session.commit()
        redirect_to('substitutions')

    @ActionProtector(not_anonymous())
    def new(self, format='html'):
        """GET /substitutions/new: Form to create a new item"""
        # url('new_substitution')
        c.date = self._closest_working_day(datetime.date.today())
        c.groups = Session.query(Group).join(Group.year).\
                order_by(desc(SchoolYear.start), Group.name).all()
        c.educators = Session.query(Educator).\
                order_by(Educator.last_name).all()
        c.year = SchoolYear.current()
        return render('substitutions/new.xml')

    @ActionProtector(not_anonymous())
    def update(self, id):
        """PUT /substitutions/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('substitution', id=ID),
        #           method='put')
        # url('substitution', id=ID)

    @ActionProtector(not_anonymous())
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

    @ActionProtector(not_anonymous())
    def edit(self, id, format='html'):
        """GET /substitutions/id/edit: Form to edit an existing item"""
        # url('edit_substitution', id=ID)
