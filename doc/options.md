Configuration and command line settings
=======================================

[i] means the option affects interactive mode
[d] means the option affects daemon mode
[e] means the option causes some effect and exits
[id] means the option affects both modes

Command line only settings
--------------------------

- --help [e]
- --config-file=<path> [id]
- --daemon [selects i / d]
- --log-file=<path> [id]
- --dump-config [e]
- --kill [id]
- --list-procs [e]
- --times [id]

Config file only settings
-------------------------

- Slave setup [id]

Config file settings which command-line over-rides
--------------------------------------------------

- output_file / --output-file [id]
- output_format / --format [id]
- log_level / --debug / --quiet [id]
- interval / --interval [id]
- serial_device / --serial-device [id]
- serial_baud / --serial-baud [id]
- serial_bytesize / --serial-bytesize [id]
- serial_parity / --serial-parity [id]
- serial_stopbits / --serial-stopbits [id]

