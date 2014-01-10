#!/bin/bash
#
# Copyright 2013, 2014 Philipp Winter <phw@nymity.ch>

if [ "$#" -lt 1 ]
then
	echo
	echo "Usage: $0 RELAY_LIST [OUTPUT_DIR]"
	echo
	echo "The file \"RELAY_LIST\" must contain one IP:port tuple on every line."
	echo
	exit 1
fi

relaylist="$1"
# Check if optional argument is given.
if [ ! -z "$2" ]
then
	outdir="$2"
	if [ ! -d $outdir ]
	then
		echo "[+] Creating directory \"${outdir}\"."
		mkdir $outdir
	fi
else
	outdir="$(mktemp -d '/tmp/traceroutes-XXXXXX')"
fi
count=1
all=$(wc -l $relaylist)
all=(${all// / })
all=${all[0]}

timestamp() {
	local file="$1"
	echo "Date in UTC: $(date -u --rfc-3339=ns)" >> $file
}

for relay in $(cat $relaylist)
do
	# Parse the input which is in the format of IP:port.
	tuple=(${relay//:/ })
	ip=${tuple[0]}
	port=${tuple[1]}
	filebase="${outdir}/${ip}:${port}"

	echo "[+] Beginning traceroutes ${count} of ${all} to ${ip}:${port}."
	count=$((${count} + 1))

	echo "[+] Running TCP traceroutes to ${ip}:${port} in the background."
	timestamp "${filebase}_tcp"
	traceroute -T -A -O ack -n -p $port $ip >> "${filebase}_tcp" 2>&1 &

	echo "[+] Running ICMP traceroutes to ${ip}:${port} in the background."
	timestamp "${filebase}_icmp"
	traceroute -I -A -n $ip >> "${filebase}_icmp" 2>&1 &

	echo "[+] Writing results to \"${filebase}_{tcp,icmp}\"."
done
