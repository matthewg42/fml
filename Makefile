# Make the installation tarball
version = "0.4"
tarball = fml-$(version).tar.gz

dist : Makefile install.sh mb_crc.py mb_formatter.py mb_master.py mb_register.py mb_rrd.py mb_slave.py pp_functions.py pretty_format.py fml fml.conf setup.py init.d/fml www/default-mini-httpd www/fml_update_graphs.sh www/index.html www/mini-httpd.conf www/cgi-bin/data_files
	rm -f $(tarball)
	tar --show-transformed-names --transform s%^%fml-$(version)/% -cvzf $(tarball) $?

clean :
	rm -rf build *.pyc

