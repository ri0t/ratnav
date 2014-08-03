#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os

from setuptools import setup

try:
    import cv
except ImportError:
    print("You must install python-opencv! Try \
    sudo apt-get install python-opencv python-numpy \
    """)

def include_readme():
    readme = open("README.rst")
    include = readme.readlines(10)[2:10]
    readme.close()
    return "".join(include)


def is_package(path):
    return (
        os.path.isdir(path) and
        os.path.isfile(os.path.join(path, '__init__.py'))
    )


def find_packages(path, base=""):
    """ Find all packages in path """
    packages = {}
    for item in os.listdir(path):
        dir = os.path.join(path, item)
        if is_package(dir):
            if base:
                module_name = "%(base)s.%(item)s" % vars()
            else:
                module_name = item
            packages[module_name] = dir
            packages.update(find_packages(dir, module_name))
    return packages


packages = find_packages(".")
package_names = packages.keys()

setup(name="trafficam",
      version="1.0.0",
      description="trafficam",

      author="Hackerfleet Community",
      author_email="packages@hackerfleet.org",
      url="https://github.com/ri0t/trafficam",
      license="GNU General Public License v3",
      packages=package_names,
      package_dir=packages,
      scripts=[
          'scripts/trafficam',
      ],
      data_files=[
          ('/etc/init.d', ["etc/init.d/trafficam"]),
          ('/etc/trafficam', ["etc/trafficam/config.json"])
      ],

      long_description=include_readme(),
      dependency_links=[],

      # These versions are not strictly checked, older ones may or may not work.
      install_requires=[''
      ]

)
