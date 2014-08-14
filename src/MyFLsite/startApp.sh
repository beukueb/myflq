#!/bin/bash

#This script serves as a wrapper for the MyFLcontainer
#It starts necessary services, such as MySQL, prior to
#executing the webb app

#Services
/usr/bin/supervisord -c /myflq/supervisord.conf
#/usr/sbin/mysqld &

#Setup postgresql
sleep 5
expect <<EOF
spawn sudo -u postgres createuser -s -P admin
expect "password" { send "passall\r" }
expect "again" { send "passall\r" }
expect eof
EOF

sudo -u postgres createdb -O admin MyFLqADMIN

##MyFLsite
useradd myflsiteuser
sudo -u postgres createuser -d myflsiteuser
sudo -u myflsiteuser createdb myflsitedb

cd /myflq/MyFLsite

#Configuring databases and superuser with expect
expect <<EOF
spawn sudo -u myflsiteuser python3 manage.py syncdb

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

#If 'test' argument passed, set up test user and analysis
if [ "$1" == "test" ]; then
    python3 <<EOF
print("Installing 'test' user")
import os,sys,gzip,django
os.environ['DJANGO_SETTINGS_MODULE'] = 'MyFLsite.settings'
sys.path.append('.')
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
User.objects.create_user(username='test', password='test')
c = Client()
c.login(username='test', password='test')
response = c.post('/myflq/setup/', {'dbname': 'testdb','submitaction':'createdb'})
optionValue = [i for i in response.content.decode().split('\n')
                       if 'option' in i and '>testdb<' in i][0].split('"')[1]
with open('../loci/myflqpaper_loci.csv','rb') as fp:
    response = c.post('/myflq/setup/', {'dbname': optionValue,'submitaction':'addlocifile','fileName': fp})
with open('../alleles/myflqpaper_alleles.csv','rb') as fp:
    c.post('/myflq/setup/', {'dbname': optionValue,'submitaction':'addallelesfile','alleleFile': fp})
c.post('/myflq/setup/', {'dbname': optionValue,'submitaction':'commitdb'})
with gzip.open('../testing/test_subsample_9947A.fastq.gz','rb') as fp:
    c.post('/myflq/analysis/', {'dbname': optionValue,
                                'fastq': fp,
                                'negativeReadsFilter': 'on',
                                'clusterInfo': 'on',
                                'threshold': '0.05',
                                'primerBuffer': '0',
                                'stutterBuffer': '1',
                                'flankOut': 'on',
                                'useCompress': 'on',
                                'submitaction': 'analysisform'
                               })
print("You can now use the user 'test' with password 'test' to have a quick look at MyFLq")
exit()
EOF
fi

#Starting server
echo "For administrative use, go to http://localhost/admin"
echo "You can log in with user 'admin' and password 'myfl1234admin'"
sudo -u myflsiteuser python3 manage.py runserver 0.0.0.0:8000 &

#Allowing interaction from system admin
sleep 10 #to have commandline prompt under first django output
bash
