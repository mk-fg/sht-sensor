# -*- coding: utf-8 -*-
from __future__ import print_function

import itertools as it, operator as op, functools as ft
from os.path import join, exists
import os, sys, logging, glob, time, select


class OnDemandLogger(object):
	log = None
	def __getattr__(self, k):
		if not self.log: self.log = logging.getLogger('bbb_gpio')
		return getattr(self.log, k)
log = OnDemandLogger()


path_gpio = '/sys/class/gpio'

class GPIOAccessFailure(Exception): pass

def gpio_access_wrap(func, checks=12, timeout=1.0):
	for n in xrange(checks, -1, -1):
		try: return func()
		except (IOError, OSError): pass
		if checks <= 0: break
		if n: time.sleep(timeout / checks)
	else:
		raise GPIOAccessFailure(func, timeout)
		# log.warn('gpio access failed (func: %s, timeout: %s)', func, timeout)

def get_pin_path(n, sub=None, _cache=dict()):
	n = int(n)
	if n not in _cache:
		for try_export in [True, False]:
			try:
				path = join(path_gpio, 'gpio{}'.format(n))
				if not exists(path): path, = glob.glob(path + '_*')
			except:
				if not try_export:
					raise OSError('Failed to find sysfs control path for pin: {}'.format(n))
			else: break
			log.debug('Exporting pin: %s', n)
			with open(join(path_gpio, 'export'), 'wb', 0) as dst:
				gpio_access_wrap(ft.partial(dst.write, bytes(n)))
		_cache[n] = path
	else: path = _cache[n]
	return path if not sub else os.path.join(path, sub)

def get_pin_value(n, k='value'):
	with gpio_access_wrap(
			ft.partial(open, get_pin_path(n, k), 'rb', 0) ) as src:
		val = src.read().strip()
	if k == 'value':
		try: val = int(val)
		except ValueError as err:
			log.warn('Failed to read/decode pin (n: %s) value %r: %s', n, val, err)
			val = None
	return val

def set_pin_value(n, v, k='value', force=False, _pin_state=dict()):
	if k == 'value' and isinstance(v, bool): v = int(v)
	if not force and _pin_state.get(n) == v: return
	if _pin_state.get(n) == v: return
	# log.debug('Setting parameter of pin-%s: %s = %r ', n, k, v)
	with gpio_access_wrap(
			ft.partial(open, get_pin_path(n, k), 'wb', 0) ) as dst:
		gpio_access_wrap(ft.partial(dst.write, bytes(v)))
	_pin_state[n] = v


class PollTimeout(Exception): pass

def poll_pin(n, timeout=1.0, edge='both', _poller_cache=dict()):
	if edge: set_pin_value(n, k='edge', v=edge)
	try:
		if n not in _poller_cache:
			_poller_cache[n] = select.poll()
		poller = _poller_cache[n]
		with gpio_access_wrap(
				ft.partial(open, get_pin_path(n, 'value'), 'rb', 0) ) as src:
			poller.register(src.fileno(), select.POLLPRI | select.POLLERR)
			res = poller.poll(timeout * 1000)
			if not res or res[0][1] & select.POLLERR == select.POLLERR:
				raise PollTimeout(n, timeout, edge, res)
		return get_pin_value(n)
	finally:
		if edge: set_pin_value(n, k='edge', v='none')
