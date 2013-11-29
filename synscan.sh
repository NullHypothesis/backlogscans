#!/bin/bash
#
# Copyright 2013 by Philipp Winter <phw@nymity.ch>
#
# This script probes a remote TCP service by sending a specific amount of TCP
# SYN segments and capturing the replies it gets.  Note that it might require a
# modified version of hping3(1) as the tool has a global counter which is
# incremented with outgoing *and* incoming packets whereas we are only
# interested in outgoing packets.

# The amount of TCP SYNs which should be sent to the target.
limit=200

# How long we should wait for SYN/ACKs after sending data.
timeout=60

if [ "$#" -lt 2 ]
then
	echo
	echo "Usage: $0 <ip_address> <port>"
	echo
	exit 1
fi

ipaddress="$1"
port="$2"

output="$(mktemp '/tmp/synscan-XXXXXX.pcap')"

echo "[+] Starting probing at: $(date)."
echo "[+] Setting iptables rules to ignore RST segments."
iptables -A OUTPUT -d ${ipaddress} -p tcp --tcp-flags RST RST -j DROP

echo "[+] Starting tcpdump to capture network data."
tcpdump -n "host ${ipaddress}" -w "${output}" &
pid=$!
sleep 1

echo "[+] Sending ${limit} TCP SYN segments to ${ipaddress}:${port}."
hping3 -n -c $limit --fast -q -S -s 10000 -p ${port} ${ipaddress}

echo "[+] Finished but waiting ${timeout}s for final SYN/ACKs to arrive."
sleep "$timeout"

echo "[+] Removing iptables rule."
iptables -D OUTPUT -d ${ipaddress} -p tcp --tcp-flags RST RST -j DROP

echo "[+] Terminating tcpdump."
if [ ! -z "$pid" ]
then
	kill "$pid"
	echo "[+] Sent SIGTERM to PID ${pid}."
fi

echo "[+] Experimental results written to ${output}."
