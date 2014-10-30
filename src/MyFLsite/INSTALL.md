DEPLOYMENT DOCUMENTATION
========================
These are instructions on how to install MyFLq webapp outside of a container in a server environment.
To do that you can simply clone the whole repository.

To write this documentation, a virtualbox ubuntu server 12.04 64bit was freshly installed
(OpenSSH server, LAMP server and Mail server included in the install)

After the main example, you can find an install on a CentOS 5 server.

# Ubuntu 12.04 server
## Dependencies

    sudo apt-get install libapache2-mod-wsgi-py3
    sudo apt-get install python3 python3-setuptools
    sudo easy_install3 django
    sudo apt-get install git libmysqlclient-dev python3-dev
    git clone https://github.com/clelland/MySQL-for-Python-3.git
    cd MySQL-for-Python-3/
    python3 setup.py build
    sudo python3 setup.py install
    sudo easy_install3 Pillow
    sudo apt-get install rabbitmq-server
    sudo easy_install3 Celery

## Prepare server mysql
With "mysql -uroot -p":

    CREATE DATABASE myflsitedb CHARACTER SET utf8;
    CREATE USER 'myflsiteuser'@'localhost' IDENTIFIED BY 'myfl1234user';
    GRANT ALL ON myflsitedb.* TO 'myflsiteuser'@'localhost';

## Extract and test web app

    git clone https://github.com/beukueb/myflq
    cd myflq/src/MyFLsite
    python3 manage.py syncdb
    python3 manage.py runserver 0.0.0.0:8000 #to test via host browser

## Change app settings for deployment
With "mg MyFLsite/settings.py":

    #Static files
    STATIC_URL = '/static/'
    STATIC_ROOT = '/var/www/myflsite/static/'
    STATICFILES_DIRS = (  
        os.path.join(BASE_DIR, "static"),
    )
    MEDIA_URL = '/media/'
    MEDIA_ROOT = '/var/www/myflsite/media/'
    
    #Email
    #Debug #=> still to be updated in documentation!!!

And next:

    sudo mkdir -p /var/www/myflsite/media
    sudo chown -R christophe:christophe /var/www/myflsite
    sudo chown -R www-data:www-data /var/www/myflsite/media #necessary for apacha, not for manage.py runserver
    python3 manage.py collectstatic

## Update httpd.conf
With "sudo mg /etc/apache2/httpd.conf":

    #Alias /robots.txt /var/www/myflsite/static/robots.txt
    Alias /favicon.ico /var/www/myflsite/static/favicon.ico

    AliasMatch ^/([^/]*\.css) /var/www/myflsite/static/styles/$1

    Alias /media/ /var/www/myflsite/media/
    Alias /static/ /var/www/myflsite/static/

    <Directory /var/www/myflsite/static>
    Order deny,allow
    Allow from all
    </Directory>

    <Directory /var/www/myflsite/media>
    Order deny,allow
    Allow from all
    </Directory>

    WSGIScriptAlias / /home/christophe/MyFLqApp/MyFLsite/MyFLsite/wsgi.py
    WSGIPythonPath /home/christophe/MyFLqApp/MyFLsite/

    <Directory /home/christophe/MyFLqApp/MyFLsite/MyFLsite>
    <Files wsgi.py>
    Order deny,allow
    Allow from all
    #Require all granted #=> if Apache version < 2.4
    </Files>
    </Directory>

## Restart apache:

    sudo apache2ctl restart

## MyFL[q|db].py setup

    cd ~/MyFLsite/myflq/programs
    #MyFL[q|db].py dependencies
    sudo easy_install3 pymysql numpy
    sudo apt-get install g++ libfreetype6-dev libpng-dev #dependencies matplotlib
    #or: sudo apt-get build-dep python-matplotlib #to install all, including optional dependencies for matplotlib (+- 700 Mb)
    sudo easy_install3 python-dateutil six #other matplotlib dependency
    sudo easy_install3 -U distribute
    sudo easy_install3 matplotlib #in case of strange installation problems, try: sudo easy_install3 -m matplotlib
    #or: sudo easy_install ipython #this normally includes above dependencies and is necessary for parallel processing

With "mysql -uroot -p":

      GRANT ALL ON *.* TO 'admin'@'localhost' IDENTIFIED BY 'passall' WITH GRANT OPTION;
      FLUSH PRIVILEGES;

Install MyFLq databases

    python3 MyFLdb.py --install admin -p passall

## Enable tasks daemon
### With simple_tasks.py

    cd ~/MyFLqApp/MyFLsite
    export PYTHONPATH=$PYTHONPATH:~/github/myflq/src/MyFLsite:~/github/myflq/src
    sudo -u www-data python3 myflq/simple_tasks.py

### With celery

    sudo -i
    cd /etc/init.d/
    wget https://raw.github.com/celery/celery/3.1/extra/generic-init.d/celeryd --no-check-certificate
    chmod +x /etc/init.d/celeryd

