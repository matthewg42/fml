# Make the installation tarball
version = "0.1"
tarball = fml-$(version).tar.gz

dist : Makefile install.sh mb_crc.py mb_formatter.py mb_master.py mb_register.py mb_rrd.py mb_slave.py pp_functions.py pretty_format.py fml fml.conf setup.py init.d/fml
	rm -f $(tarball)
	tar --show-transformed-names --transform s%^%fml-$(version)/% -cvzf $(tarball) $?

clean :
	rm -rf build *.pyc

