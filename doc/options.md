Command line options
--------------------

usage: fml [-h] [-c CONFIG_FILE] [--clobber] [-d] [--errors] [--debug]
           [--dump-config] [-f OUTPUT_FORMAT] [--info] [-i INTERVAL]
           [--list-fml] [--log-file LOG_FILE] [--kill-fml]
           [--output-file OUTPUT_FILE] [-r] [-R] [-D SERIAL_DEVICE]
           [--serial-baud SERIAL_BAUD] [--serial-bytesize SERIAL_BYTESIZE]
           [--serial-parity SERIAL_PARITY] [--serial-stopbits SERIAL_STOPBITS]
           [--serial-timeout SERIAL_TIMEOUT] [-t TIMES] [-v]

Fast Modbus Logging Daemon

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        specify the path to the config file
  --clobber             try to run even if there is already an fml process
                        running (kill it first), also create new RRD database
                        when the slave config has changed
  -d, --daemon          run in daemon mode (detach, log to syslog, output to
                        file)
  --errors              set debugging level to errors only
  --debug               write debugging output in the log
  --dump-config         print fml configuratio and exit
  -f OUTPUT_FORMAT, --formats OUTPUT_FORMAT
                        write in specified format (gnostic, csv, pretty)
  --info                write informational output in the log
  -i INTERVAL, --interval INTERVAL
                        how many seconds between fetching data from slaves
  --list-fml            show a list of fml processes which are running
  --log-file LOG_FILE   send logging to this file instead of stderr (has no
                        effect when in daemon mode)
  --kill-fml            kill any running instances of fml
  --output-file OUTPUT_FILE
                        write output to specified file
  -r, --raw             suppress post-processing - just write data as it comes
                        from the slaves
  -R, --rrd-disable     suppress rrd recording of data
  -D SERIAL_DEVICE, --serial-device SERIAL_DEVICE
                        specify serial device node to connect with, e.g.
                        /dev/ttyS0
  --serial-baud SERIAL_BAUD
                        specify baud rate for serial communications
  --serial-bytesize SERIAL_BYTESIZE
                        specify bytesize for serial communications
  --serial-parity SERIAL_PARITY
                        specify parity for serial communications (none, mark,
                        even, or odd)
  --serial-stopbits SERIAL_STOPBITS
                        specify number of stop bits for serial communications
  --serial-timeout SERIAL_TIMEOUT
                        how long to wait for a modbus reply
  -t TIMES, --times TIMES
                        fetch from slaves a specified number of times and then
                        exit
  -v, --verbose         be more verbose (dump command)

