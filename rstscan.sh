#!/bin/bash
#
# Copyright 2014 Philipp Winter <phw@nymity.ch>

source log.sh
source config.sh

# The amount of (unspoofed) TCP SYNs used to estimate the destination's backlog
# size.
control_syns=5

# The amount of spoofed TCP SYNs which are sent to fill the destination's SYN
# backlog more than 50%.
spoofed_syns=150

# How long we should wait for SYN/ACKs after sending data.  65 is a reasonable
# value given 5 SYN/ACK retransmissions and exponential backoff in between
# segments.  After 65 seconds, our SYNs should no longer be in the destinations
# backlog.
timeout=65

# This experiment can be run by the uncensored machine without assistance of
# the censored machine.  For synchronisation, we use sleep calls instead.
if [ $prober_type = "censored" ]
then
	sleep "$timeout"
	sleep 2
	exit 0
fi

if [ "$#" -lt 3 ]
then
	echo
	echo "Usage: $0 DST_ADDRESS DST_PORT SPOOFED_ADDRESS [OUTPUT_FILE]"
	echo
	exit 1
fi

dst_addr="$1"
port="$2"
spoofed_addr="$3"

if [ ! -z "$4" ]
then
	outfile="$4"
else
	outfile="$(mktemp '/tmp/rstscan-XXXXXX.pcap')"
fi

log "Beginning RST probing."
log "Setting iptables rules to ignore RST segments."
iptables -A OUTPUT -d "${dst_addr}" -p tcp --tcp-flags RST RST -j DROP

log "Invoking tcpdump(8) to capture network data."
tcpdump -i any -n "host ${dst_addr} and portrange 20000-20005" -w "${outfile}" &
pid=$!

# Give tcpdump some time to start.
sleep 2

log "Sending ${control_syns} control TCP SYN segments to ${dst_addr}:${port}."
timeout 5 hping3-custom -n -c $control_syns -i u15000 -q -S -L 0 -s 20000 -p ${port} ${dst_addr} &

# 15,000 usec means ~66.7 SYNs a second.
log "Sending ${spoofed_syns} spoofed TCP SYN segments to ${spoofed_addr}."
timeout 5 hping3-custom -n -c $spoofed_syns -a $spoofed_addr -i u15000 -q -S -L 0 -s 30000 -p ${port} ${dst_addr} &

log "Done transmitting but waiting ${timeout}s for final SYN/ACKs to arrive."
sleep "$timeout"

log "Removing iptables rule."
iptables -D OUTPUT -d ${dst_addr} -p tcp --tcp-flags RST RST -j DROP

log "Terminating tcpdump."
if [ ! -z "$pid" ]
then
	kill "$pid"
	log "Sent SIGTERM to tcpdump's PID ${pid}."
fi

log "Experimental results written to: ${outfile}"
