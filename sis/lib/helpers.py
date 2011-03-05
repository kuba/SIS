"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password
import datetime

from pylons import url
from webhelpers.html.tags import *

from sis.lib.auth.helpers import signed_in
from sis.model.basic import Schedule

def schedule_last_update():
    current = Schedule.current()
    return current.updated
