#!/bin/sh

PATH=$PATH:/bin:/usr/local/bin:/usr/local/sbin
export PATH
#mkdir -p /data0/htdocs/
#touch /data0/htdocs/exclude.list.centos /data0/htdocs/exclude.list.epel /data0/htdocs/exclude.list.rpmfusion /data0/htdocs/exclude.list.fedora
#
#add the entries into /etc/crontab for cron jobs
#0 */6 * * * root perl -le 'sleep rand 900' && bash -l /data0/htdocs/mirrors_sync_ver2.sh mirrors.s1na.com.cn centos >/dev/null 2>&1
#15 */6 * * * root perl -le 'sleep rand 900' && bash -l /data0/htdocs/mirrors_sync_ver2.sh mirrors.s1na.com.cn epel >/dev/null 2>&1
#30 */6 * * * root perl -le 'sleep rand 900' && bash -l /data0/htdocs/mirrors_sync_ver2.sh mirrors.s1na.com.cn rpmfusion >/dev/null 2>&1
#45 */6 * * * root perl -le 'sleep rand 900' && bash -l /data0/htdocs/mirrors_sync_ver2.sh mirrors.s1na.com.cn fedora >/dev/null 2>&1
#
#by navigator182@20121128

if [ $# -lt 2 ]; then
        echo "usage: $0 <local-domain-root> <sub-module>
  <local-domain-root> may be local repositories website root directory.
  <sub-module> may be a sub directory of configured repositories like
	centos ,epel ,fedora etc. 
example: $0 mirrors.s1na.com.cn centos"
        exit 1
fi

CURPATH="/data0/htdocs" && cd $CURPATH

#Local Site Root
ROOTDIR=$1
SUBDIR=$2
LROOT="/data0/htdocs/$1/$2"

#Master SYNC Site
case $SUBDIR in
centos)
	#MSYNC="us-msync.centos.org::CentOS"
	#MSYNC="eu-msync.centos.org::CentOS"
	#MSYNC="rsync://mirrors.sohu.com/centos"
	MSYNC="rsync://mirrors.tuna.tsinghua.edu.cn/centos"
	[ ! -d $LROOT ] && (mkdir -p $LROOT)
	;;
epel)
	#MSYNC="rsync://dl.fedoraproject.org/fedora-epel"
	#MSYNC="rsync://mirrors.sohu.com/fedora-epel"
	MSYNC="rsync://mirrors.tuna.tsinghua.edu.cn/epel"
	[ ! -d $LROOT ] && (mkdir -p $LROOT)
	;;
rpmfusion)
	#MSYNC="rsync://mirrors.tuna.tsinghua.edu.cn/rpmfusion"
	MSYNC="rsync://download1.rpmfusion.org/rpmfusion"
	[ ! -d $LROOT ] && (mkdir -p $LROOT)
	;;
fedora)
	#MSYNC="rsync://dl.fedoraproject.org/fedora-enchilada"
	#MSYNC="rsync://mirrors.sohu.com/fedora"
	MSYNC="rsync://mirrors.tuna.tsinghua.edu.cn/fedora"
	LROOT="/data0/htdocs/$1/$2/linux"
	[ ! -d $LROOT ] && (mkdir -p $LROOT)
	;;
*)
	echo "no matched Master Mirrors"
	exit 1
	;;
esac

echo "will sync $MSYNC to $LROOT"

#log handled
[ ! -d $CURPATH/logs ] && (mkdir -p $CURPATH/logs)
TODAY=`date "+%Y%m%d"`
LASTYEAR=`date -d "1 years ago" "+%Y%m%d"`
LOGFILE=$CURPATH/logs/"$TODAY"_"$SUBDIR"_mirror.log
[ -f $CURPATH/logs/"$LASTYEAR"_"$SUBDIR"_mirror.log ] && (/bin/rm -f $CURPATH/logs/"$LASTYEAR"_"$SUBDIR"_mirror.log)

EXCLUDES="$CURPATH/exclude.list.$SUBDIR"
#SYNC="rsync -avH --timeout=60 --exclude-from=$EXCLUDES --delete-excluded --numeric-ids --delete --delete-after --delay-updates"
SYNC="rsync -avH --timeout=60 --exclude-from=$EXCLUDES --numeric-ids --delete --delete-after --delay-updates"
RETRYTIME=180

RUN=`ps x | grep -E "$MSYNC" | grep -v grep | wc -l`
if [ "$RUN" -gt 0 ];
then
	echo "mirrors sync already running"
	exit 1
else
        echo "engine start in 5 sec"
        printf "5....." && sleep 1 && printf "4...."  && sleep 1 && printf "3..."  && sleep 1 && printf "2.."  && sleep 1 && printf "1." && sleep 1 && printf "Go!" 
fi

	echo "===`date "+%Y%m%d %T"` Start mirror from $MSYNC===" >>$LOGFILE
	$SYNC $MSYNC $LROOT >>$LOGFILE 2>&1
	if [ $? -ne 0 ]
		then
		echo "`date "+%Y%m%d %T"` Waiting $RETRYTIME sec for retry mirror $MSYNC" >>$LOGFILE
		sleep $RETRYTIME
		$SYNC $MSYNC $LROOT >>$LOGFILE 2>&1
		if [ $? -ne 0 ]
			then
			echo "`date "+%Y%m%d %T"` Retry mirror $MSYNC failed" >>$LOGFILE
#			exit 1
		fi 
	fi

echo "===`date "+%Y%m%d %T"` END ,See U Next Time===" >>$LOGFILE

##########################################################################
#Unless you are running or intending to run a listed public CentOS mirror#
#use a mirror listed at http://centos.org/download/mirrors               #
#                                                                        #
#If you intend to populate a mirror for public use please read the       #
#notes at http://wiki.centos.org/HowTos/CreatePublicMirrors              #
##########################################################################
