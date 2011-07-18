#!/usr/bin/env python
from setuptools import setup, find_packages
import sys, os
setup(name='CalibrationCam',
      version='0.1',
      description='Camera Calibration Tool',
      author='Patrice Ferlet',
      author_email='metal3d@gmail.com',
      packages=['calibration'],
      package_dir={'calibration': 'src/calibration'},
      license='BSD',
      requires = ['cv','PyQt4'], 
      scripts = ['src/camcalib']
      )
