#from __future__ import absolute_import
from celery import shared_task
#from celery.contrib import rdb #DEBUG

@shared_task
def validateDOI(doi,userName):
    """
    Checks if a username is an author in a doi-linked pubblication 
    """
    #Check if active doi
    from urllib import request
    url = 'http://dx.doi.org/{doi}'.format(doi=doi)
    #If original browser link is needed, add user_Agent to headers
    #user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    headers = {'Accept':'application/rdf+xml'}
              #'User-Agent':user_agent,
              #'Accept':'text/turtle' => would then require rdflib for parsing
    req = request.Request(url, headers = headers)
    try: response = request.urlopen(req)
    except request.HTTPError: return None #doi not valid
    
    #Check if user is author of the referenced pubblication
    import xml.etree.ElementTree as ET
    root = ET.fromstring(response.read())
    root = root.getchildren()[0]
    namespaces={'j.2':'http://purl.org/dc/terms/',
                'j.1':'http://xmlns.com/foaf/0.1/'}
    try:
        for c in root.findall('j.2:creator',namespaces=namespaces):
            name = c.find('j.1:Person/j.1:name',namespaces=namespaces)
            name = name.text
            if name == userName:
                raise StopIteration
            return False #user not an author
    except StopIteration:
        #user is author
        return True    

@shared_task
def backup():
    """
    Makes a backup of FLAD, consisting out of FLADid,sequence lines
    Celery beat has to be active to make this a weekly job with djcelery in the admin settings
    In the site root dir, run:
      $ celery beat -A MyFLsite -S djcelery.schedulers.DatabaseScheduler
    TODO: add to supervisor config
    """
    from django.conf import settings
    from flad.models import Allele
    import subprocess,tempfile,os
    from datetime import datetime

    #rdb.set_trace() #DEBUG => telnet 127.0.0.1 portnumber
    
    try:
        backupfile = settings.STATIC_ROOT + 'FLAD/' + settings.FLAD_BACKUPFILE
    except AttributeError:
        raise Exception("Define FLAD_BACKUPFILE='/path/to/file' in settings.py")

    #Rename previous backup
    #TODO consider also renaming sha256
    try: os.rename(backupfile+'.tar.gz',backupfile+datetime.now().strftime('_%H_%M_%d_%m_%Y.tar.gz'))
    except FileNotFoundError:
        print('FLADbackup file not found. This is normal for the first backup event.')

    tempcsv = tempfile.NamedTemporaryFile(delete=False,suffix='.csv',mode='wt')
    for a in Allele.objects.all():
        tempcsv.write('{},{}\n'.format(a.fladid(),a.sequence))
    tempcsv.close()

    subprocess.check_call(['tar','-czf',backupfile+'.tar.gz',tempcsv.name])
    subprocess.check_call(['sudo','/usr/bin/openssl','dgst','-sha256','-sign','/etc/ssl/private/forensic.ugent.be.key',
                           '-out',backupfile+'.sha256',backupfile+'.tar.gz'])
    #With visudo, enable exact execution of above command on server
    #Cmnd_Alias FLADBACKUP = /usr/bin/openssl dgst -sha256 -sign /etc/ssl/private/forensic.ugent.be.key -out /home/christophe/.virtualenv/myflqenv/static/FLAD/FLADbackup.sha256 /home/christophe/.virtualenv/myflqenv/static/FLAD/FLADbackup.tar.gz
    #christophe  ALL=NOPASSWD: FLADBACKUP
    
    #To allow verify, pub key is needed with following commands on the server from ipython django shell
    #from django.conf import settings
    #!mkdir {settings.STATIC_ROOT}FLAD
    #!openssl x509 -in /etc/ssl/certificates/forensic.ugent.be.pem -pubkey -noout > {settings.STATIC_ROOT}FLAD/forensic.ugent.be.pub

    #After downloading forensic.ugent.be.pub and FLADbackup.sha256 a user can verify FLADbackup with the following command
    #openssl dgst -sha256 -verify forensic.ugent.be.pub -signature FLADbackup.sha256 FLADbackup
    
    os.remove(tempcsv.name)
    return 'Backup completed'
