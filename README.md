Overview
========

This repository contains a set of scripts which implement a number of TCP-based
network measurement tests.  These tests were written for a [research
project analysing the Great Firewall of
China](http://cs.unm.edu/~royaen/projects/gfw/).
In particular, the following tests are supported.

 * TCP backlog scan which probes a Linux machine's SYN backlog in order to
   learn how many half-open TCP connections it currently has.  This is
   implemented by `synscan.sh` and `rstscan.sh`.
 * Traceroute script which runs a number of traceroutes to a given host.  This
   is implemented by `traceroute.sh` and `traceroute_host.sh`.
 * All tests are wrapped by the script `probing_wrapper.sh` which invokes
   `probe_host.sh`.

Feedback
========

Contact: Philipp Winter <phw@nymity.ch>  
OpenPGP fingerprint: `B369 E7A2 18FE CEAD EB96  8C73 CF70 89E3 D7FD C0D0`
