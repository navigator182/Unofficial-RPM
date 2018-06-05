#!/bin/sh
#
# description: gmond check script
# wrote by navigator182@20180602
#

GSTAT=/usr/bin/gstat
GMOND=/usr/sbin/gmond
GMOND_S=/etc/init.d/gmond

[ -x $GSTAT ] || exit 5
[ -x $GMOND_S ] || exit 7

. /etc/rc.d/init.d/functions

status $GMOND
RETVAL=$?
echo
[ $RETVAL -eq 0 ] || exit 9

$GSTAT
RETVAL_G=$?
echo
[ $RETVAL_G -eq 0 ] || $GMOND_S restart
exit $?

