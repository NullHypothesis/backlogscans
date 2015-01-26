#!/usr/bin/env python
#
# Copyright 2014 Philipp Winter <phw@nymity.ch>

import csv
import sys
import os
import argparse
import logging
import datetime
import time

import pygmaps

LAT_LON_CSV = "gsIPs-lat-long.csv"

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(fmt="%(asctime)s [%(levelname)s]: "
                                           "%(message)s"))

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

icon_paths = {
    1: "https://raw.githubusercontent.com/NullHypothesis/backlogscans/master/plotting/icons/source_icon.png",
    2: "https://raw.githubusercontent.com/NullHypothesis/backlogscans/master/plotting/icons/destination_icon.png",
    3: "https://raw.githubusercontent.com/NullHypothesis/backlogscans/master/plotting/icons/hybrid_icon.png"
}

path_colours = {
    1: "#000000", # Error.
    2: "#FF0000", # Server-to-client drop.
    3: "#00FF00", # No drop.
    4: "#FF8800"  # Client-to-server drop.
}

class Machine( object ):

    """Represents a machine which is part of a scan."""

    def __init__( self, ip_addr, latitude, longitude, region=None,
                  machine_type=None ):

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

    def get_ip_addresses( self ):

        return (self.src_host.ip_addr,
                self.dst_host.ip_addr)

    def __str__( self ):

        s = "Type %d at hour %d: %s --> %s" % (self.scan_verdict,
                                               self.hour,
                                               self.src_host,
                                               self.dst_host)
        return s

class Cluster( object ):

    def __init__( self, cluster_id ):

        self.cluster_id = str(cluster_id)
        self.machines = []

    def add_machine( self, machine ):

        self.machines.append(machine)

    def __iter__( self ):
        return iter(self.machines)

    def __str__( self ):

        return self.cluster_id + "\n\t" + \
               "\n\t".join([str(m) for m in self.machines])

def get_lat_long( loc_data, ip_addr ):

    fd = open(loc_data, 'r')
    reader = csv.DictReader(fd,
                            fieldnames = ['ip', 'lat', 'lon', 're', 'ipt'],
                            delimiter = ',',
                            quotechar = '"',
                            skipinitialspace=True)

    loc_data = list(reader)

    for lats in loc_data:
        if ip_addr in lats['ip']:
            return [lats['lat'], lats['lon'], lats['re'], lats['ipt']]

    return None

def print_clusters( clusters, file_name ):
    """
    Analyse all clusters and write a map to the given file.
    """

    # arg1: start latitude
    # arg2: start longitude
    # arg3: default zoom level (must be in {0..20})

    my_map = pygmaps.maps(0, 0, 2)

    # First, parse all scans and create dictionaries for the markers/points as
    # well as paths.

    colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#00ffff",
              "#ff00ff", "#000000", "#ffffff",
              "#770000", "#007700", "#000077", "#777700", "#007777",
              "#770077"]

    for cluster in clusters:

        points = {}

        # Determine cluster color.

        color = colors.pop(0)

        # points key=coordinates, value=ip address(es)

        for machine in cluster.machines:
            if points.has_key(machine.get_coordinates()):
                points[machine.get_coordinates()].append(machine.ip_addr)
            else:
                points[machine.get_coordinates()] = [machine.ip_addr]

        for latitude, longitude in points:
            my_map.addpoint(latitude, longitude,
                            color=color,
                            title=",".join(points[(latitude, longitude)]))

    logger.info("Writing output to \"%s\"." % file_name)
    my_map.draw(file_name)

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
        my_map.addpoint(latitude, longitude, "#FFFFFF", icon=icon_path)

    # Finally, plot the paths between the points.  Again, depending on the scan
    # verdict, we plot the path in different colours.

    for src_coordinates, dst_coordinates in paths:

        scan_verdict = paths[(src_coordinates, dst_coordinates)]

        if path_colours.has_key(scan_verdict):
            colour = path_colours[scan_verdict]
        else:
            colour = "#0000FF"

        my_map.addpath([src_coordinates, dst_coordinates], color=colour)

    logger.info("Writing output to \"%s\"." % file_name)
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

def parse_clusters( file_name ):
    """
    Read the entire given file and create cluster objects out of the data.
    """

    clusters = []
    fd = open(file_name, 'r')
    cluster_id = 0

    while True:
        line = fd.readline()
        if not line:
            break

        # Format: <ip_1>, <ip_2>, ..., <ip_n>

        ip_addrs = [ip_addr.strip() for ip_addr in line.split(',')]
        cluster = Cluster(cluster_id)
        cluster_id += 1

        for ip_addr in ip_addrs:

            ret = get_lat_long(LAT_LON_CSV, ip_addr)
            if not ret:
                logger.error("No location information for IP address %s." %
                             ip_addr)
                continue
            else:
                lat, lon = ret[:2]

            cluster.add_machine(Machine(ip_addr, float(lat), float(lon)))

        clusters.append(cluster)

    return clusters

def parse_arguments( args ):

    parser = argparse.ArgumentParser(description="Plot and filter idle "
                                     "scan results on a clustered Google map.")

    parser.add_argument("datafile", metavar="IDLE_SCAN_FILE",
                        help="Parse and plot the given file.")

    parser.add_argument("-w", "--write", metavar="OUTPUT_FILE",
                        type=str, default="idle_scan_map.html",
                        help="Write HTML output to the given file.")

    parser.add_argument("-d", "--directory", metavar="OUTPUT_DIR",
                        type=str, default=None,
                        help="Where to write all analysis files to.")

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

    parser.add_argument("-c", "--cluster", metavar="CLUSTER_FILE",
                        type=str, help="Use the given cluster file.")

    return parser.parse_args()

def mkdir_analysis( dirname ):
    """
    Create and return a directory where all created data is stored.
    """

    if not dirname:
        dt = datetime.datetime.fromtimestamp(time.time())
        dirname = dt.strftime("%Y-%m-%d_%H:%M:%S")

    try:
        os.mkdir(dirname)
    except OSError as err:
        logger.error("Could not create directory: %s" % err)
        exit(1)

    return dirname

def main( ):
    """
    The tool's entry point.
    """

    args = parse_arguments(sys.argv[0:])

    dirname = mkdir_analysis(args.directory)

    if args.cluster:
        logger.debug("Parsing IP address cluster file `%s'." % args.cluster)
        clusters = parse_clusters(args.cluster)
        print_clusters(clusters, "%s/ip_addr_clusters.html" % dirname)

    logger.debug("Parsing idle scan file `%s'." % args.datafile)
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
        print_map(scans, "%s/%s" % (dirname, args.write))
        logger.info("Wrote HTML data to `%s'." % args.write)

    # Create cluster-specific scan maps.  Every scan in all scan maps contains
    # an IP address which is part of a cluster.

    if not args.cluster:
        return 0

    for cluster in clusters:

        cluster_scans = []

        for machine in cluster:
            for scan in scans:
                if machine.ip_addr in scan.get_ip_addresses():
                    cluster_scans.append(scan)

        print_map(cluster_scans, "%s/cluster_%s.html" % (dirname,
                                                         cluster.cluster_id))

    return 0

if __name__ == "__main__":
    exit(main())
