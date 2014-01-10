#!/bin/bash
#
# Copyright 2014 Philipp Winter <phw@nymity.ch>

PATH=$PATH:.

# Path to the relays file which contains IP:port tuples.
relays="relays.txt"
# Path to the SYN scanning script.
script="synscan.sh"
# Directory where .pcap files are written to.
outputdir="data"

if [ ! -f "$relays" ]
then
	echo "File \"${relays}\" does not exist." >&2
	exit 1
fi

if [ ! -f "$script" ]
then
	echo "Script \"${script}\" does not exist." >&2
	exit 1
fi

if [ ! -d "$outputdir" ]
then
	mkdir -p "$outputdir"
	if [ $? != 0 ]
	then
		echo "Could not create directory \"${outputdir}\"." >&2
		exit 1
	fi
fi

relay=$(head -1 "$relays")
if [ -z "$relay" ]
then
	# Apparently, we drained the entire file.
	echo "[+] No more data in file \"${relays}\"."
	exit 0
else
	# Run a scan.
	array=(${relay//:/ })
	ip=${array[0]}
	port=${array[1]}
	echo "[+] Running SYN scan for \"${ip}:${port}\" at $(date -u --rfc-3339=ns)."
	"$script" "$ip" "$port" "${outputdir}/${relay}_$(date -u '+%F_%T').pcap"

	# Drain the first relay and write back the remaining relays.
	echo "[+] Draining first relay from file \"${relays}\"."
	tmpfile=$(mktemp '/tmp/relay_list-XXXXXXXXXX')
	tail -n +2 "$relays" > "$tmpfile"
	mv "$tmpfile" "$relays"
fi
