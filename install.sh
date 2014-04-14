#!/bin/bash

main () {
    check_root
    check_net
    disable_serial_console
    add_pi_to_dialout_group
    set_serial_perms
    install_deps
    install_libs
    install_daemon
    update_motd
    create_lib_dir
    install_httpd
}

erex () {
    l=${1:-1}
    shift
    echo "$@" 1>&2
    exit $l
}

check_root () {
    echo "checking we're running as root... "
    [ $(id -u) = "0" ] || erex 2 "ERROR: must run as root / with sudo"
}

check_net () {
    echo "checking we're running as root... "
    # see if we can see google.  It's a fair test...
    ping -c 1 google.com > /dev/null || erex 2 "ERROR: no Internet connection"
}

disable_serial_console () {
    echo "Disabling serial console... "
    # comment out the serial console line in inittab
    sed -i '/^T.*-L ttyAMA0/ s/^/#/' /etc/inittab
    # make init apply changes
    init q
}

add_pi_to_dialout_group () {
    echo "adding to to fml and dialout groups... "
    groupadd fml
    usermod -aG dialout pi
    usermod -aG fml pi
}

set_serial_perms () {
    echo "Setting serial dev node permissions... "
    chown root:dialout /dev/ttyAMA0
    chmod 770 /dev/ttyAMA0
}

install_deps () {
    echo "Installing dependencies using apt-get (may take a little while)... "
    apt-get -qq -y install screen vim python-serial python-daemon python-rrdtool rrdtool mini-httpd bc || erex 3 "ERROR: failed to install packages"
}

install_libs () {
    echo "Installing python libs... "
    python setup.py install || erex 4 "ERROR: failed to install fml program or module"
}

install_daemon () {
    # copy installation files to target directories
    echo "Installing daemon... "
    install -m 755 fml /usr/local/bin/ && 
    install -m 644 fml.conf /etc
    install -m 755 init.d/fml /etc/init.d/ && 
    for d in /etc/rc2.d /etc/rc3.d /etc/rc4.d /etc/rc5.d; do
        cd "$d"
        ln -s ../init.d/fml S02fml
        cd -
    done
}

update_motd () {
    echo "Updating /etc/motd..."
    cat > /etc/motd <<EOD

             ---===>>> RPi Data Logger <<<===---

Useful files:
 - Config file...     /etc/fml.conf
 - Data files...      /var/lib/fml/
 - Logging goes to... /var/log/syslog

Useful commands:
 - Check daemon status...   sudo /etc/init.d/fml status
 - Start fml daemon...      sudo /etc/init.d/fml start
 - Stop fml daemon...       sudo /etc/init.d/fml stop
 - Restart fml darmon...    sudo /etc/init.d/fml restart
 - Check slave config...    fml --dump

             ---===>>>    Mouse  <3    <<<===---

EOD
    chmod 644 /etc/motd
}

create_lib_dir () {
    echo "Creating /var/lib/fml..."
    mkdir -p /var/lib/fml/www/cgi-bin
    chown root:fml fml /var/lib/fml /var/lib/fml/www /var/lib/fml/www/cgi-bin
    chmod 775 /var/lib/fml /var/lib/fml/www /var/lib/fml/www/cgi-bin
}

install_httpd () {
    echo "Installing httpd settings..."
    install -m 644 www/index.html /var/lib/fml/www/ &&
    install -m 755 www/cgi-bin/status /var/lib/fml/www/cgi-bin/ &&
    install -m 755 www/cgi-bin/data_files /var/lib/fml/www/cgi-bin/ &&
    install -m 755 www/fml_update_graphs.sh /usr/local/bin/ && 
    install -m 644 www/mini-httpd.conf /etc/ && 
    install -m 644 www/default-mini-httpd /etc/default/mini-httpd && 
    tmp=$(mktemp)
    su pi -c "crontab -l | grep -v '^ *$'" > "$tmp"
    echo '* * * * * nice /usr/local/bin/fml_update_graphs.sh' >> "$tmp"
    chmod 644 "$tmp" 
    su pi -c "crontab $tmp"
    rm -f "$tmp"
    echo "crontab command to update graphs has been added to pi user, but is commented - use 'crontab -e' to edit"
    /etc/init.d/mini-httpd restart
}

main "$@"


