#!/bin/bash
#
# Start the script as follows:
# $ sudo ./ipid_prober.sh IP_ADDRESS_LIST
#
# The script expects one IP address per line in the given input file.  It does
# not know how to deal with CIDR notation.  Use another tool to convert CIDR
# notation to IP addresses first.

if [ "$#" -ne 1 ]
then
	echo
	echo "Usage: $0 IP_ADDRESS_FILE"
	echo
	exit 1
fi

# Change this to your needs.
spoofed_addr="1.2.3.4"

probe_real() {
	local ip_addr="$1"

	hping3 -n -s 20000 -p 80 -S -c 1 "$ip_addr" | \
		grep 'id=' | \
		sed 's/.*id=\([^ ]\+\).*/\1/'
}

probe_spoof() {
	local ip_addr="$1"

	hping3 -a "$spoofed_addr" -n -s 20000 -p 80 -S -c 1 "$ip_addr" | \
		grep 'id=' | \
		sed 's/.*id=\([^ ]\+\).*/\1/'
}

while read ip_addr
do

	echo -n "Probing ${ip_addr}: "

	(
		probe_real "$ip_addr"
		probe_spoof "$ip_addr"
		probe_real "$ip_addr"
		probe_spoof "$ip_addr"
		probe_real "$ip_addr"
	) 2>/dev/null | ./analyse_sequence

done < "$1"
