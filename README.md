sht-sensor
--------------------

Python driver and command-line tool for Sensirion SHT1x and SHT7x sensors
connected to GPIO pins.

Pure-python module only requires /sys/class/gpio interface, provided by the
Linux kernel and should work on any device that has it (including RPi,
Beaglebone boards, Cubieboard, etc).

Its main purpose is reading temperature (in degrees Celsius) and humidity (%RH)
values from these devices, checking CRC8 checksums for received data to make
sure it was not corrupted in transfer.

SHT1x (SHT10, SHT11, SHT15) and SHT7x (SHT71, SHT75) are fairly popular and
accurate capacitive/band-gap relative humidity and temperature sensor IC's, with
digital output via custom 2-wire serial interface.

SHT1x differs from SHT7x in packaging, with SHT1x being surface-mountable one
and latter having pluggable FR4 package.

Sensors include additional functionality available via the status register (like
VDD level check, enabling internal heating element, resolution, OTP reload, etc)
which may or may not also be implemented here, see "Stuff that is not
implemented" section at the end.


Usage
--------------------

Module can be imported from the python code or used via included command-line
tool, which should be installed along with the module (or can be used via ./sht
symlink in the repo root without installation).
See "Installation" section below on how to install the module.

GPIO numbers (to which SCK and DATA sensor pins are connected) must be specified
either on command-line (for cli tool) or on class init (when using as a python
module).

Example, for SCK connected to gpio 21 and DATA to gpio 17:

	% sht -v -trd 21 17
	temperature: 25.07
	rh: 26.502119362
	dew_point: 4.4847911176

GPIO "pin" numbers here (and in python module) use whichever numbering scheme
kernel has in /sys/class/gpio, which is likely be totally different from the
actual (physical) pin numbers on the board headers, and can potentially change
between board revisions (e.g. RPi rev 1.0 -> 2.0) or even kernel updates, so be
sure to check up-to-date docs on these.

For both the tool and module, also be sure to check/specify correct voltage
(default is '3.5V', value is from the datasheet table, not free-form!) that the
sensor's VDD pin is connected to:

	% sht --voltage=5V --temperature 21 17
	25.08

This voltage value is used to pick coefficient (as presented in datasheet table)
for temperature calculation, and incorrect setting here should result in less
precise output values (these values add/subtract 0.1th of degree, while sensor's
typical precision is +/- 0.4 degree, so mostly irrelevant).

If you're using non-SHT1x/SHT7x, but a similar sensor (e.g. some later model),
it might be a good idea to look at the Sht class in the code and make sure all
coefficients (taken from
[SHT7x datasheet](https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/Humidity_Sensors/Sensirion_Humidity_Sensors_SHT7x_Datasheet_V5.pdf))
there match your model's datasheet exactly.

See `sht --help` output for the full list of options for command-line tool.

Example usage from python code:

	from sht_sensor import Sht
	sht = Sht(21, 17)
	print 'Temperature', sht.read_t()
	print 'Relative Humidity', sht.read_rh()

Voltage value (see note on it above) on sensor's VDD pin can be specified for
calculations exactly as it is presented in datasheet table (either as a string
or ShtVDDLevel enum value), if it's not module-default '3.5V', for example:
`sht = Sht(21, 17, voltage=ShtVDDLevel.vdd_5v)`.

It might be preferrable to use `ShtVDDLevel.vdd_5v` value over simple '5V'
string as it should catch typos and similar bugs in cases, but makes no
difference otherwise.

Some calculations (e.g. for RH) use other sensor-provided values, so it's
possible to pass these to the corresponding read_* methods, to avoid heating-up
sensor with unnecessary extra measurements:

	t = sht.read_t()
	rh = sht.read_rh(t)
	dew_point = sht.read_dew_point(t, rh)

If included `sht_sensor.gpio` module (accessing /sys/class/gpio directly) should
not be used (e.g. on non-linux or with different gpio interface), its interface
("get_pin_value" and "set_pin_value" attrs/functions) can be re-implemented and
passed as a "gpio" keyword argument on Sht class init.

ShtComms class is an implementation of 2-wire protocol that sensor uses and
probably should not be used directly.
All the coefficients, calculations and such high-level logic is defined in Sht
class, extending ShtComms.

Installed python module can also be used from cli via the usual `python -m
sht_sensor ...` convention.


Installation
--------------------

It's a regular package for Python 2.7 (not 3.X).

Using [pip](http://pip-installer.org/) is the best way:

	% pip install sht-sensor

If you don't have it, use:

	% easy_install pip
	% pip install sht-sensor

Alternatively (see also
[pip2014.com](http://pip2014.com/) and
[install guide](http://www.pip-installer.org/en/latest/installing.html)):

	% curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python
	% pip install sht-sensor

Or, if you absolutely must:

	% easy_install sht-sensor

But, you really shouldn't do that.

Current-git version can be installed like this:

	% pip install 'git+https://github.com/mk-fg/sht-sensor.git#egg=sht-sensor'

Note that to install stuff in system-wide PATH and site-packages, elevated
privileges are often required.
Use "install --user",
[~/.pydistutils.cfg](http://docs.python.org/install/index.html#distutils-configuration-files)
or [virtualenv](http://pypi.python.org/pypi/virtualenv) to do unprivileged
installs into custom paths.

Alternatively, `./sht` tool can be run right from the checkout tree without any
installation, if that's the only thing you need there.


Stuff that is not implemented
--------------------

* Everything related to the Status Register.

	In particular, commands like VDD level check, enabling internal heating
	element, resolution, OTP reload, etc.

* Temerature measurements in degrees Fahrenheit.

	These just use different calculation coefficients, which can be overidden in
	the Sht class.
	Or degrees-Celsius value can easily be converted to F after the fact.

	Metric system is used here, so I just had no need for these.

* Lower-resolution measurements.

	Sensor supports returning these after changing the value in the Status
	Register, so interface to that one should probably be implemented/tested
	first.

* Skipping CRC8 checksum validation.

	Code is there, as ShtComms._skip_crc() method, but no idea why it might be
	preferrable to skip this check.

* Changing SCK clock rate.

	Might be desirable for slower boards or more electric-noisy environments.


Links
--------------------

Other drivers for these sensors that I know of and might be more suitable for
some particular case:

* [rpiSht1x](https://pypi.python.org/pypi/rpiSht1x) (python package)

	Uses RaspberryPi-specific RPi.GPIO module.

	As of 2015-01-12, did not check CRC8 checksums for received data,
	used hard-coded 5V temperature conversion coefficients,
	returned invalid values even if ack's were incorrect,
	looked more like proof-of-concept overall.

* [Pi-Sht1x](https://github.com/drohm/pi-sht1x/) (python package)

	Python-3.x module based on rpiSht1x, also uses RPi.GPIO, and rather similar to
	this one, but with more extensive functionality - has most/all stuff from "not
	implemented" list above, addresses all of the rpiSht1x shortcomings.

	Probably wouldn't have bothered writing this module if it was around at the time.

* sht1x module in [Linux kernel](https://www.kernel.org/)

	Looks very mature and feature-complete, probably used a lot for various
	platforms' hardware monitoring drivers.

	Seem to be only for internal use (i.e. from other kernel modules) at the
	moment (3.17.x), but should be possible (and easy) to add Device Tree hooks
	there, which would allow to specify how it is connected (gpio pins) via Device
	Tree.

* [SHT1x module for Arduino](https://github.com/practicalarduino/SHT1x)

	C++ code, rpiSht1x above is based on this one.
