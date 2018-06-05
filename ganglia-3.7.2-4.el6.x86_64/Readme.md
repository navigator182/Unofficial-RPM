ganglia-3.7.2-4.el6.x86_64

navigator182@gmail.com @20180605

==============

1.RPMBuild in Centos6.6

2.Follow the offical packaging rules.

3.Provide SRPMs.

=======

gmetad:

4.turn on rrdcached in writing rrds with ganglia_conf_files/etc/rc.d/init.d/gmetad. it optimizes so much for disk responsiveness and reduces io latency by using memory cache.


=======

ganglia-web:

5.turn on rrdcached in reading rrds with ganglia_conf_files/etc/ganglia/conf.php


=======

ganglia-gmond:

6.Provides some plugins that be included in ganglia sources but epel offical rpm package.

/etc/ganglia/conf.d/

apache_status.pyconf.disabled

example.pyconf.disabled

memcached.pyconf.disabled

modgstatus.conf

mysql.pyconf.disabled

nfsstats.pyconf.disabled

redis.pyconf.disabled

riak.pyconf.disabled

spfexample.pyconf.disabled

tcpconn.pyconf

traffic1.pyconf.disabled

varnish.pyconf.disabled

xenstats.pyconf.disabled


7.Modify the tcpconn plugin command "netstat -ant" to "ss -ant", it's good for a large number of tcp network connections(e.g.CDN Devices).
with the files

ganglia-3.7.2-4.el6.x86_64/ganglia_conf_files/usr/lib64/ganglia/python_modules/tcpconn.py

ganglia_conf_files/etc/ganglia/conf.d/tcpconn.pyconf


8.Provide udpconn plugin like tcpconn. it only display State ESTAB and UNCONN in the Statelessness of udp.

with the files

ganglia-3.7.2-4.el6.x86_64/ganglia_conf_files/usr/lib64/ganglia/python_modules/udpconn.py

ganglia_conf_files/etc/ganglia/conf.d/udpconn.pyconf


9.Check gmond state and restart gmond for a bug. sometimes gmetad can not fetching xml data from tcp port 8649 of the cluster proxy gmond.

set file "ganglia_conf_filesopt/scripts/gmond_check.sh"

and add the item in /etc/crontab

"# restart gmond when gmetad can not fetch xml data SALT_CRON_IDENTIFIER:common_gmond_check"

"* * * * * root bash -l /opt/scripts/gmond_check.sh >/dev/null 2>&1"
