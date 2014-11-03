#from __future__ import absolute_import
from celery import shared_task

#Example
#@shared_task
#def add(x, y):
#    return x + y

@shared_task
def myflqTaskRequest(analysisID):
    from django.conf import settings
    from myflq.models import Analysis,AnalysisResults
    from django.core.files import File
    import subprocess,time,tempfile

    analysis = Analysis.objects.get(id=analysisID)
    analysis.progress = 'P'
    analysis.save()
    tempfigure = tempfile.NamedTemporaryFile(delete=False,suffix='.png')
    tempxml = tempfile.NamedTemporaryFile(delete=False,suffix='.xml')
    tempfigure.close(), tempxml.close() #Only their filenames need to be passed to the subprocess

    command = ['python3','../MyFLq.py', '-p', analysis.configuration.user.password, 
               'analysis', '--negativeReadsFilter' if analysis.negativeReadsFilter else 'REMOVE'
               '--primerBuffer', str(analysis.primerBuffer),
               '--flankOut' if analysis.flankOut else 'REMOVE',
               '--stutterBuffer', str(analysis.stutterBuffer),
               '--useCompress' if analysis.useCompress else 'REMOVE',
               '--withAlignment' if analysis.withAlignment else 'REMOVE',
               '--threshold', str(analysis.threshold),
               '--clusterInfo' if analysis.clusterInfo else 'REMOVE',
               '--randomSubset' if analysis.randomSubset else 'REMOVE',
               str(analysis.randomSubset) if analysis.randomSubset else 'REMOVE',
               '-r',tempxml.name,'-s', settings.STATIC_URL+'css/resultMyFLq.xsl','-v',tempfigure
               analysis.fastq.file.name, analysis.configuration.dbusername(), 
               analysis.configuration.fulldbname(), 'default']
    while 'REMOVE' in command: command.remove('REMOVE')

    try:
        subprocess.check_output(command,stderr=subprocess.STDOUT)
        analysisResult = AnalysisResults(analysis=analysis)
        analysisResult.xmlFile.save(tempxml.name,File(open(tempxml.name)))
        analysisResult.figFile.save(tempfigure.name,File(open(tempfigure.name,'rb')))
        analysisResult.save()
        analysis.progress = 'F'
        analysis.save()
    except subprocess.CalledProcessError as e:
        analysis.progress = 'FA'
        analysis.save()
        print('FAILURE:',e.output.decode())
    import os
    os.remove(tempxml.name), os.remove(tempfigure.name)

    return 'Executed:\n'+' '.join(command)
