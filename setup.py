# coding=utf-8
# author=UlionTse

import re
import pathlib
import setuptools


NAME = 'exejs'
PACKAGE = 'exejs'
AUTHOR = 'UlionTse'
AUTHOR_EMAIL = 'uliontse@outlook.com'
HOMEPAGE_URL = 'https://github.com/uliontse/exejs'
DESCRIPTION = 'Run JavaScript code from Python.'
LONG_DESCRIPTION = pathlib.Path('README.md').read_text(encoding='utf-8')
VERSION = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', pathlib.Path('exejs/__init__.py').read_text(), re.M).group(1)


setuptools.setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license='Apache-2.0',
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_dir={'exejs': 'exejs'},
    url=HOMEPAGE_URL,
    project_urls={
        'Source': 'https://github.com/UlionTse/exejs',
        'Changelog': 'https://github.com/UlionTse/exejs/blob/main/change_log.txt',
        'Documentation': 'https://github.com/UlionTse/exejs/blob/main/README.md',
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: JavaScript',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords=['JavaScript',],
    install_requires=[],
    python_requires='>=3.8',
    extras_require={'pypi': ['build>=1.2.2', 'twine>=6.1.0', 'setuptools>=75.3.0']},
    zip_safe=False,
)

