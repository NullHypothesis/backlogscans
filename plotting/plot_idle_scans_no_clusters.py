#!/usr/bin/env python
#
# Copyright 2014 Philipp Winter <phw@nymity.ch>

import sys
import argparse
import logging

import pygmaps

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(fmt="%(asctime)s [%(levelname)s]: "
                                           "%(message)s"))

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

icon_paths = {
    1: "source_icon.png",      # Source.
    2: "destination_icon.png", # Destination.
    3: "hybrid_icon.png"       # Hybrid (source and destination).
}

path_colours = {
    1: "#000000", # Error.
    2: "#FF0000", # Server-to-client drop.
    3: "#00FF00", # No drop.
    4: "#FF8800"  # Client-to-server drop.
}

class Machine( object ):

    """Represents a machine which is part of a scan."""

    def __init__( self, ip_addr, latitude, longitude, region, machine_type ):

        self.ip_addr = ip_addr
        self.latitude = latitude
        self.longitude = longitude
        self.region = region
        self.machine_type = machine_type

    def get_coordinates( self ):

        return (self.latitude, self.longitude)

    def __str__( self ):

        s = "%s (%.5f:%.5f, %s, %s)" % (self.ip_addr,
                                        self.latitude,
                                        self.longitude,
                                        self.region,
                                        self.machine_type)
        return s

class Scan( object ):

    """Represents a scan between two machines."""

    def __init__( self, scan_verdict, src_host, dst_host, hour ):

        self.scan_verdict = scan_verdict
        self.src_host = src_host
        self.dst_host = dst_host
        self.hour = hour

    def get_hosts( self ):

        return (self.src_host, self.dst_host)

    def __str__( self ):

        s = "Type %d at hour %d: %s --> %s" % (self.scan_verdict,
                                               self.hour,
                                               self.src_host,
                                               self.dst_host)
        return s

def print_map( scans, file_name ):
    """
    Analyse all scans and write a map to the given file.
    """

    global icon_paths
    global path_colours

    # arg1: start latitude
    # arg2: start longitude
    # arg3: default zoom level (must be in {0..20})

    my_map = pygmaps.maps(0, 0, 2)

    # First, parse all scans and create dictionaries for the markers/points as
    # well as paths.

    points = {}
    paths = {}

    for scan in scans:

        src_host, dst_host = scan.get_hosts()
        path = (src_host.get_coordinates(), dst_host.get_coordinates())

        # Paths can overlap but for performance reasons, we plot them only
        # once.  So for every overlapping path, store the scan result (block,
        # error, unblocked) in a bitmap.

        if paths.has_key(path):
            paths[path] |= (scan.scan_verdict + 1)
        else:
            paths[path] = (scan.scan_verdict + 1)

        # We also plot overlapping points only once.  We store the point type
        # (scan source or destination) in a bitmap.

        src_coordinates = src_host.get_coordinates()
        if points.has_key(src_coordinates):
            points[src_coordinates] |= 1
        else:
            points[src_coordinates] = 1

        dst_coordinates = dst_host.get_coordinates()
        if points.has_key(dst_coordinates):
            points[dst_coordinates] |= 2
        else:
            points[dst_coordinates] = 2

    # Now that we have all our points, plot them.  Depending on the determined
    # bitmap, we plot the source, destination, or hybrid icon for the point.

    for latitude, longitude in points:

        icon_path = icon_paths[points[(latitude, longitude)]]
        my_map.addpoint(latitude, longitude, "#FFFFFF", icon_path)

    # Finally, plot the paths between the points.  Again, depending on the scan
    # verdict, we plot the path in different colours.

    for src_coordinates, dst_coordinates in paths:

        scan_verdict = paths[(src_coordinates, dst_coordinates)]

        if path_colours.has_key(scan_verdict):
            colour = path_colours[scan_verdict]
        else:
            colour = "#0000FF"

        my_map.addpath([src_coordinates, dst_coordinates], color=colour)

    print "Writing output to \"%s\"." % file_name
    my_map.draw(file_name)

def parse_file( file_name ):
    """
    Read the entire given file and create scan objects out of the data.
    """

    scans = []
    fd = open(file_name, 'r')

    while True:
        line = fd.readline()
        if not line:
            break
        line = line.strip()

        values = line.split(' ')
        src_host = Machine(values[1], float(values[2]), float(values[3]),
                           values[7], values[8])
        dst_host = Machine(values[4], float(values[5]), float(values[6]),
                           values[9], values[10])

        scans.append(Scan(int(values[0]), src_host, dst_host, int(values[11])))

    logger.info("Read %d idle scans from file `%s'." %
                (len(scans), file_name))

    return scans

def parse_arguments( args ):

    parser = argparse.ArgumentParser(description="Plot and filter idle "
                                     "scan results on a clustered Google map.")

    parser.add_argument("datafile", metavar="DATA_FILE",
                        help="Parse and plot the given file.")

    parser.add_argument("-w", "--write", metavar="OUTPUT_FILE",
                        type=str, default="scan_map.html",
                        help="Write HTML output to the given file.")

    parser.add_argument("-r", "--region", metavar="REGION",
                        type=str, help="Region information of source or "
                                       "destination machine (e.g.: CN_R7).")

    parser.add_argument("-H", "--hour", metavar="HOUR",
                        type=int, help="Scan hour (e.g.: 0-23).")

    parser.add_argument("-t", "--type", metavar="TYPE", type=str,
                        help="Type of source or destination machine (e.g.: "
                             "Tor_Relay, Tor_Dir, Web_Server, GIP).")

    parser.add_argument("-v", "--verdict", metavar="VERDICT", type=int,
                        help="The scan's verdict (e.g.: 0, 1, 2, 3).")

    parser.add_argument("-a", "--address", metavar="ADDRESS", type=str,
                        help="IP address of source or destination machine "
                             "(e.g.: 1.2.3.4).")

    parser.add_argument("-i", "--inspect",
                        action="store_true",
                        help="Only display search result without printing "
                             "HTML/JavaScript.  Useful for manual analysis.")

    return parser.parse_args()

def main( ):
    """
    The tool's entry point.
    """

    args = parse_arguments(sys.argv[0:])

    logger.debug("Parsing file `%s'." % args.datafile)

    scans = parse_file(args.datafile)

    # Filter scans based on the user's parameters.

    logger.debug("Filtering idle scan data.")

    if args.region is not None:
        scans = filter(lambda scan: scan.src_host.region == args.region or
                                    scan.dst_host.region == args.region, scans)

    if args.hour is not None:
        scans = filter(lambda scan: scan.hour == args.hour, scans)

    if args.type is not None:
        scans = filter(lambda scan: scan.src_host.machine_type == args.type or
                                    scan.dst_host.machine_type == args.type,
                       scans)

    if args.verdict is not None:
        scans = filter(lambda scan: scan.scan_verdict == args.verdict, scans)

    if args.address is not None:
        scans = filter(lambda scan: scan.src_host.ip_addr == args.address or
                                    scan.dst_host.ip_addr == args.address,
                       scans)

    # Depending on what user wants, print object representations or
    # browser-ready HTML/JavaScript.

    if not scans:
        logger.warning("No scan data after filtering steps.")
    else:
        logger.info("%d idle scans remain after filtering step." % len(scans))

    if args.inspect:
        for scan in scans:
            print scan
    else:
        print_map(scans, args.write)
        logger.info("Wrote HTML data to `%s'." % args.write)

    return 0

if __name__ == "__main__":
    exit(main())
