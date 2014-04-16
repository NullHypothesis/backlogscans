
import csv

def get_lat_long(IP):
	loc_data = list( csv.DictReader( open(loc_data, 'rb'), fieldnames = ['ip', 'lat', 'lon', 're', 'ipt'], delimiter = ',', quotechar = '"', skipinitialspace=True) )

	for lats in loc_data:
		if IP in lats['ip']:
			return([lats['lat'],lats['lon'],lats['re'],lats['ipt']])
	print "\n \nThis IP info is not in loc_data", IP,"\n \n"
	return(['0','0',"NULL","NULL"])
