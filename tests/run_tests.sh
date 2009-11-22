#!/bin/sh
# run from parent directory (e.g. tests/run_tests.sh)
django-admin.py test batch_select --pythonpath=. --settings=test_settings