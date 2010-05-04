try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='School',
    version='0.1',
    description='',
    author='Jakub Warmuz',
    author_email='jakub.warmuz@gmail.com',
    url='',
    install_requires=[
        "Routes >= 1.11",
        "Pylons >= 0.9.7",
        "SQLAlchemy >= 0.5",
        "Genshi >= 0.4",
        "repoze.who <= 1.99",
        "repoze.what-quickstart >= 1.0.6",
        "repoze.what-pylons >= 1.0",
        "repoze.who.plugins.formcookie >= 0.3.0"
    ],
    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'school': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors={'school': [
    #        ('**.py', 'python', None),
    #        ('public/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['PasteScript', 'Pylons'],
    entry_points="""
    [paste.app_factory]
    main = school.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