Celery config with "emacs /etc/default/celeryd":

    # Names of nodes to start
    #   most will only start one node:
    CELERYD_NODES="worker1"
    #   but you can also start multiple and configure settings
    #   for each in CELERYD_OPTS (see `celery multi --help` for examples).
    #CELERYD_NODES="worker1 worker2 worker3"

    # Absolute or relative path to the 'celery' command:
    CELERY_BIN="/usr/local/bin/celery"
    #CELERY_BIN="/virtualenvs/def/bin/celery"

    # App instance to use
    # comment out this line if you don't use an app
    CELERY_APP="MyFLsite"
    # or fully qualified:
    #CELERY_APP="proj.tasks:app"

    # Where to chdir at start.
    CELERYD_CHDIR="/home/christophe/MyFLqApp/MyFLsite/"

    # Extra command-line arguments to the worker
    CELERYD_OPTS="--time-limit=86400 --concurrency=4"
     #86400s = 24h => after which unfinished tasks are killed

    # %N will be replaced with the first part of the nodename.
    CELERYD_LOG_FILE="/var/log/celery/%N.log"
    CELERYD_PID_FILE="/var/run/celery/%N.pid"

    # Workers should run as an unprivileged user.
    #   You need to create this user manually (or you can choose
    #   a user/group combination that already exists, e.g. nobody).
    CELERYD_USER="www-data"
    CELERYD_GROUP="www-data"

    # If enabled pid and log directories will be created if missing,
    # and owned by the userid/group configured.
    CELERY_CREATE_DIRS=1

Usage:	/etc/init.d/celeryd {start|stop|restart|status}

With "emacs /etc/rc.local":

    /etc/init.d/celeryd start #Add this line before 'exit 0'
    #Other option would be making symbolic links in relevant /etc/rcX.d/ runlevels


# CentOS 5
This section contains the steps that were necessary to get the MyFLq website running on an older server that was still running CentOS 5

cat /proc/version:

    Linux version 2.6.18-348.4.1.el5 (mockbuild@builder10.centos.org)
    (gcc version 4.1.2 20080704 (Red Hat 4.1.2-54)) #1 SMP Tue Apr 1

## Python
The system python version is 2.4.3, which is way outdated.
Install python version 3.3.0 from source:

    wget https://www.python.org/ftp/python/3.3.0/Python-3.3.0.tgz
    tar xzf Python-3.3.0.tgz
    cd Python-3.3.0
    ./configure
    make
    sudo make install #Will install it in /usr/local/bin/

Install virtualenv with python3.3

    sudo yum install python-virtualenv
        #or from source
        #wget --no-check-certificate https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.9.tar.gz
        #tar xzf virtualenv-1.9.tar.gz
        #cd virtualenv-1.9
        #/usr/local/bin/python3.3 setup.py install #will install it under /usr/local bin
    mkdir ~/.virtualenv
    virtualenv -p /usr/local/bin/python3.3 ~/.virtualenv/myflqenv
    source  ~/.virtualenv/myflqenv/bin/activate

Inside virtualenv:

    cd ~/.virtualenv/myflqenv/
    pip install numpy==1.8
    pip install ipython
    pip install matplotlib==1.3.1
    pip install django==1.6
    pip install uwsgi
    pip install pymysql
    wget http://dev.mysql.com/get/Downloads/Connector-Python/mysql-connector-python-2.0.1.tar.gz
    tar xzf mysql-connector-python-2.0.1.tar.gz
    cd mysql-connector-python-2.0.1
    python setup.py install

### Matplotlib

    yum install libpng-devel
    yum install freetype-devel

## MySQL
Was already installed but without root password available

### Reset MySQL root password
As root

    /etc/init.d/mysqld stop

As mysql user with "su mysql":

    cat > /var/lib/mysql/reset.sql <<EOF
       UPDATE mysql.user SET Password=PASSWORD('YOURNEWROOTPASSWORD') WHERE User='root';
       FLUSH PRIVILEGES;
    EOF
    mysqld_safe --init-file=/var/lib/mysql/reset.sql
   
As root

    /etc/init.d/mysqld start
    chkconfig mysqld on

## Normal config
With "mysql -uroot -pYOURNEWROOTPASSWORD"

    CREATE DATABASE myflsitedb CHARACTER SET utf8;
    #On different computer with recent MySQL client => SELECT PASSWORD('myfl1234user');
    CREATE USER 'myflsiteuser'@'localhost' IDENTIFIED BY '*5CBC1F92CB520771C013EA7C62ED99670EBC6342';
    GRANT ALL ON myflsitedb.* TO 'myflsiteuser'@'localhost';
    GRANT ALL ON *.* TO 'admin'@'localhost' IDENTIFIED BY 'passall' WITH GRANT OPTION;
    FLUSH PRIVILEGES;
    

## Nginx

    yum install nginx
    service nginx start
    chkconfig nginx on

