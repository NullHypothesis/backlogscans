#!/bin/bash
#
# Copyright 2014 Philipp Winter <phw@nymity.ch>
#
# This script is meant to be executed using watch(1), e.g.:
# $ watch -n 70 -p -x ./probing_wrapper.sh

source log.sh

PATH=$PATH:.

# Path to the script which probes a single host.
probe="probe_host.sh"

if [ "$#" -lt 2 ]
then
	echo
	echo "Usage: $0 HOSTS_FILE OUTPUT_DIR"
	echo
	exit 1
fi

hosts_file="$1"
outdir="$2"

if [ ! -f "$hosts_file" ]
then
	err "File \"${hosts_file}\" does not exist."
	exit 1
fi

if [ ! -d "$outdir" ]
then
	mkdir -p "$outdir"
	if [ $? != 0 ]
	then
		err "Could not create directory \"${outdir}\"."
		exit 1
	fi
fi

if [ ! -f "$probe" ]
then
	err "Script \"${probe}\" does not exist."
	exit 1
fi

host=$(head -1 "$hosts_file")
if [ -z "$host" ]
then
	err "No more hosts in file \"${hosts_file}\"."
else
	# Extract IP address and port from the IP:port tuple.
	array=(${host//:/ })
	ip_addr=${array[0]}
	port=${array[1]}

	# Probe the host.
	mkdir -p "${outdir}/${host}"
	"$probe" "${ip_addr}" "${port}" "${outdir}/${host}"

	# Drain the first relay and write back the remaining relays.
	log "Draining first relay from file \"${hosts_file}\"."
	tmpfile=$(mktemp '/tmp/relay_list-XXXXXXXXXX')
	tail -n +2 "$hosts_file" > "$tmpfile"
	mv "$tmpfile" "$hosts_file"
fi
