sht-sensor
==========

Python driver and command-line tool for Sensirion SHT1x and SHT7x sensors
connected to GPIO pins.


.. contents::
  :backlinks: none



Description
-----------

This is a pure-python module that only requires /sys/class/gpio interface,
provided by the Linux kernel and should work on any device that has it
(including RPi, Beaglebone boards, Cubieboard, etc - any linux).

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
-----

Module can be imported from the python code or used via included command-line
tool, which should be installed along with the module (or can be used via ./sht
symlink in the repo root without installation).

See "Installation" section below on how to install the module.

GPIO numbers (to which SCK and DATA sensor pins are connected) must be specified
either on command-line (for cli tool) or on class init (when using as a python
module).

Example, for SCK connected to gpio 21 and DATA to gpio 17::

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
sensor's VDD pin is connected to::

  % sht --voltage=5V --temperature 21 17
  25.08

This voltage value is used to pick coefficient (as presented in datasheet table)
for temperature calculation, and incorrect setting here should result in less
precise output values (these values add/subtract 0.1th of degree, while sensor's
typical precision is +/- 0.4 degree, so mostly irrelevant).

If you're using non-SHT1x/SHT7x, but a similar sensor (e.g. some later model),
it might be a good idea to look at the Sht class in the code and make sure all
coefficients (taken from SHT1x/SHT7x datasheet - google it, sensirion.com URL
for it changed like 4 times in 2y) there match your model's datasheet exactly.

See `sht --help` output for the full list of options for command-line tool.

Example usage from python code::

  from sht_sensor import Sht
  sht = Sht(21, 17)
  print 'Temperature', sht.read_t()
  print 'Relative Humidity', sht.read_rh()

Voltage value (see note on it above) on sensor's VDD pin can be specified for
calculations exactly as it is presented in datasheet table (either as a string
or ShtVDDLevel enum value), if it's not module-default '3.5V', for example:
``sht = Sht(21, 17, voltage=ShtVDDLevel.vdd_5v)``.

It might be preferrable to use ``ShtVDDLevel.vdd_5v`` value over simple '5V'
string as it should catch typos and similar bugs in some cases, but makes no
difference otherwise.

Some calculations (e.g. for RH) use other sensor-provided values, so it's
possible to pass these to the corresponding read_* methods, to avoid heating-up
sensor with unnecessary extra measurements::

  t = sht.read_t()
  rh = sht.read_rh(t)
  dew_point = sht.read_dew_point(t, rh)

If included ``sht_sensor.gpio`` module (accessing /sys/class/gpio directly)
should not be used (e.g. on non-linux or with different gpio interface), its
interface ("get_pin_value" and "set_pin_value" attrs/functions) can be
re-implemented and passed as a "gpio" keyword argument on Sht class init.

ShtComms class is an implementation of 2-wire protocol that sensor uses and
probably should not be used directly.
All the coefficients, calculations and such high-level logic is defined in Sht
class, extending ShtComms.

Installed python module can also be used from cli via the usual ``python -m
sht_sensor ...`` convention.



Installation
------------

It's a regular package for Python 2.7 (not 3.X).

If you have Python-3.x on linux as default "python" command (run ``python
--version`` to check), be sure to use python2/pip2 and such below.

Using pip_ is the best way::

  % pip install sht-sensor

(add --user option to install into $HOME for current user only)

Or, if you don't have "pip" command::

  % python -m ensurepip
  % python -m pip install --upgrade pip
  % python -m pip install sht-sensor

On a very old systems, **one of** these might work::

  % easy_install pip
  % pip install sht-sensor

  % curl https://bootstrap.pypa.io/get-pip.py | python
  % pip install sht-sensor

  % easy_install sht-sensor

  % git clone --depth=1 https://github.com/mk-fg/sht-sensor
  % cd sht-sensor
  % python setup.py install

Current-git version can be installed like this::

  % pip install 'git+https://github.com/mk-fg/sht-sensor.git#egg=sht-sensor'

Note that to install stuff to system-wide PATH and site-packages (without
--user), elevated privileges (i.e. root and su/sudo) are often required.

Use "...install --user", `~/.pydistutils.cfg`_ or virtualenv_ to do unprivileged
installs into custom paths.

More info on python packaging can be found at `packaging.python.org`_.

