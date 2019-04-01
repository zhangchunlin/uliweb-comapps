#coding=utf8
__doc__ = """uliweb-comapps"""

import re
import os
import sys

from setuptools import setup, find_packages

def fpath(name):
    return os.path.join(os.path.dirname(__file__), name)


def read(fname, default=''):
    filename = fpath(fname)
    if os.path.exists(filename):
        return open(fpath(fname)).read()
    else:
        return default


def desc():
    info = read('README.md', __doc__)
    return info + '\n\n' + read('doc/CHANGELOG.md')

file_text = read(fpath('uliweb_comapps/__init__.py'))


def grep(attrname):
    pattern = r"{0}\s*=\s*'([^']*)'".format(attrname)
    strval, = re.findall(pattern, file_text)
    return strval

if sys.version_info[0] == 2:
    uliweb_mname = "uliweb"
else:
    uliweb_mname = "uliweb3"

setup(
    name='uliweb-comapps',
    version=grep('__version__'),
    url=grep('__url__'),
    license='BSD',
    author=grep('__author__'),
    author_email=grep('__email__'),
    description='uliweb-comapps',
    long_description=desc(),
    packages = find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        uliweb_mname,
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)