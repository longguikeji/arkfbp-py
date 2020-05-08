#!/usr/bin/env python
import os
from setuptools import setup, find_packages

from arkfbp import __version__

f = open(os.path.join(os.path.dirname(__file__), 'README.md'))
long_description = f.read()
f.close()

setup(
    name='arkfbp',
    version=__version__,
    description='Python implementation of the arkfbp',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/longguikeji/arkfbp-py',
    author='Rock Lee',
    author_email='insfocus@gmail.com',
    maintainer='Rock Lee',
    maintainer_email='insfocus@gmail.com',
    keywords=['arkfbp'],
    license='MIT',
    packages=find_packages(),
    python_requires="!=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*",
    install_require=["requests"],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ]
)