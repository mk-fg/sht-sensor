#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import itertools as it, operator as op, functools as ft
import os, sys, logging, time, math

try: import sht_sensor
except ImportError:
	# Make sure tool works from a checkout
	if __name__ != '__main__': raise
	from os.path import dirname, exists, isdir, join, abspath
	pkg_root = abspath(dirname(__file__))
	for pkg_root in pkg_root, dirname(pkg_root):
		if isdir(join(pkg_root, 'sht_sensor'))\
				and exists(join(pkg_root, 'setup.py')):
			sys.path.insert(0, dirname(__file__))
			try: import sht_sensor
			except ImportError: pass
			else: break
	else: raise ImportError('Failed to find/import "sht_sensor" module')


class ShtFailure(Exception): pass
class ShtCommFailure(ShtFailure): pass
class ShtCRCCheckError(ShtFailure): pass

class ShtComms(object):

	def _crc8(self, cmd, v0, v1, _crc_table=[
			0x00, 0x31, 0x62, 0x53, 0xc4, 0xf5, 0xa6, 0x97, 0xb9, 0x88, 0xdb, 0xea,
			0x7d, 0x4c, 0x1f, 0x2e, 0x43, 0x72, 0x21, 0x10, 0x87, 0xb6, 0xe5, 0xd4,
			0xfa, 0xcb, 0x98, 0xa9, 0x3e, 0x0f, 0x5c, 0x6d, 0x86, 0xb7, 0xe4, 0xd5,
			0x42, 0x73, 0x20, 0x11, 0x3f, 0x0e, 0x5d, 0x6c, 0xfb, 0xca, 0x99, 0xa8,
			0xc5, 0xf4, 0xa7, 0x96, 0x01, 0x30, 0x63, 0x52, 0x7c, 0x4d, 0x1e, 0x2f,
			0xb8, 0x89, 0xda, 0xeb, 0x3d, 0x0c, 0x5f, 0x6e, 0xf9, 0xc8, 0x9b, 0xaa,
			0x84, 0xb5, 0xe6, 0xd7, 0x40, 0x71, 0x22, 0x13, 0x7e, 0x4f, 0x1c, 0x2d,
			0xba, 0x8b, 0xd8, 0xe9, 0xc7, 0xf6, 0xa5, 0x94, 0x03, 0x32, 0x61, 0x50,
			0xbb, 0x8a, 0xd9, 0xe8, 0x7f, 0x4e, 0x1d, 0x2c, 0x02, 0x33, 0x60, 0x51,
			0xc6, 0xf7, 0xa4, 0x95, 0xf8, 0xc9, 0x9a, 0xab, 0x3c, 0x0d, 0x5e, 0x6f,
			0x41, 0x70, 0x23, 0x12, 0x85, 0xb4, 0xe7, 0xd6, 0x7a, 0x4b, 0x18, 0x29,
			0xbe, 0x8f, 0xdc, 0xed, 0xc3, 0xf2, 0xa1, 0x90, 0x07, 0x36, 0x65, 0x54,
			0x39, 0x08, 0x5b, 0x6a, 0xfd, 0xcc, 0x9f, 0xae, 0x80, 0xb1, 0xe2, 0xd3,
			0x44, 0x75, 0x26, 0x17, 0xfc, 0xcd, 0x9e, 0xaf, 0x38, 0x09, 0x5a, 0x6b,
			0x45, 0x74, 0x27, 0x16, 0x81, 0xb0, 0xe3, 0xd2, 0xbf, 0x8e, 0xdd, 0xec,
			0x7b, 0x4a, 0x19, 0x28, 0x06, 0x37, 0x64, 0x55, 0xc2, 0xf3, 0xa0, 0x91,
			0x47, 0x76, 0x25, 0x14, 0x83, 0xb2, 0xe1, 0xd0, 0xfe, 0xcf, 0x9c, 0xad,
			0x3a, 0x0b, 0x58, 0x69, 0x04, 0x35, 0x66, 0x57, 0xc0, 0xf1, 0xa2, 0x93,
			0xbd, 0x8c, 0xdf, 0xee, 0x79, 0x48, 0x1b, 0x2a, 0xc1, 0xf0, 0xa3, 0x92,
			0x05, 0x34, 0x67, 0x56, 0x78, 0x49, 0x1a, 0x2b, 0xbc, 0x8d, 0xde, 0xef,
			0x82, 0xb3, 0xe0, 0xd1, 0x46, 0x77, 0x24, 0x15, 0x3b, 0x0a, 0x59, 0x68,
			0xff, 0xce, 0x9d, 0xac ]):
		# See: http://www.sensirion.com/nc/en/products/\
		#  humidity-temperature/download-center/?cid=884&did=124&sechash=5c5f91f6
		crc = _crc_table[cmd]
		crc = _crc_table[crc ^ v0]
		crc = _crc_table[crc ^ v1]
		# Reverse bit order
		# See: http://graphics.stanford.edu/~seander/bithacks.html#ReverseByteWith64BitsDiv
		return (crc * 0x0202020202 & 0x010884422010) % 1023

	def __init__(self, pin_sck, pin_data, gpio=None):
		if gpio is None:
			from sht_sensor import gpio
		self.pin_sck, self.pin_data, self.gpio = pin_sck, pin_data, gpio
		self.log = logging.getLogger('Sht')
		self._init()

	def _init(self):
		for pin in self.pin_sck, self.pin_data:
			# self.gpio.set_pin_value(pin, k='edge', v='none')
			self.gpio.set_pin_value(pin, k='direction', v='low')
		self.pin_data_mode = 'out'
	_cleanup = _init


	def _data_mode(self, mode):
		if self.pin_data_mode != mode:
			self.gpio.set_pin_value(self.pin_data, k='direction', v=mode)
			self.pin_data_mode = mode

	def _data_set(self, v):
		self._data_mode('out')
		self.gpio.set_pin_value(self.pin_data, v, force=True)

	def _data_get(self):
		self._data_mode('in')
		return self.gpio.get_pin_value(self.pin_data)

	def _sck_tick(self, v):
		self.gpio.set_pin_value(self.pin_sck, v)
		time.sleep(0.0000001) # 100ns, not sure if actually makes a difference


	def _send(self, cmd):
		tick, data = self._sck_tick, self._data_set

		tick(0)
		data(1)
		tick(1)
		data(0)
		tick(0)
		tick(1)
		data(1)

		tick(0)
		for n in xrange(8):
			data(cmd & (1 << 7 - n))
			tick(1)
			tick(0)

		tick(1)
		if self._data_get():
			raise ShtCommFailure('Command ACK failed on step-1')
		tick(0)
		if not self._data_get():
			raise ShtCommFailure('Command ACK failed on step-2')

	def _wait(self, timeout=1.0, poll_interval=0.01):
		self._data_mode('in')
		## Proper edge-poll seem to always return POLLERR on BBB
		## Also seem unreliable in general case, and not super-necessary here
		# ack = self.gpio.poll_pin(self.pin_data, edge='falling')
		for i in xrange(int(timeout / poll_interval) + 1):
			time.sleep(poll_interval)
			ack = self.gpio.get_pin_value(self.pin_data)
			if not ack: break
		else:
			raise ShtCommFailure('Measurement timeout: {:.2f}s'.format(timeout))

	def _read_bits(self, bits, v=0):
		tick = self._sck_tick
		self._data_mode('in')
		for n in xrange(bits):
			tick(1)
			v = v * 2 + self._data_get()
			tick(0)
		return v

	def _read_meas_16bit(self):
		# Most significant bits (upper nibble is always zeroes)
		v0 = self._read_bits(8)
		# Send ack
		tick, data = self._sck_tick, self._data_set
		data(1)
		data(0)
		tick(1)
		tick(0)
		# Least significant bits
		v1 = self._read_bits(8)
		return v0, v1

	def _get_meas_result(self, cmd):
		self._send(cmd)
		self._wait()
		v0, v1 = self._read_meas_16bit()
		# self._skip_crc()
		crc0, crc1 = self._crc8(cmd, v0, v1), self._read_crc()
		if crc0 != crc1: raise ShtCRCCheckError(crc0, crc1)
		return v0 * 256 | v1

	def _read_crc(self):
		self._data_set(1)
		self._data_set(0)
		self._sck_tick(1)
		self._sck_tick(0)
		return self._read_bits(8)

	def _skip_crc(self):
		self._data_set(1)
		self._sck_tick(1)
		self._sck_tick(0)

	def _conn_reset(self):
		self._data_set(1)
		for n in xrange(10):
			self._sck_tick(1)
			self._sck_tick(0)


