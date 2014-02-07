#!/bin/bash
#
# Copyright 2014 Philipp Winter <phw@nymity.ch>

# The amount of (unspoofed) TCP SYNs used to estimate the destination's backlog
# size.
control_syns=5

# The amount of spoofed TCP SYNs which are sent to fill the destination's SYN
# backlog more than 50%.
spoofed_syns=150

# How long we should wait for SYN/ACKs after sending data.  60 is a reasonable
# value given 5 SYN/ACK retransmissions and exponential backoff in between
# segments.
timeout=60

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

echo "[+] Beginning RST probing at: $(date -u --rfc-3339=ns)."
echo "[+] Setting iptables rules to ignore RST segments."
iptables -A OUTPUT -d ${dst_addr} -p tcp --tcp-flags RST RST -j DROP

echo "[+] Invoking tcpdump(8) to capture network data."
tcpdump -i any -n "host ${dst_addr} and portrange 10000-10005" -w "${outfile}" &
pid=$!
sleep 1

echo "[+] Sending ${control_syns} control TCP SYN segments to ${dst_addr}:${port}."
hping3-custom -n -c $control_syns -i u15000 -q -S -s 10000 -p ${port} ${dst_addr}

# 15,000 usec means ~66.7 SYNs a second.
echo "[+] Sending ${spoofed_syns} spoofed TCP SYN segments to ${spoofed_addr}."
hping3-custom -n -c $spoofed_syns -a $spoofed_addr -i u15000 -q -S -s 20000 -p ${port} ${dst_addr}

echo "[+] Done transmitting but waiting ${timeout}s for final SYN/ACKs to arrive."
sleep "$timeout"

echo "[+] Removing iptables rule."
iptables -D OUTPUT -d ${dst_addr} -p tcp --tcp-flags RST RST -j DROP

echo "[+] Terminating tcpdump."
if [ ! -z "$pid" ]
then
	kill "$pid"
	echo "[+] Sent SIGTERM to tcpdump's PID ${pid}."
fi

echo "[+] Experimental results written to: ${outfile}"
