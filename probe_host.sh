#!/bin/bash
#
# Copyright 2014 Philipp Winter <phw@nymity.ch>
#
# Probes a given host using traceroutes, SYN scans and RST scans.  All data is
# written to the given directory.  Probing should happen in sync with the
# censored machine behind the GFW.

source log.sh

PATH=$PATH:"."

traceroute="traceroute_host.sh"
synscan="synscan.sh"
rstscan="rstscan.sh"
#spoofed_addr="1.93.36.159"
spoofed_addr="130.243.26.55"

if [ "$#" -ne 3 ]
then
	echo
	echo "Usage: $0 DST_ADDR DST_PORT OUTPUT_DIR"
	echo
	exit 1
fi

ip_addr="$1"
port="$2"
outdir="$3"

log "0. Now probing host ${ip_addr}:${port}."

log "1. Running TCP and ICMP-based traceroutes to ${ip_addr}:${port}."
"$traceroute" "$ip_addr" "$port" "$outdir" &

sleep 5

log "2. Running SYN scan to determine if SYN or SYN/ACK segments are dropped."
"$synscan" "$ip_addr" "$port" "${outdir}/$(date -u +'%F.%T')_synscan.pcap" &

log "3. Running TCP and ICMP-based traceroutes to ${ip_addr}:${port}."
"$traceroute" "$ip_addr" "$port" "$outdir" &

sleep 5

log "4. Running RST scan to determine if RST segments are dropped."
"$rstscan" "$ip_addr" "$port" "$spoofed_addr" "${outdir}/$(date -u +'%F.%T')_rstscan.pcap" &

log "5. Running TCP and ICMP-based traceroutes to ${ip_addr}${port}."
"$traceroute" "$ip_addr" "$port" "$outdir"

sleep 10
