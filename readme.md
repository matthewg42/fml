FML : Fast Modbus Logger
========================

FML acts as a modbus master, collects and logs data from one or more  
modbus slaves over a serial connection.  

Output formats
--------------

- File modes (data is appened to a file or sent to stdout)
    - CSV
    - Gnostic
    - Pretty-printed / tabular
- Database mode using rrd


Run modes
---------

FML can run as a daemon (a process which runs in the background, writing
output to files and logging to syslog), or in user/script mode - executed
from a login shell or called from a script to produce output which is
typically printed to a terminal or re-directed into a file.

Mode selection is done using the --daemon command line option - if this
option is used when FML is invoked, it will detach from the calling
terminal and run in the background.


Single instance
---------------

FML communicates with slave modbus modes using a serial interface.
Only one instace of FML should use a serial interface at a time to
prevent serial communications getting corrupted.  FML will check to
see if there are other instances running before it starts.  Using
the --clobber option will cause fml to kill off other instances 
as it starts (permissions permitting).


Configuration
-------------

Configuration is stored in the file `/etc/fml.conf`. Some settings
can also be set using command line options. Command line options take
precedence over settings in the configuration file.

Each modbus slave device which is connected using the serial interface
should have a `slave_<address>` section in the configuration file (where
`<address>` is the numerical ID of the slave device).  This section
defines the registers for that slave device. An example should make
it clearer:

`
[slave_1]
name = WeatherStation

r0_name = Temperature sensor
r1_name = Pressure sensor
r2_name = Humidity sensor
`
In this case, three registers are defined which return various bits
of data from a small weather station.  Data is expected to come back
as a 16 bit integer value.  It is possible to specify a funcion which
will post-process this value, and parameters to that function for the
specified register.  This makes it possible to have different calibrations
for different devices:

`
r0_name = Temperature sensor
r0_pp_func = post_process_temp
r0_pp_params = 1.076,2
`

Post processing functions must be defined in the program and registered
using `pp_functions.register()`.


Program flow summary
--------------------

1. Parse command-line arguments
2. Logging init
3. Special operations (kill / list / show config)
4. Create MBMaster
    1. load slaves / regs from config file
5. Run
    1. Output headers
    2. Loop
	1. Poll slaves
	2. Format and write output


Installer
---------

The install.sh script is designed to install and configure an FML instance
on a fresh Raspian-based Raspberry Pi (or other debian-based system). The
install.sh script uses apt-get to install dependencies, installs the 
startup scripts in /etc/init.d, /etc/rc.d, creates FML working directories
in /var/lib/fml, sets up the web server and adds a cron script to the pi 
user which updates the graphs for the web server.


Creating a tarball installer package
------------------------------------

Clone the guthub repository and run "make" from that directory. This will
generage a tarball named "fml-{version}.tar.gz". 


Installing using a tarball
--------------------------

Copy the tarball to the target raspian system, untar and run install.sh
with superuser permissions.  i.e.

`
mypi$ cd /tmp
mypi$ tar zxf fml-1.0.tar.gz
mypi$ cd fml-1.0
mypi$ sudo ./install.sh
`

Edit the /etc/fml.conf file according to your hardware and preferences,
then use this command to start fml:A

`
mypi$ sudo /etc/init.d/fml start
`


Future development
------------------

- One instance per serial interface?
- Other modbus data types.

