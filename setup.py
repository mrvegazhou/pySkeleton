# -*- coding: utf-8 -*-
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name="***",
    version="0.1",
    install_requires=[
                        "futures","pygal","Crypto","python-memcached","redis","MySQL-python","ez_setup","Crypto"
                      ],
    packages=find_packages(),
    author="vega",
    author_email="mrvegazhou@gmail.com",
    url="",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    description="",
)
