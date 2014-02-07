#!/bin/bash
#
# Copyright 2013, 2014 Philipp Winter <phw@nymity.ch>

source log.sh

if [ "$#" -lt 2 ]
then
	echo
	echo "Usage: $0 DST_ADDR DST_PORT [OUTPUT_DIR]"
	echo
	exit 1
fi

ip_addr="$1"
port="$2"

# Check if optional argument is given.
if [ ! -z "$3" ]
then
	outdir="$3"
	if [ ! -d $outdir ]
	then
		log "Creating directory \"${outdir}\"."
		mkdir -p $outdir
	fi
else
	outdir="$(mktemp -d '/tmp/traceroutes-XXXXXX')"
fi

timestamp() {
	local file="$1"
	printf "Date in UTC: $(date -u --rfc-3339=ns)\n" >> $file
}

# Parse the input which is in the format of IP:port.
filebase="${outdir}/$(date -u +'%F.%T')_traceroute"

log "Running TCP traceroute to ${ip_addr}:${port} in the background."
timestamp "${filebase}_tcp"
traceroute -T -A -O ack -n -w 3 -p $port $ip_addr >> "${filebase}_tcp" 2>&1 &

log "Running ICMP traceroute to ${ip_addr} in the background."
timestamp "${filebase}_icmp"
traceroute -I -A -n -w 3 $ip_addr >> "${filebase}_icmp" 2>&1 &

log "Writing results to \"${filebase}_{tcp,icmp}\"."
