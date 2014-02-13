#!/usr/bin/env python
#
# Copyright 2014 Philipp Winter <phw@nymity.ch>

import sys
import argparse
import logging

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(fmt="%(asctime)s [%(levelname)s]: "
                                           "%(message)s"))

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

pre_data="""
<!DOCTYPE>
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8" />
    <title>MarkerClusterer v3 Example</title>

    <style type="text/css">
      body {
        margin: 0;
        padding: 10px 20px 20px;
        font-family: Arial;
        font-size: 16px;
      }

      #map-container {
        padding: 6px;
        border-width: 1px;
        border-style: solid;
        border-color: #ccc #ccc #999 #ccc;
        -webkit-box-shadow: rgba(64, 64, 64, 0.5) 0 2px 5px;
        -moz-box-shadow: rgba(64, 64, 64, 0.5) 0 2px 5px;
        box-shadow: rgba(64, 64, 64, 0.1) 0 2px 5px;
        width: 600px;
      }

      #map {
        width: 1500px;
        height: 800px;
      }

    </style>
    <script src="markerclusterer.js"></script>
    <script src="http://maps.google.com/maps/api/js?sensor=false"></script>
    <script type="text/javascript">
      function initialize() {
        var center = new google.maps.LatLng(37.4419, -122.1419);

        var map = new google.maps.Map(document.getElementById('map'), {
          zoom: 3,
          center: center,
          mapTypeId: google.maps.MapTypeId.ROADMAP
        });

        var markers = [];
"""

post_data="""
        var markerCluster = new MarkerClusterer(map, markers);
      }
      google.maps.event.addDomListener(window, 'load', initialize);
    </script>
  </head>
  <body>
    <h3>A simple example of MarkerClusterer</h3>
    <p>
      <a href="?compiled">Compiled</a> |
      <a href="?">Standard</a> version of the script.
    </p>
    <div id="map-container"><div id="map"></div></div>
  </body>
</html>
"""

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

    def __init__( self, scan_type, src_host, dst_host, hour ):

        self.scan_type = scan_type
        self.src_host = src_host
        self.dst_host = dst_host
        self.hour = hour

    def get_hosts( self ):

        return (self.src_host, self.dst_host)

    def __str__( self ):

        s = "Type %d at hour %d: %s --> %s" % (self.scan_type,
                                               self.hour,
                                               self.src_host,
                                               self.dst_host)
        return s

def print_map( scans, file_name ):
    """
    Print the gathered scan data to an HTML file to be viewed in a browser.
    """

    if file_name:
        fd = open(file_name, 'w')
    else:
        fd = sys.stdout

    fd.write(pre_data)

    # Add the source and destination points for every scan.  Both machines have
    # different colors.  They are also connected by a path.

    for scan in scans:
        src_host, dst_host = scan.get_hosts()

        # We only plot the scan source as a marker.  The library takes care of
        # also plotting the destination (mrk.dst).

        fd.write("var mrk = new google.maps.Marker({ position: new "
                 "google.maps.LatLng( %.5f, %.5f )});\n" %
                 (src_host.latitude, src_host.longitude))
        fd.write("var dst = new google.maps.Marker({ position: new "
                 "google.maps.LatLng( %.5f, %.5f )});\n" %
                 (dst_host.latitude, dst_host.longitude))
        fd.write("mrk.dst = dst;\n")
        fd.write("markers.push(mrk);\n")

    fd.write(post_data)

    if file_name:
        fd.close()

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
        scans = filter(lambda scan: scan.scan_type == args.verdict, scans)

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
