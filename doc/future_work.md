Future Work
===========

At time of writing, FML is a proof-of-concept prototype.  It has not 
been rigourously tested, and some features are not complete. However,
it should be fairly usable for simple systems.  


Web Interface
-------------
The most notable weak point is the web interface. The script which 
generates graph images has to be manually edited to generate anything 
other than the default graphs.  Also, the generated pages would 
benefit from good CSS styling.


Better location for post-processing function definitions
--------------------------------------------------------

Currently, post-processing functions are defined in one of the modules
which is installed with fml in the python module path.  It might be
better to have a file in /etc/... somewhere for this.


Debian Package
--------------

The installer script is functional, but not really the 'right' way to 
install FML. A better approach would be to create a .deb package. This
would allow automatic un-installation, and use apt's dependency 
management.




