from setuptools import setup, find_packages
 
setup(
    name='django-batch-select',
    version=__import__('batch_select').__version__,
    description='batch select many-to-many and one-to-many fields (to help avoid n+1 query problem)',
    long_description=open('README.rst').read(),
    author='John Montgomery',
    author_email='john@littlespikeyland.com',
    url='http://github.com/lilspikey/django-batch-select/',
    download_url='http://github.com/lilspikey/django-batch-select/downloads',
    license='BSD',
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)