"""Setuptools setup file for the SIS project."""
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

version = __import__('sis').__version__

setup(
    name='SIS',
    version=version,
    description='',
    author='Jakub Warmuz',
    author_email='jakub.warmuz@gmail.com',
    url='http://sis.staszic.edu.pl',
    install_requires=[
        "Routes >= 1.12.3",
        "Pylons >= 1.0",
        "SQLAlchemy >= 0.6.3",
        "Genshi >= 0.6",
        "repoze.who <= 1.99",
        "repoze.what-quickstart >= 1.0.6",
        "repoze.what-pylons >= 1.0",
        "repoze.who.plugins.formcookie >= 0.3.0",
        "reportlab >= 2.4",
    ],
    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    data_files = [('resources', ['resources/Ubuntu-R.ttf', 'resources/Ubuntu-B.ttf'])],
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'sis': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors={'sis': [
    #        ('**.py', 'python', None),
    #        ('public/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['PasteScript', 'Pylons'],
    entry_points="""
    [paste.app_factory]
    main = sis.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
