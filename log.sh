#!/bin/bash
#
# Copyright 2014 Philipp Winter <phw@nymity.ch>

log() {
	local msg="$1"
	printf "[$(date -u --rfc-3339=ns)] ${msg}\n"
}

err() {
	local msg="$1"
	printf "[$(date -u --rfc-3339=ns)] ${msg}\n" >&2
}
