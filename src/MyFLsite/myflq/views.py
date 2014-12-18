from django.shortcuts import render
from django.http import HttpResponse #,HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils.safestring import mark_safe

# Loggin
import logging
logger = logging.getLogger(__name__)

# Create your views here.
#Setup
from myflq.models import UserResources,Locus,Allele,FLADconfig
from myflq.forms import ConfigurationForm,FLADconfigForm

import os, subprocess

@login_required
def setup(request):
    #Testing parameter for bounded/unbounded forms
    configForm = configFilesError = None

    try: fladuser = FLADconfig.objects.get(user=request.user)
    except: fladuser = None
    fladconfigform = FLADconfigForm(instance=fladuser)
    
    if request.method == 'POST':
        if request.POST['submitaction'] == 'createconfig':
            configform = ConfigurationForm(request.POST,request.FILES)
            if configform.is_valid():
                configform.instance.user = request.user
                configform.save() #Should be deleted if try block encounters errors
                config = configform.instance
                try:
                    process_config(config)
                except subprocess.CalledProcessError as e:
                    #Clean up database if commiting configuration did not work
                    subprocess.call(['python3',os.path.join(settings.BASE_DIR,'../MyFLdb.py'),
                                     '-p',request.user.password,'--delete',config.dbusername(),
                                     config.fulldbname()]) #No error raised if database not created
                    #Clean up UserResource
                    os.remove(config.lociFile.file.name)
                    if config.alleleFile: os.remove(config.alleleFile.file.name)
                    UserResources.objects.get(id=config.id).delete()
                    #Retrieve error for user
                    from django.utils import html
                    configFilesError = mark_safe('<span style="color:red;">'+
                                       html.escape(e.output.decode())+'</span>')
                except NotImplementedError as e:
                    config.delete()
                    configFilesError = e.args[0]
                    logger.error(e.args[0])
            else:
                configForm = configform
                

        elif request.POST['submitaction'] == 'deletedb':
            userdb = UserResources.objects.get(dbname=request.POST['dbname'],user=request.user)
            subprocess.call(['python3',os.path.join(settings.BASE_DIR,'../MyFLdb.py'),
                            '-p',request.user.password,'--delete',userdb.dbusername(),userdb.fulldbname()]) 
            userdb.delete()

        elif request.POST['submitaction'] == 'setFLAD':
            fladconfigform = FLADconfigForm(request.POST)
            if fladconfigform.is_valid():
                fladconfigform.instance.user = request.user
                if fladuser: fladconfigform.instance.id = fladuser.id
                fladconfigform.save()

    userdbs = UserResources.objects.filter(user=request.user)
    if not configForm: configForm = ConfigurationForm()

    return render(request,'myflq/setup.html',{'myflq':True,
                                              'userdbs':userdbs,
                                              'fladconfigform': fladconfigform,
                                              'configForm':configForm,
                                              'configFilesError':configFilesError})

##Further functions for processing setup view
def process_config(config):
    #Imports
    import tempfile
    from django.core.files.base import File

    #Process loci
    for line in open(config.lociFile.file.name):
        if line.strip().startswith('#'): continue
        line = line.strip().split(',')
        lenline = len(line)
        if lenline == 4:
            raise NotImplementedError("Loci config file V1.0 not yet reimplemented. Contact us and we will activate it.")
        locus = Locus(configuration = config,
                      name = line[0],
                      locusType = None if line[1] == 'SNP' else line[1],
                      forwardPrimer = line[2].upper(),
                      reversePrimer = line[3].upper(),
                      refnumber = line[4] if lenline >= 6 and line[1] != 'SNP' else None,
                      refsequence = line[5].upper() if lenline >= 6 else None,
                      refmask = line[6].upper() if lenline == 7 else None
                  )
        locus.save()

    #Process alleles
    ##If no initial allele file, make one based on lociFile version 2
    if not config.alleleFile:
        alleleFile = tempfile.NamedTemporaryFile(delete=False,suffix='.csv')
        for line in open(config.lociFile.file.name):
            line = line.strip().split(',')
            alleleFile.file.write('{},{},{}\n'.format(
                line[0],line[4],line[5]).encode())
        alleleFile.close()
        config.alleleFile = File(open(alleleFile.name))
        config.save()

    ##Add alleles to MyFLsite db and retrieve FLADids
    for line in open(config.alleleFile.file.name):
        if line.strip().startswith('#'): continue
        line = line.strip().split(',')
        allele = Allele(configuration = config,
                        locus = Locus.objects.get(name=line[0],
                                                  configuration=config),
                        name = line[1],
                        FLADid = getFLAD(line[2],config.user),
                        #repeatNumber => not implemented for now
                        sequence = line[2].upper())
        allele.save()

    ##Save new allele config file with FLADids for MyFLq
    alleleFile = tempfile.NamedTemporaryFile(delete=False,suffix='.csv')
    for a in Allele.objects.filter(configuration=config):
        alleleFile.file.write('{},{},{}\n'.format(
            a.locus.name,a.FLADid,a.sequence).encode())
    alleleFile.close()
    config.alleleFile = File(open(alleleFile.name))
    config.save()

    #Make database for user
    subprocess.check_output(['python3',
                             os.path.join(settings.BASE_DIR,'../MyFLdb.py'), 
                             '-p',config.user.password,config.dbusername(),
                             config.fulldbname()],stderr=subprocess.STDOUT)

    #Validate and save config for MyFLq
    subprocess.check_output(['python3',
                             os.path.join(settings.BASE_DIR,'../MyFLq.py'),
                             '-p',config.user.password, 'add',
                             '-k',config.lociFile.file.name,
                             '-a',config.alleleFile.file.name,
                             config.dbusername(),
                             config.fulldbname(),
                             'default'],stderr=subprocess.STDOUT)

