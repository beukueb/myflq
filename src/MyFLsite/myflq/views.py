from django.shortcuts import render
from django.http import HttpResponse #,HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.conf import settings

# Create your views here.

#Setup
from myflq.models import UserResources,Primer
from myflq.forms import ConfigurationForm

import os, subprocess

@login_required
def setup(request):
    #Testing parameter for bounded/unbounded forms
    configForm = configFilesError = None
    
    if request.method == 'POST':
        if request.POST['submitaction'] == 'createconfig':
            configform = ConfigurationForm(request.POST,request.FILES)
            if configform.is_valid():
                configform.instance.user = request.user
                command = ['python3',os.path.join(settings.BASE_DIR,'../MyFLdb.py'), 
                           '-p',request.user.password,configform.instance.dbusername(),configform.instance.fulldbname()]
                subprocess.check_call(command)#,  shell=True)
                configform.save() #Should only get saved if subprocess runs without errors
                try:
                    subprocess.check_output(['python3',
                                             os.path.join(settings.BASE_DIR,'../MyFLq.py'),
                                             '-p',configform.instance.user.password, 'add',
                                             '-k',configform.instance.lociFile.file.name,
                                             '-a',configform.instance.alleleFile.file.name,
                                             configform.instance.dbusername(),
                                             configform.instance.fulldbname(),
                                             'default'],stderr=subprocess.STDOUT)
                    process_primerfile(request.FILES['lociFile'],dbname=configform.instance)
                except subprocess.CalledProcessError as e:
                    #Clean up database if commiting configuration did not work
                    subprocess.call(['python3',os.path.join(settings.BASE_DIR,'../MyFLdb.py'),
                                     '-p',request.user.password,'--delete',configform.instance.dbusername(),
                                     configform.instance.fulldbname()])
                    #Clean up UserResource
                    os.remove(configform.instance.lociFile.file.name)
                    os.remove(configform.instance.alleleFile.file.name)
                    UserResources.objects.get(id=configform.instance.id).delete()
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

    userdbs = UserResources.objects.filter(user=request.user)
    if not configForm: configForm = ConfigurationForm()

    return render(request,'myflq/setup.html',{'myflq':True,
                                              'userdbs':userdbs,
                                              'configForm':configForm,
                                              'configFilesError':configFilesError})

##Further functions for processing setup view
def process_primerfile(requestfile,dbname):
    for line in requestfile.readlines():
        if line.decode().strip().startswith('#'): continue
        line = line.decode().strip().split(',')
        primer = Primer(dbname = dbname,
                        locusName = line[0],
                        locusType = None if line[1] == 'SNP' else line[1],
                        forwardPrimer = line[2],
                        reversePrimer = line[3])
        primer.save()

#Analysis
from myflq.forms import analysisform_factory
from myflq.models import Analysis
from myflq.tasks import myflqTaskRequest #import tasks

@login_required
def analysis(request):
    #add.delay(2,3) #debug tasks
    #User specific Form(Set)s/processes queud/running
    AnalysisForm = analysisform_factory(UserResources.objects.filter(user=request.user),Analysis.objects.filter(dbname__user=request.user))
    processes = Analysis.objects.filter(dbname__user=request.user).exclude(progress__contains='F')
    
    #Process AJAX
    if request.is_ajax():
        for p in processes: #Change progress code for human readible value
            p.progress = p.get_progress_display()
        from django.core import serializers
        data = serializers.serialize("json", processes, fields=('progress',)) #Only progress field required. pk automatically added
        return HttpResponse(data, mimetype='application/json') 
    
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
    #User specific Form(Set)s
    
    if request.method == 'POST':
        analysis = Analysis.objects.get(pk=request.POST['viewResult'])
    else: analysis = False
    
    return render(request,'myflq/results.html',{'myflq':True,
                                                'analysis':analysis,
                                                'processes':Analysis.objects.filter(dbname__user=request.user).filter(progress__contains='F')})
     
 
 
 
 
 
 