class Sht(ShtComms):
	# All table/chapter refs here point to:
	#  Sensirion_Humidity_SHT7x_Datasheet_V5.pdf

	voltage_default = '3.5V'

	class c:
		d1 = { # Table 8, C
			'5V': -40.1,
			'4V': -39.8,
			'3.5V': -39.7,
			'3V': -39.6,
			'2.5V': -39.4 }
		d2 = 0.01 # Table 8, C/14b
		c1, c2, c3 = -2.0468, 0.0367, -1.5955e-6 # Table 6, 12b
		t1, t2 = 0.01, 0.00008 # Table 7, 12b
		tn = dict(water=243.12, ice=272.62) # Table 9
		m = dict(water=17.62, ice=22.46) # Table 9

	class cmd:
		t = 0b00000011
		rh = 0b00000101

	def __init__(self, pin_sck, pin_data, voltage=None, **sht_comms_kws):
		'''"voltage" setting is important,
					as it influences temperature conversion coefficients!!!
			Unless you're using SHT1x/SHT7x, please make
				sure all coefficients match your sensor's datasheet.'''
		self.voltage = voltage or self.voltage_default
		assert self.voltage in self.c.d1, [self.voltage, self.c.d1.keys()]
		super(Sht, self).__init__(pin_sck, pin_data, **sht_comms_kws)

	def read_t(self):
		t_raw = self._get_meas_result(self.cmd.t)
		return t_raw * self.c.d2 + self.c.d1[self.voltage]

	def read_rh(self, t=None):
		if t is None: t = self.read_t()
		return self._read_rh(t)

	def _read_rh(self, t):
		rh_raw = self._get_meas_result(self.cmd.rh)
		self._cleanup()
		rh_linear = self.c.c1 + self.c.c2 * rh_raw + self.c.c3 * rh_raw**2 # ch 4.1
		return (t - 25.0) * (self.c.t1 + self.c.t2 * rh_raw) + rh_linear # ch 4.2

	def read_dew_point(self, t=None, rh=None):
		'With t and rh provided, does not access the hardware.'
		if t is None: t, rh = self.read_t(), None
		if rh is None: rh = self.read_rh(t)
		t_range = 'water' if t >= 0 else 'ice'
		tn, m = self.c.tn[t_range], self.c.m[t_range]
		return ( # ch 4.4
			tn * (math.log(rh / 100.0) + (m * t) / (tn + t))
			/ (m - math.log(rh / 100.0) - m * t / (tn + t)) )


