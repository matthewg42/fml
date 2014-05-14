FML Software Components
=======================

Overview
--------

This document provides a list of what the installer program
does, where FML program and other files are installed and a
brief description of what each is for.

There are four categories detailed in this document:

1. Files for the FML program itself
2. Files for the init wrapper (automatic start/stop)
3. Web interface programs and files
4. Other changes the installer makes to the system config

FML program
-----------

The FML program is written in Python. The code is spit into an
actual binary (in the path, with executable permissions set):

    /usr/local/bin/fml

...and a group of modules in the Python library path:

    /usr/local/lib/python2.7/dist-packages/mb_rrd.py
    /usr/local/lib/python2.7/dist-packages/mb_crc.py
    /usr/local/lib/python2.7/dist-packages/mb_slave.py
    /usr/local/lib/python2.7/dist-packages/mb_formatter.py
    /usr/local/lib/python2.7/dist-packages/mb_master.py
    /usr/local/lib/python2.7/dist-packages/mb_register.py
    
The behaviour of fml is largely dictated by the configuration 
file, which is kept in /etc:

    /etc/fml.conf

By default, data is logged into files in this directory (although
this can be changed in the configuration file):

    /var/lib/fml/
    /var/lib/fml/20140514_171213.csv (example data file name)

Round robin data is written to a database here, created the first
time FML runs:

    /var/lib/fml/fml.rrd

To detect when configuration has changed in a manner which
requires a new RRD to be created, a signature file is also
written when FML runs for the first time:

    /var/lib/fml/fml.sig

When the RRD structure is changed, a new RRD file is created. The
old one gets renamed by appenting a tilde to the filename:

    /var/lib/fml/fml.rrd~

Should a backup already exist, tilde characters are appended
until an unused filename is found:

    /var/lib/fml/fml.rrd~~
    /var/lib/fml/fml.rrd~~~

Init daemon files
-----------------

In order to automatically execute FML on system startup, an
init wrapper script is installed in /etc/init.d, and symbolic
links to this script are made n various /etc/rc<level>.d 
directories:

    /etc/init.d/fml
    link from /etc/rc2.d/S20fml -> /etc/init.d/fml (auto-start daemon in runlevel 2)
    link from /etc/rc3.d/S20fml -> /etc/init.d/fml (auto-start daemon in runlevel 3)
    link from /etc/rc4.d/S20fml -> /etc/init.d/fml (auto-start daemon in runlevel 4)
    link from /etc/rc5.d/S20fml -> /etc/init.d/fml (auto-start daemon in runlevel 5)

Web interface programs and files
--------------------------------

The web interface is served by the mini-httpd package. The 
files it serves are kept in /var/lib/fml/www:

    /var/lib/fml/www/index.html
    /var/lib/fml/www/cgi-bin/data_files
    /var/lib/fml/www/cgi-bin/status

The program which updates the graphs for the web server (run once per
minute from cron). This program extracts data from the round robin 
database:

    /usr/local/bin/fml_update_graphs.sh

The graph files it generates:

    /var/lib/fml/www/temp_ten-minute.png
    /var/lib/fml/www/voltage_ten-minute.png
    /var/lib/fml/www/voltage_week.png
    /var/lib/fml/www/current_ten-minute.png
    /var/lib/fml/www/current_week.png
    /var/lib/fml/www/temp_week.png
    /var/lib/fml/www/errors.png

Configuration files for mini-httpd:

    /etc/mini-httpd.conf
    /etc/default/mini-httpd

Other things the installer does
-------------------------------

1. Disables serial console so that serial MODBUS devices can 
   talk to FML without logging messages causing probems. This
   is achieved by commenting out the line in /etc/inittab which
   refers to ttyAMA0.
2. Add "pi" user to "dialout" group, so it has permissions to 
   access serial ports.
3. Explicitly sets permissions on serial device /dev/ttyAMA0 
   to read & write for user and group, with owner set to root, 
   and group set to dialout.
4. Installs dependencies and a few useful packagaes: 
*screen
*vim
*python-serial
*python-daemon 
*python-rrdtool 
*rrdtool 
*mini-httpd 
*bc
5. Updates the /etc/motd (printed when a user does a console
   or ssh login), to give useful information about using FML.
6. Creates the directory for logging data into: /var/lib/fml
   and sets owner, group and permissions appropriately.
7. Adds a cron job for the pi user which calls fml_update_graphs.sh
   every minute to update the graphs for the web server