def getFLAD(sequence,user):
    from urllib.request import urlopen
    from django.utils.http import urlquote
    url = 'https://{flad}/flad/validate/plain/{seq}?user={u}&password={p}'
    provider = user.fladconfig.FLAD
    if provider == "localhost" or provider.startswith("localhost:"):
        url = url.replace('https://','http://')
    response = urlopen(
        url.format(
            flad=user.fladconfig.FLAD,
            seq=sequence,
            u=urlquote(user.fladconfig.FLADname),
            p=urlquote(user.fladconfig.FLADkey)))
    return response.read().decode()
    
#Analysis
from myflq.forms import analysisform_factory
from myflq.models import Analysis
from myflq.tasks import myflqTaskRequest #import tasks

@login_required
def analysis(request):
    #add.delay(2,3) #debug tasks
    #User specific Form(Set)s/processes queud/running
    AnalysisForm = analysisform_factory(UserResources.objects.filter(user=request.user),
                                        Analysis.objects.filter(configuration__user=request.user))
    processes = Analysis.objects.filter(configuration__user=request.user).exclude(progress__contains='F')
    
    #Process AJAX
    if request.is_ajax():
        for p in processes: #Change progress code for human readible value
            p.progress = p.get_progress_display()
        from django.core import serializers
        data = serializers.serialize("json", processes, fields=('progress',)) #Only progress field required. pk automatically added
        return HttpResponse(data, 'application/json')
            #mimetype error in django 1.7 => in django < 1.6 mimetype='application/json'
            #                                in django 1.7   content_type='application/json'
            #                 temporary solution that works in all django => do not mention keyword
    
    #Testing parameter for bounded/unbounded forms
    newanalysisform = True
    
    if request.method == 'POST':
        if request.POST['submitaction'] == 'analysisform':
            analysisform = AnalysisForm(request.POST,request.FILES)
            if analysisform.is_valid():
                analysismodel = analysisform.save(commit=False)
                if analysisform.cleaned_data.get('originalFilename',False):
                    analysismodel.originalFilename =  analysisform.cleaned_data['originalFilename']
                analysismodel.save()
                myflqTaskRequest.delay(analysismodel.id)

            else: newanalysisform = False
    if newanalysisform: analysisform = AnalysisForm()
    return render(request,'myflq/analysis.html',{'myflq':True,
                                                 'analysisform':analysisform,
                                                 'processes':processes})
 
 
@login_required
def results(request):
    #TODO search options/page functionality for users with many results

    #User specific Form(Set)s
    return render(request,'myflq/results.html',
                  {'myflq':True,
                   'processes': Analysis.objects.filter(configuration__user=request.user
                                                    ).filter(progress__contains='F')})

@login_required
def result(request):
    #User requeste result
    
    if request.method == 'POST':
        analysis = Analysis.objects.get(pk=request.POST['viewResult'])
        return render(request,'myflq/result.html',
                      {'myflq':True,
                       'analysis':analysis})


     
 
 
 
 
 
 