def main(args=None):
	import argparse
	parser = argparse.ArgumentParser(description='Read data from SHTxx-type sensor.')
	parser.add_argument('pin_sck', type=int,
		help='Number of SCK pin, specified using kernel sysfs numbering scheme.')
	parser.add_argument('pin_data', type=int,
		help='Number of DATA pin, specified using kernel sysfs numbering scheme.')

	parser.add_argument('--voltage', default='3.5V', metavar='label_from_table',
		help='Voltage value (exactly as presented'
			' in datasheet table) that is used. Default: %(default)s')

	parser.add_argument('-t', '--temperature', action='store_true',
		help='Print temperature value to stdout. Default if no other values were specified.')
	parser.add_argument('-r', '--rel-humidity',
		action='store_true', help='Print RH value to stdout.')
	parser.add_argument('-d', '--dew-point',
		action='store_true', help='Print "dew point" value to stdout.')

	parser.add_argument('-v', '--verbose', action='store_true', help='Print labels before values.')
	parser.add_argument('--debug', action='store_true', help='Verbose operation mode.')
	opts = parser.parse_args(sys.argv[1:] if args is None else args)

	logging.basicConfig(level=logging.DEBUG if opts.debug else logging.WARNING)
	if not (opts.temperature or opts.rel_humidity or opts.dew_point): opts.temperature = True

	sht = Sht(opts.pin_sck, opts.pin_data)

	p = '{name}: {val}' if opts.verbose else '{val}'
	p = lambda name, val, fmt=p: print(fmt.format(name=name, val=val))
	t = rh = dp = None
	if opts.temperature: t = sht.read_t()
	if opts.rel_humidity: rh = sht.read_rh(t)
	if opts.dew_point: dp = sht.read_dew_point(t, rh)

	for name, v in zip(['temperature', 'rh', 'dew_point'], [t, rh, dp]):
		if v is not None: p(name, v)


if __name__ == '__main__': sys.exit(main())
