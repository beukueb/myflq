#from __future__ import absolute_import
from celery import shared_task
#from celery.contrib import rdb #DEBUG

@shared_task
def myflqTaskRequest(analysisID):
    from django.conf import settings
    from myflq.models import Analysis,AnalysisResults
    from django.core.files import File
    import subprocess,time,tempfile

    #rdb.set_trace() #DEBUG => telnet 127.0.0.1 portnumber

    analysis = Analysis.objects.get(id=analysisID)
    analysis.progress = 'P'
    analysis.save()
    tempfigure = tempfile.NamedTemporaryFile(delete=False,suffix='.png')
    tempxml = tempfile.NamedTemporaryFile(delete=False,suffix='.xml')
    tempfigure.close(), tempxml.close() #Only their filenames need to be passed to the subprocess

    command = ['python3','../MyFLq.py', '-p', analysis.configuration.user.password, 
               'analysis', '--sampleName', analysis.originalFilename,
               '--negativeReadsFilter' if analysis.negativeReadsFilter else 'REMOVE',
               '--primerBuffer', str(analysis.primerBuffer),
               '--kMerAssign' if analysis.kMerAssign else 'REMOVE',
               str(analysis.kMerAssign) if analysis.kMerAssign else 'REMOVE',
               '--flankOut' if analysis.flankOut else 'REMOVE',
               '--stutterBuffer', str(analysis.stutterBuffer),
               '--useCompress' if analysis.useCompress else 'REMOVE',
               '--withAlignment' if analysis.withAlignment else 'REMOVE',
               '--threshold', str(analysis.threshold),
               '--clusterInfo' if analysis.clusterInfo else 'REMOVE',
               '--randomSubset' if analysis.randomSubset else 'REMOVE',
               str(analysis.randomSubset) if analysis.randomSubset else 'REMOVE',
               '-r',tempxml.name,'-s', settings.STATIC_URL+'css/resultMyFLq.xsl','-v',tempfigure.name,
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

    print('Command:\n',' '.join(command))
    return 'Executed:\n'+' '.join(command)

@shared_task
def alleleTaskRequest(sequence):
    """
    Retrieves the sequence identifier on ENA.
    Submits an entry if not already available.
    """
    from urllib.request import urlopen
    from time import sleep
    #urlopen("http://www.ebi.ac.uk/ena/search/showQueryCollections?type=exact") #DEBUG see collection ids
    #  20	Human	-----Human (EMBL-Bank)
    
    #Submit search for sequence #TODO make work with &type=exact => mail ENA
    response = urlopen('http://www.ebi.ac.uk/ena/search/executeSearch?Sequence={seq}&collection_id=20'.format(seq=sequence))
    response = response.read().decode().strip()
    
    #Wait for result completion
    status = urlopen(response).read().decode()
    while not status.startswith('COMPLETE'):
        sleep(30)
        status = urlopen(response).read().decode()
    totalResults = int(status.strip().split('\t')[-1])

    #See if there is a full identity match (check first only 10 results)
    resultsQuery = response.replace('Status','Results')+'&fields=accession,identity,e_value&offset={offset}&length=10'
    for i in range(0,totalResults,10):
        results = urlopen(resultsQuery.format(offset=i))
        results = response.read().decode().strip()
        if '\t100\t' in results: break

    if '\t100\t' in results:
        for result in results.split('\r\n'):
            result = result.split('\t')
            if result[1] == '100': return result[0] #result[0] is the accession id

    #If not returned then sequence has to be submitted
    enasubmit = 'https://www-test.ebi.ac.uk/ena/submit/drop-box/submit/'
      #https://www.ebi.ac.uk/ena/submit/drop-box/submit/ #TODO for production


    
