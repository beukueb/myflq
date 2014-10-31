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

    command = ['python3','../MyFLq.py', '-p', analysis.dbname.user.password, 
                                   'analysis', '--negativeReadsFilter', int(analysis.negativeReadsFilter),
                                   '--primerBuffer', str(analysis.primerBuffer), '--flankOut', int(analysis.flankOut),
                                   '--stutterBuffer', str(analysis.stutterBuffer), '--useCompress', int(analysis.useCompress),
                                   '--withAlignment', int(analysis.withAlignment), '--threshold', str(analysis.threshold),
                                   '--clusterInfo', str(analysis.clusterInfo), '--randomSubset', str(analysis.randomSubset),
                                   '-r',tempxml.name,'-s', settings.STATIC_URL+'css/resultMyFLq.xsl','-v',tempfigure.name,
                                   analysis.fastq.file.name, analysis.dbname.dbusername(), 
                                   analysis.dbname.fulldbname(), 'default']
    if not analysis.randomSubset:
        command.pop(command.index('--randomSubset')+1)
        command.pop(command.index('--randomSubset'))
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
    import os
    os.remove(tempxml.name), os.remove(tempfigure.name)

    return 'Executed:\n'+' '.join(command)+'\nStatus: '+str(failed)
