#!/bin/bash

outfile="relays.txt"

if [ ! -e consensus ]
then
	# Download the current consensus from moria.
	wget http://128.31.0.39:9131/tor/status-vote/current/consensus
fi

grep '^r' consensus | \
	grep -oE '((1?[0-9][0-9]?|2[0-4][0-9]|25[0-5])\.){3}(1?[0-9][0-9]?|2[0-4][0-9]|25[0-5]) ([0-9]{1,5})' | \
	sed 's/ /:/g' > $outfile

echo "[+] Wrote relays to \"${outfile}\"."
