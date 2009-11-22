
DEBUG = True
TEMPLATE_DEBUG = DEBUG
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = ':memory:'
INSTALLED_APPS = ( 'batch_select', )

TESTING_BATCH_SELECT=True

# enable this for coverage
TEST_RUNNER = 'django-test-coverage.runner.run_tests'
COVERAGE_MODULES = ('batch_select.models', )