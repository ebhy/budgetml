#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importlib.util
from codecs import open  # Use a consistent encoding.
from os import path
from pathlib import Path

from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Get the base version from the library.  (We'll find it in the `version.py`
# file in the src directory, but we'll bypass actually loading up the library.)
vspec = importlib.util.spec_from_file_location(
    "version",
    str(Path(__file__).resolve().parent /
        'budgetml' / 'constants.py')
)
vmod = importlib.util.module_from_spec(vspec)
vspec.loader.exec_module(vmod)
version = getattr(vmod, '__version__')

setup(
    name='budgetml',
    description="BudgetML: Deploy ML models on a budget.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests", "examples",
                 "docs"]),
    version=version,
    install_requires=[
        "google-api-python-client==1.12.8",
        "google-cloud-storage==1.35.0",
        "docker==4.4.1",
    ],
    python_requires=">=3.6, <3.9.0",
    license='Apache License 2.0',  # noqa
    author='ebhy Inc.',
    author_email='htahir111@gmail.com',
    url='https://github.com/ebhy/budgetml',
    keywords=[
        "deploy", "machine learning", "deep learning", "inference", "api"
    ],
    # See https://PyPI.python.org/PyPI?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for.
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',

        # Pick your license.  (It should match "license" above.)

        'License :: OSI Approved :: Apache Software License',  # noqa
        # noqa
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.6',
    ],

    data_files=[
        ('budgetml/template.Dockerfile', ['budgetml/template.Dockerfile']),
        ('budgetml/template-compose.yaml', ['budgetml/template-compose.yaml']),
        ('budgetml/template-nginx.conf', ['budgetml/template-nginx.conf'])],
    include_package_data=True
)
