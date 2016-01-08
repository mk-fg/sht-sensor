#!/usr/bin/env python2
#-*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os, sys

# Error-handling here is to allow package to be built w/o README included
try:
	readme = open(os.path.join(
		os.path.dirname(__file__), 'README.txt' )).read()
except IOError: readme = ''

setup(

	name = 'sht-sensor',
	version = '16.1.0',
	author = 'Mike Kazantsev',
	author_email = 'mk.fraggod@gmail.com',
	license = 'WTFPL',
	keywords = [
		'sht', 'sensor', 'sensirion', 'ic',
		'sht1x', 'sht7x', 'sht10', 'sht11', 'sht15', 'sht71', 'sht75',
		'T', 'temperature', 'RH', 'relative', 'humidity', 'dew point', 'celsius',
		'environment', 'conditioning', 'measurement',
		'gpio', 'hardware', 'driver', 'serial', '2-wire', 'crc8' ],

	url = 'http://github.com/mk-fg/sht-sensor',

	description = 'Driver and command-line tool'
		' for Sensirion SHT1x and SHT7x sensors connected to GPIO pins.',
	long_description = readme,

	classifiers = [
		'Development Status :: 4 - Beta',
		'Environment :: Console',
		'Intended Audience :: Developers',
		'Intended Audience :: End Users/Desktop',
		'Intended Audience :: Manufacturing',
		'Intended Audience :: System Administrators',
		'License :: Public Domain',
		'Operating System :: POSIX :: Linux',
		'Programming Language :: Python',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 2 :: Only',
		'Topic :: Home Automation',
		'Topic :: Scientific/Engineering :: Atmospheric Science',
		'Topic :: System :: Hardware :: Hardware Drivers',
		'Topic :: System :: Monitoring',
		'Topic :: System :: Operating System Kernels :: Linux',
		'Topic :: Utilities' ],

	packages=find_packages(),
	include_package_data=True,
	package_data={'': ['README.txt']},
	exclude_package_data={'': ['README.*']},

	entry_points = {
		'console_scripts': ['sht = sht_sensor.sensor:main'] })
