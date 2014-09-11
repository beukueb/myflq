# MyFLq container dockerfile
#
# VERSION 1.0
# Execute with: docker build myflq.build

FROM ubuntu:14.04
MAINTAINER Christophe Van Neste, christophe.vanneste@ugent.be

#Prepare
RUN apt-get update

#Set up database
RUN echo 'mysql-server mysql-server/root_password password root' | debconf-set-selections && \
    echo 'mysql-server mysql-server/root_password_again password root' | debconf-set-selections && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install mysql-server
#RUN sed -i -e"s/^bind-address\s*=\s*127.0.0.1/bind-address = 0.0.0.0/" /etc/mysql/my.cnf #Will make it listen on any port to make it available outside of the container
EXPOSE 3306

RUN apt-get install -y supervisor #managing container services
RUN apt-get -y install expect
RUN apt-get -y install python3 python3-setuptools
RUN apt-get install -y git libmysqlclient-dev python3-dev
RUN apt-get install -y ipython3 python3-numpy
RUN easy_install3 pymysql
#Matplotlib dependencies => this section of the buildfile can break easily
RUN apt-get install -y g++ libfreetype6-dev libpng-dev
RUN easy_install3 python-dateutil six
RUN easy_install3 -U distribute
RUN apt-get install -y python3-matplotlib
#RUN apt-get build-dep -y python-matplotlib
#RUN easy_install3 -m matplotlib
RUN easy_install3 matplotlib

#Saxon => XSLT output
RUN apt-get install -y openjdk-7-jre-headless
RUN apt-get install -y libsaxonb-java
#Previously needed the following workaround to get java running
#after that section you could not use apt-get install any more due to dependencies issues from dpkg strategy
#RUN mkdir /tmp/saxon && cd /tmp/saxon && apt-get download openjdk-7-jre-headless openjdk-7-jre && dpkg --force-all -i /tmp/saxon/* && rm /tmp/saxon/* && rmdir /tmp/saxon

#MyFLsite dependencies
RUN easy_install3 django celery Pillow
RUN apt-get install -y rabbitmq-server
RUN cd /tmp && git clone https://github.com/clelland/MySQL-for-Python-3.git && \
    cd MySQL-for-Python-3/ && \
    python3 setup.py build && \
    python3 setup.py install

#Supervisor config
RUN mkdir -p /var/log/supervisor
ADD ./src/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

#Sending program files
#The files must be within the buildfile dir or below
RUN mkdir /myflq
#Add dir containing all needed files
ADD src/ /myflq

#One file example
#ADD ./MyFLq.py /myflq/

#Programs
##Main entry for basebase
ENTRYPOINT ["/myflq/basespace/myflq_wrapper.sh"]
#Wih this entrypoint configuration, you can run the container as a program
#All extra parameters to docker run will be passed as arguments to the entry
#This does not work with: ENTRYPOINT /myflq/basespace/myflq_wrapper.sh

##Easy links for other container contexts
RUN ln -s /myflq/MyFLsite/startApp.sh /bin/webapp && \
    ln -s /myflq/basespace/myflq_wrapper.sh /bin/basespace

# USER myflquser #if program needs to run as specific user

#Expose the standard django runserver port to the container
EXPOSE 8000
