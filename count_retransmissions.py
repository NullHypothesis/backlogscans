#!/usr/bin/env python
#
# Copyright 2013, 2014 by Philipp Winter <phw@nymity.ch>
#
# Reads the given .pcap file and determines the subsequent SYN/ACK
# retransmissions after a SYN segment was sent to a service.

import sys

from scapy.all import *
from scapy.utils import rdpcap

class Connection( object ):

    """
    Represents a TCP connection attempt.
    """

    def __init__( self, syn):
        self.syn = syn
        self.syn_acks = []

    def add_syn_ack( self, syn_ack ):
        self.syn_acks.append(syn_ack)

    def get_isn( self ):
        return self.syn[TCP].seq

def extract_connections( pkts ):
    """
    Iterate over .pcap and create Connection objects.
    """

    SYN = 2
    SYN_ACK = 18

    # Maps ISNs to Connection objects.
    connections = {}

    for pkt in pkts:

        flags = pkt[TCP].flags

        # Add a new SYN segment to our hash table.
        if flags == SYN:
            connections[pkt[TCP].seq] = Connection(pkt)

        # Add a SYN/ACK response to the respective SYN segment.
        elif flags == SYN_ACK:
            # If the key doesn't exist, the SYN/ACK is unsolicited.
            if connections.has_key(pkt[TCP].ack - 1):
                conn = connections[pkt[TCP].ack - 1]
                conn.add_syn_ack(pkt)

    return connections

def has_exponential_backoff( connection ):
    """
    Check if the given connection used exponential backoff for retransmissions.
    """

    backoff_model = ((0, 1.125), (1, 2.27), (3, 4.5), (7, 9), (15, 17), (31, 33))

    backoffs = []

    start_time = connection.syn.time

    good = True

    # Iterate over all SYN/ACKs inside a connection.
    for syn_ack in connection.syn_acks:

        time_diff = syn_ack.time - start_time
        backoffs.append(time_diff)

        fit = [upper <= time_diff <= lower for upper, lower in backoff_model]
        if not sum(fit):
            good = False

    if not good:
        print backoffs
        return False

    return True

def extract_retransmissions( connections ):

    start_time = None

    # Amount of SYN/ACK retransmissions when backlog is < 50% full.
    orig_retrans = []

    # Amount of SYN/ACK retransmissions when backlog is > 50% full.
    scan_retrans = []

    # Time between backlog scan and backlog size estimation.
    TIME_THRESHOLD = 1.5

    # Now sort the dictionary based on the timestamps.
    sorted_connections = sorted(connections.items(),
                                key = lambda pkt: pkt[1].syn.time)

    i = 1
    syns = synacks = max_synacks = 0

    # Extract SYN/ACK retransmissions for every connection.
    for (_, conn) in sorted_connections:

        # When was the first SYN sent?
        if start_time is None:
            start_time = conn.syn.time

        syn_ack_count = len(conn.syn_acks)
        if conn.syn.time > (start_time + TIME_THRESHOLD):
            orig_retrans.append(syn_ack_count)
        else:
            scan_retrans.append(syn_ack_count)

        print "[%.4f] SYN segment #%d received %d SYN/ACKs." % \
              (conn.syn.time, i, syn_ack_count)

        synacks += syn_ack_count
        if syn_ack_count == 6:
            max_synacks += 1

        syns += 1
        i += 1

    return (orig_retrans, scan_retrans)

def analyse_retransmissions( orig_retrans, scan_retrans ):
    """
    Print high-level scan statistics used to filter and analyse the data.
    """

    # Calculate average number of SYN/ACK retransmissions during backlog scan.
    syn_ack_mean = (0 if len(scan_retrans) == 0 \
                    else sum(scan_retrans) / float(len(scan_retrans)))
    print "On average, we received %.3f SYN/ACKs for every SYN." % syn_ack_mean

    # Machines whose original backlog is not as expected have to be dumped.
    if len(orig_retrans):
        print "Max original backlog: %d (%s)." % (max(orig_retrans),
                                                  orig_retrans)

    # Machine was probably offline.
    if syn_ack_mean == 0:
        verdict = "ERR"

    # 3.5 is our threshold.
    elif (syn_ack_mean < 3.5) and (3 in scan_retrans):
        verdict = "!RST" if "rst" in sys.argv[1] else "SYN"
    else:
        verdict = "RST" if "rst" in sys.argv[1] else "!SYN"

    print "Verdict: %s" % verdict
    print scan_retrans

def process_file( file_name ):

    connections = extract_connections(rdpcap(file_name))

    orig_retrans, scan_retrans = extract_retransmissions(connections)

    for connection in connections.values():
        if not has_exponential_backoff(connection):
            print "Connections don't follow exponential backoff."

    analyse_retransmissions(orig_retrans, scan_retrans)

    return 0

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print >> sys.stderr, "\nUsage: %s PCAP_FILE\n" % sys.argv[0]
        exit(1)

    exit(process_file(sys.argv[1]))
