
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Django 1.2 and less
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = ':memory:'
# Django 1.3 and above
DATABASES = {
    'default': {
        'NAME': DATABASE_NAME,
        'ENGINE': 'django.db.backends.sqlite3',
    },
}

INSTALLED_APPS = ( 'batch_select', )


TESTING_BATCH_SELECT=True

# enable this for coverage (using django test coverage 
# http://pypi.python.org/pypi/django-test-coverage )
#TEST_RUNNER = 'django-test-coverage.runner.run_tests'
#COVERAGE_MODULES = ('batch_select.models', 'batch_select.replay')