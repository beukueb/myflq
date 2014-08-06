#!/bin/bash

#This script serves as a wrapper for the MyFLcontainer
#It starts necessary services, such as MySQL, prior to
#executing the main analysis program MyFLq.py

#Services
/usr/bin/supervisord -c /myflq/supervisord.conf
#/usr/sbin/mysqld &

#Setup MySQL for MyFLq
sleep 10 #mysqld needs some time to start up (maybe less than 5 seconds is also ok)
mysql <<EOF
GRANT ALL ON *.* TO 'admin'@'localhost' IDENTIFIED BY 'passall' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EOF
#yes '' | python3 /myflq/MyFLdb.py --install root
python3 /myflq/MyFLdb.py --install admin -p 'passall'

#Start wrapper py
python3 /myflq/basespace/myflq_wrapper.py $@ #passes any arguments that come from run container
exitValueMainProgram=$?

#For debug
#echo $1 > /tmp/testargs
#echo $@
#bash #Be sure to comment this out for published version

#Have to remain last commands
if [ $exitValueMainProgram != 0  ];
  then echo Something went wrong with MyFLq. \
            Please send the above information bag to us, \
            or share this project with us, so we can debug it. ;
fi
exit $exitValueMainProgram
