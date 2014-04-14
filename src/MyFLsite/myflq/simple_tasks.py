#Should be started with python3 as a daemon, from the MyFLsite root directory
#(in order to import everything from the site as needed)
#This is a simple task manager, processes the tasks on one processor one after the other.
#For more complex processing use celery.

#This file queries the Analysis table to see if any analysis requests need to be processed
#If nothing needs processing it checks each minute

import os,sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'MyFLsite.settings'
sys.path.append('.')
from django.conf import settings

#In future this will be sufficient
#import django
#django.setup()

from django.core.files import File
from myflq.models import Analysis,AnalysisResults
import subprocess,time,tempfile

while True:
    queryset=Analysis.objects.filter(progress='Q')
    for analysis in queryset:
        analysis.progress = 'P'
        analysis.save()
        tempfigure = tempfile.NamedTemporaryFile(delete=False,suffix='.png')
        tempxml = tempfile.NamedTemporaryFile(delete=False,suffix='.xml')
        tempfigure.close(), tempxml.close() #Only their filenames need to be passed to the subprocess
        command = ['python3','../MyFLq.py', '-p', analysis.dbname.user.password, 
                                   'analysis', '--negativeReadsFilter', str(analysis.negativeReadsFilter),
                                   '--primerBuffer', str(analysis.primerBuffer), '--flankOut', str(analysis.flankOut),
                                   '--stutterBuffer', str(analysis.stutterBuffer), '--useCompress', str(analysis.useCompress),
                                   '--withAlignment', str(analysis.withAlignment), '--threshold', str(analysis.threshold),
                                   '--clusterInfo', str(analysis.clusterInfo), '--randomSubset', str(analysis.randomSubset),
                                   '-r',tempxml.name,'-s', settings.STATIC_URL+'css/results.css','-v',tempfigure.name,
                                   '--parallelProcessing','0', analysis.fastq.file.name, analysis.dbname.dbusername(), 
                                   analysis.dbname.fulldbname(), 'default']
        if not analysis.randomSubset:
            command.pop(command.index('--randomSubset')+1)
            command.pop(command.index('--randomSubset'))
        print('Executing:\n',' '.join(command)) #DEBUG# Comment out for production site
        failed = subprocess.call(command)
        if not failed:
            analysisResult = AnalysisResults(analysis=analysis)
            analysisResult.xmlFile.save(tempxml.name,File(open(tempxml.name)))
            analysisResult.figFile.save(tempfigure.name,File(open(tempfigure.name,'rb')))
            analysisResult.save()
            analysis.progress = 'F'
            analysis.save()
        else:
            analysis.progress = 'FA'
            analysis.save()
        os.remove(tempxml.name), os.remove(tempfigure.name)
    print('Waiting for new analysis requests')
    time.sleep(60)
    

#For future
#from celery import Celery
#
#app = Celery('tasks', broker='django://guest@localhost//')
#
#@app.task
#def add(x, y):
#    return x + y
