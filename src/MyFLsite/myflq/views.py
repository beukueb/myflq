from django.shortcuts import render
from django.http import HttpResponse #,HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.conf import settings

# Create your views here.

#Setup
from myflq.models import UserResources,Locus,FLADconfig
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
                command = ['python3',os.path.join(settings.BASE_DIR,'../MyFLdb.py'), 
                           '-p',request.user.password,configform.instance.dbusername(),configform.instance.fulldbname()]
                subprocess.check_call(command)#,  shell=True)
                configform.save() #Should be deleted if try block encounters errors
                config = configform.instance
                try:
                    process_config(request.FILES['lociFile'],config=config)
                except subprocess.CalledProcessError as e:
                    #Clean up database if commiting configuration did not work
                    subprocess.call(['python3',os.path.join(settings.BASE_DIR,'../MyFLdb.py'),
                                     '-p',request.user.password,'--delete',config.dbusername(),
                                     config.fulldbname()])
                    #Clean up UserResource
                    os.remove(config.lociFile.file.name)
                    if config.alleleFile: os.remove(config.alleleFile.file.name)
                    UserResources.objects.get(id=config.id).delete()
                    #Retrieve error for user
                    from django.utils import html
                    configFilesError = html.escape(e.output.decode())
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
def process_config(locifile,config):
    for line in locifile.readlines():
        if line.decode().strip().startswith('#'): continue
        line = line.decode().strip().split(',')
        lenline = len(line)
        locus = Locus(configuration = config,
                      locusName = line[0],
                      locusType = None if line[1] == 'SNP' else line[1],
                      forwardPrimer = line[2],
                      reversePrimer = line[3],
                      refnumber = line[4] if lenline >= 6 and line[1] == 'SNP' else None,
                      refsequence = line[5] if lenline >= 6 else None,
                      refmask = line[6] if lenline == 7 else None
                  )
        locus.save()

    if not config.alleleFile:
        import tempfile
        from django.core.files.base import File
        alleleFile = tempfile.NamedTemporaryFile(delete=False,suffix='.csv')
        for line in open(config.lociFile.file.name):
            line = line.strip().split(',')
            alleleFile.file.write('{},{},{}\n'.format(line[0],line[4],line[5]).encode())
        alleleFile.close()
        config.alleleFile = File(open(alleleFile.name))
        config.save()

    #Validate and save config for MyFLq
    subprocess.check_output(['python3',
                             os.path.join(settings.BASE_DIR,'../MyFLq.py'),
                             '-p',config.user.password, 'add',
                             '-k',config.lociFile.file.name,
                             '-a',config.alleleFile.file.name,
                             config.dbusername(),
                             config.fulldbname(),
                             'default'],stderr=subprocess.STDOUT)

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


     
 
 
 
 
 
 
