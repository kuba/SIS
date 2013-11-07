===============================
School Information System (SIS)
===============================

Created back in 2009 for Stanisław Staszic 4th High School in Sosnowiec,
School Information System (SIS) is the system consisting of a database
for various school data (e.g. class schedules) and tools for managing,
retrieval and processing of this data.


Installation and Setup
======================

Install ``SIS`` using easy_install::

    easy_install SIS

Make a config file as follows::

    paster make-config SIS sis.ini

Tweak the config file as appropriate and then setup the application::

    paster setup-app sis.ini

Then you are ready to go.
