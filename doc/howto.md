FML HOWTO
=========

How to download
---------------

Clone the git repo https://github.com/matthewg42/fml.git

i.e. use the command
    $ git clone https://github.com/matthewg42/fml.git

How to: make installer tarball from github repo
-----------------------------------------------

Change into the fml root directory and run make.  i.e.

    $ cd fml
    $ make

A file named fml-{version}.tar.gz should be generated. This contains 
everthing needed to install FML on a raspberry pi with a fresh Raspian
installation.

How to: use an installer tarball
--------------------------------

Synopsis: copy the tarball to a raspberry pi running Raspian, untar it, 
change into the directory it creates and run the install.sh with root 
permissions:

    $ untar zxf fml-1.0.tar.gz
    $ cd fml-1.0
    $ sudo ./install.sh

How to: check if FML is running
-------------------------------

Run this command:

    $ fml --list

This will list any FML processes which are running, or print a message
saying no FML processes could be found.

How to: start & stop FML service
--------------------------------

The installer creates an init script for fml, which may be used to start
and stop the fml as a service, and check if the service has been started:

    $ sudo /etc/init.d/fml start
    $ sudo /etc/init.d/fml status
    $ sudo /etc/init.d/fml stop

How to: edit the configuration file
-----------------------------------

The configuration file is "/etc/fml.conf". Use your favourite editor 
(e.g. nano, vim) to edit this file. The file is formatted in "ini" style.

### Change serial port settings

The following options can be set in the "[master]" section of the 
configuration file: serial_device (e.g. /dev/ttyUSB0), serial_baud,
serial_bytesize, serial_parity (none, odd, even), serial_stopbits,
serial_timeout

### Change how frequently FML polls slave devices

Change the value of "interval" in the "[master]" section of the config
file.

### Add a new modbus slave

First create a new section in the config file where the section name is 
"[slave_{ID}]".

For each register create a key / value pair in the new section with 
the key set to "r{register-id}_name" and the value being some short
description of the contents of the register.

#### Example

Slave ID (numerical modbus address): 240, has two temperature sensors
with register IDs 4 and 7. The raw values from these registers is to
be used, so no post-processing function is needed.  Create the following
section in the config file:

    [slave_240]
    r4_name = Temp1
    r7_name = Temp1

#### Note
Any change to the slave configuration will result in the re-creation
of the RRD database, destroying historical data.

### Adding a register with a post-processing function

Assuming an appropriate post-processing function is already implemented,
it may be called by adding a new key in the slave section of the config 
file named "r{register-id}_pp_fn". The value for this key is the name 
of the post-processing function to be used.

Some post-processing functions require additional per-register 
parameters. These may be specified using a key named 
"r{register-id}_pp_param" with parameters passed as a comma separated list 
of values.

#### Example

To specify the post-processing function "thermister_to_celcius" for 
register 0 with parameters 4126, 298.15, 10000, the register should defined 
in the appropriate slave section of the config file as follows:

    r0_name = Temp1
    r0_pp_fn = thermister_to_celcius
    r0_pp_param = 4126,298.15,10000

How to: add a graph to the web server
-------------------------------------

Updating what the web server shows is still pretty manual. Future 
development may make this easier. For now you have to do the following:

1. Edit /usr/local/bin/fml_update_graphs.sh to generate new graphs using rrdtool.
2. Edit /var/lib/fml/www/index.html to add the graph to the web page.