Alternatively, ``./sht`` tool can be run right from the checkout tree without
any installation, if that's the only thing you need there.

.. _pip: http://pip-installer.org/
.. _~/.pydistutils.cfg: http://docs.python.org/install/index.html#distutils-configuration-files
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _packaging.python.org: https://packaging.python.org/installing/




Misc features / quirks
----------------------

Description of minor things that might be useful in some less common cases.


ShtCommFailure: Command ACK failed on step-1
````````````````````````````````````````````

Very common error indicating that there's no response from the sensor at all.

Basically, command gets sent on a wire and at the very first step where there
should be response (acknowledgement) from the sensor, there is none.

This would happen if specified pins are not connected to anything for example,
which is the most likely issue here - probably worth double-checking
GPIO-line/pin numbering scheme (usually GPIO numbers are NOT the same as
physical pin numbers, and their wiring may vary between board revisions) and
whether `controlling specified pins via /sys/class/gpio`_ can be measured -
e.g. lights up the LED connected to the pin/gnd or shows up on the multimeter
display.

For example, to control voltage on GPIO line number 17 (again, note that it can
be connected to any physical pin number, check device docs)::

  # cd /sys/class/gpio
  # echo 17 > export
  # echo high > gpio17/direction
  # echo low > gpio17/direction

Another simple thing to check is whether used sensor package needs a pull-up
resistor, and whether that is connected properly.

Might also be some issue with the sensor of course, but that should be extremely
unlikely compared to aforementioned trivial issues.

.. _controlling specified pins via /sys/class/gpio: https://www.kernel.org/doc/Documentation/gpio/sysfs.txt


Max bit-banging frequency control
`````````````````````````````````

Max frequency value Can be passed either on command-line with --max-freq or when
creating an Sht instance, with separate values for SCK and DATA pins, if necessary.

Sensor can work just fine with very low frequencies like 20Hz -
e.g. ``sht --max-freq 20 -trv 30 60`` - though that'd obviously slow things down a bit.

Separate SCK:DATA frequencies (in that order): ``sht --max-freq 100:200 -trv 30 60``

Same from python module: ``sht = Sht(21, 17, freq_sck=100, freq_data=200)``



Stuff that is not implemented
-----------------------------

- Everything related to the Status Register.

  In particular, commands like VDD level check, enabling internal heating
  element, resolution, OTP reload, etc.

- Temerature measurements in degrees Fahrenheit.

  These just use different calculation coefficients, which can be overidden in
  the Sht class.
  Or degrees-Celsius value can easily be converted to F after the fact.

  Metric system is used here, so I just had no need for these.

- Lower-resolution measurements.

  Sensor supports returning these after changing the value in the Status
  Register, so interface to that one should probably be implemented/tested
  first.

- Skipping CRC8 checksum validation.

  Code is there, as ShtComms._skip_crc() method, but no idea why it might be
  preferrable to skip this check.



Links
-----

Other drivers for these sensors that I know of and might be more suitable for
some particular case:

* `rpiSht1x <https://pypi.python.org/pypi/rpiSht1x>`_ (python package)

  Uses RaspberryPi-specific RPi.GPIO module.

  As of 2015-01-12, did not check CRC8 checksums for received data,
  used hard-coded 5V temperature conversion coefficients,
  returned invalid values even if ack's were incorrect,
  looked more like proof-of-concept overall.

* `Pi-Sht1x <https://github.com/drohm/pi-sht1x/>`_ (python package)

  Python-3.x module based on rpiSht1x, also uses RPi.GPIO, and rather similar to
  this one, but with more extensive functionality - has most/all stuff from "not
  implemented" list above, addresses all of the rpiSht1x shortcomings.

  Probably wouldn't have bothered writing this module if it was around at the time.

* sht1x module in `Linux kernel <https://www.kernel.org/>`_

  Looks very mature and feature-complete, probably used a lot for various
  platforms' hardware monitoring drivers.

  Seem to be only for internal use (i.e. from other kernel modules) at the
  moment (3.17.x), but should be possible (and easy) to add Device Tree hooks
  there, which would allow to specify how it is connected (gpio pins) via Device
  Tree.

* `SHT1x module for Arduino <https://github.com/practicalarduino/SHT1x>`_

  C++ code, rpiSht1x above is based on this one.
