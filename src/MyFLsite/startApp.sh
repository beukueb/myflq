#!/bin/bash

#This script serves as a wrapper for the MyFLcontainer
#It starts necessary services, such as MySQL, prior to
#executing the webb app

#Services
/usr/bin/supervisord -c /myflq/supervisord.conf
#/usr/sbin/mysqld &

#Setup MySQL for MyFLq
sleep 10 #mysqld needs some time to start up (maybe less than 5 seconds is also ok)
##MyFLdb
mysql <<EOF                                                                                                         
GRANT ALL ON *.* TO 'admin'@'localhost' IDENTIFIED BY 'passall' WITH GRANT OPTION; 
FLUSH PRIVILEGES;
EOF
python3 /myflq/MyFLdb.py --install admin -p 'passall'

##MyFLsite
mysql <<EOF
    CREATE DATABASE myflsitedb CHARACTER SET utf8;
    CREATE USER 'myflsiteuser'@'localhost' IDENTIFIED BY 'myfl1234user';
    GRANT ALL ON myflsitedb.* TO 'myflsiteuser'@'localhost';
EOF
cd /myflq/MyFLsite

#Configuring databases and superuser with expect
expect <<EOF
spawn python3 manage.py syncdb

set timeout 60
expect "(yes/no):" { send "yes\r" }
expect "Username" { send "admin\r" }
expect "Email" { send "admin@localhost\r" }
expect "Password" { send "myfl1234admin\r" }
expect "Password" { send "myfl1234admin\r" }
expect eof
EOF

#Taskmanager celery started with supervisord
#python3 myflq/simple_tasks.py & #deprecated

#Starting server
echo "For administrative use, go to http://localhost/admin"
echo "You can log in with user 'admin' and password 'myfl1234admin'"
python3 manage.py runserver 0.0.0.0:8000 &
bash #Debug
