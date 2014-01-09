Configuration and command line settings
=======================================

[i] means the option affects interactive mode
[d] means the option affects daemon mode
[e] means the option causes some effect and exits
[id] means the option affects both modes

Command line only settings
--------------------------

- --help [e]
- --daemon [selects i / d]
- --log-file=<path> [id]
- --show-config [e]
- --kill [e]
- --list-procs [e]
- --times [id]

Config file only settings
-------------------------

- Slave setup [id]

Config file settings which command-line over-rides
--------------------------------------------------

- output_file / --output-file [u,d]
- output_format / --format [u,d]
- log_level / --debug / --quiet [u,d]
- interval / --interval [u,d]
- serial_device / --serial-device [u,d]
- serial_baud / --serial-baud [u,d]
- serial_bytesize / --serial-bytesize [u,d]
- serial_parity / --serial-parity [u,d]
- serial_stopbits / --serial-stopbits [u,d]

