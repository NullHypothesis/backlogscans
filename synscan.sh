#!/bin/bash
#
# Copyright 2013, 2014 Philipp Winter <phw@nymity.ch>
#
# This script probes a remote TCP service by sending a specific amount of TCP
# SYN segments and capturing the replies it gets.  Note that it requires a
# modified version of hping3(8) as the tool has a global counter which is
# incremented with outgoing *and* incoming packets whereas we are only
# interested in outgoing packets.

source log.sh
source config.sh

# The amount of TCP SYNs used to estimate the destination's backlog size.
if [ $prober_type = "censored" ]
then
	control_syns=145
else
	control_syns=10
fi

# How long we should wait for SYN/ACKs after sending data.  65 is a reasonable
# value given 5 SYN/ACK retransmissions and exponential backoff in between
# segments.  After 65 seconds, our SYNs should no longer be in the destinations
# backlog.
timeout=65

if [ "$#" -lt 2 ]
then
	echo
	echo "Usage: $0 DST_ADDRESS DST_PORT [OUTPUT_FILE]"
	echo
	exit 1
fi

dst_addr="$1"
port="$2"

if [ ! -z "$3" ]
then
	outfile="$3"
else
	outfile="$(mktemp '/tmp/synscan-XXXXXX.pcap')"
fi

log "Beginning SYN probing."
log "Setting iptables rules to ignore RST segments."
iptables -A OUTPUT -d ${dst_addr} -p tcp --tcp-flags RST RST -j DROP

log "Invoking tcpdump(8) to capture network data."
tcpdump -i any -n "host ${dst_addr} and port ${port}" -w "${outfile}" &
pid=$!

# Give tcpdump some time to start.
sleep 2

# 15,000 usec means ~66.7 SYNs a second.
log "Sending ${control_syns} TCP SYN segments to ${dst_addr}:${port} in the background."
timeout 5 hping3-custom -n -c "$control_syns" -i u13000 -q -S -s 10000 -p ${port} ${dst_addr} &

log "Now waiting ${timeout}s for final SYN/ACKs to arrive."
sleep "$timeout"

log "Removing iptables rule."
iptables -D OUTPUT -d ${dst_addr} -p tcp --tcp-flags RST RST -j DROP

log "Terminating tcpdump."
if [ ! -z "$pid" ]
then
	kill "$pid"
	log "Sent SIGTERM to PID ${pid}."
fi

log "Experimental results written to: ${outfile}"