## Celery

    yum install rabbitmq-server
    service rabbitmq-server start
    chkconfig rabbitmq-server on

## Final setup

    git clone https://github.com/beukueb/myflq
    mkdir /home/christophe/.virtualenv/myflqenv/media/
    mkdir /home/christophe/.virtualenv/myflqenv/static
    cp /etc/nginx/uwsgi_params /home/christophe/.virtualenv/myflqenv/myflq/src/MyFLsite/MyFLsite/
    cat > myflsite_nginx.conf <<EOF
    	# myflsite_nginx.conf

	# the upstream component nginx needs to connect to
	upstream django {
		 server unix:///home/christophe/.virtualenv/myflqenv/myflq/src/MyFLsite/MyFLsite/myflsite.sock; # for a file socket
	         #server 127.0.0.1:8001; # for a web port socket (we'll use this first)
		 }

	# configuration of the server
	server {
    	       # the port your site will be served on
	       listen      8000;
	       # the domain name it will serve for
	       server_name ipar4.ugent.be; # substitute your machine's IP address or FQDN
	       charset     utf-8;

	       # max upload size
	       client_max_body_size 75M;   # adjust to taste

	# Django media
	    location /media  {
	             alias /home/christophe/.virtualenv/myflqenv/media;  # your Django project's media files - amend as required
	    }

	    location /static {
	    	     alias /home/christophe/.virtualenv/myflqenv/static; # your Django project's static files - amend as required
   	    }

    	# Finally, send all non-media requests to the Django server.
    	   location / {
           	    uwsgi_pass  django;
        	    include     /home/christophe/.virtualenv/myflqenv/myflq/src/MyFLsite/MyFLsite/uwsgi_params; # the uwsgi_params file you installed
           }
	   }

    EOF
    sudo ln -s /home/christophe/.virtualenv/myflqenv/myflq/src/MyFLsite/MyFLsite/myflsite_nginx.conf /etc/nginx/conf.d/

Change the following in /home/christophe/.virtualenv/myflqenv/myflq/src/MyFLsite/MyFLsite/settings.py:

    'ENGINE': 'mysql.connector.django', #=> new database driver
    STATIC_ROOT = '/home/christophe/.virtualenv/myflqenv/static/'
    MEDIA_ROOT = '/home/christophe/.virtualenv/myflqenv/media/'

uwsgi ini file:

    cat > /home/christophe/.virtualenv/myflqenv/myflq/src/MyFLsite/MyFLsite/myflsite_uwsgi.ini <<EOF
    # myflsite_uwsgi.ini file
    [uwsgi]
    
    # Django-related settings
    # the base directory (full path)
    chdir           = /home/christophe/.virtualenv/myflqenv/myflq/src/MyFLsite/
    # Django's wsgi file
    module          = MyFLsite.wsgi
    # the virtualenv (full path)
    home            = /home/christophe/.virtualenv/myflqenv
    
    # process-related settings
    # master
    master          = true
    # maximum number of worker processes
    processes       = 10
    # the socket (use the full path to be safe
    socket          = /home/christophe/.virtualenv/myflqenv/myflq/src/MyFLsite/MyFLsite/myflsite.sock
    # ... with appropriate permissions - may be needed
    chmod-socket    = 666
    # clear environment on exit
    vacuum          = true
    EOF

##Manual startup

    su christophe
    source  /home/christophe/.virtualenv/myflqenv/bin/activate
    cd /home/christophe/.virtualenv/myflqenv/myflq/src/MyFLsite
    celery -A MyFLsite worker -l info &
    disown
    uwsgi --socket MyFLsite/myflsite.sock --module MyFLsite.wsgi --chmod-socket=666 &
    #or if using inifile => uwsgi --ini /home/christophe/.virtualenv/myflqenv/myflq/src/MyFLsite/MyFLsite/myflsite_uwsgi.ini
    disown
    deactivate

##Automatic startup

    yum install supervisor
    chkconfig supervisord on
    cat >> /etc/supervisord.conf <<EOF
        [program:uwsgi]
	command=/home/christophe/.virtualenv/myflqenv/bin/uwsgi --ini /home/christophe/.virtualenv/myflqenv/myflq/src/MyFLsite/MyFLsite/myflsite_uwsgi.ini
	priority=888
	user=christophe

	[program:celery]
	command=bash -c "source /home/christophe/.virtualenv/myflqenv/bin/activate && /home/christophe/.virtualenv/myflqenv/bin/celery -A MyFLsite worker -l info"
	numprocs=1
	directory=/home/christophe/.virtualenv/myflqenv/myflq/src/MyFLsite
	priority=999
	startsecs=10
	startretries=3
	user=christophe
	redirect_stderr=true
	stdout_logfile=/var/tmp/celery.log
    EOF

supervisord.conf still needed to be ammended with the following, as supervisorctl was not working:

    [unix_http_server]
    file=/var/tmp/supervisor.sock

    [rpcinterface:supervisor]
    supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface
