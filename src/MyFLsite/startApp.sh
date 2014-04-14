#!/bin/bash

#This script serves as a wrapper for the MyFLcontainer
#It starts necessary services, such as MySQL, prior to
#executing the webb app

#Services
/usr/bin/supervisord
#/usr/sbin/mysqld &

#Setup MySQL for MyFLq
sleep 10 #mysqld needs some time to start up (maybe less than 5 seconds is also ok)
mysql <<EOF
    CREATE DATABASE myflsitedb CHARACTER SET utf8;
    CREATE USER 'myflsiteuser'@'localhost' IDENTIFIED BY 'myfl1234user';
    GRANT ALL ON myflsitedb.* TO 'myflsiteuser'@'localhost';
EOF

cd /myflq/MyFLsite

#Configuring databases and superuser with EOF
python3 manage.py syncdb <<EOF
yes
admin
admin@localhost
myfl1234admin
myfl1234admin
EOF

#Starting simple taskmanager (for more advance use still need to configure celery)
python3 myflq/simple_tasks.py &

#Starting server
python3 manage.py runserver 0.0.0.0:8000
#bash