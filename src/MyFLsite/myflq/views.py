from django.shortcuts import render
from django.http import HttpResponse #,HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.conf import settings

# Create your views here.

#Setup
from myflq.models import UserResources,Primer
from myflq.forms import primerformset_factory, primerfileform_factory, \
                        allelefileform_factory, databaseselectionform_factory

import os, subprocess

@login_required
def setup(request):
    #User specific Form(Set)s
    PrimerFormSet = primerformset_factory(UserResources.objects.filter(user=request.user))
    PrimerFileForm = primerfileform_factory(UserResources.objects.filter(user=request.user))
    AlleleFileForm = allelefileform_factory(UserResources.objects.filter(user=request.user))
    DatabaseSelectionForm = databaseselectionform_factory(UserResources.objects.filter(user=request.user))
    
    #Testing parameter for bounded/unbounded forms
    newprimerform = newprimerfileform = newallelefileform = newdatabaseselectionform = True
    
    if request.method == 'POST':
        if request.POST['submitaction'] == 'createdb':
            #For the databasename user and dbname are combined so that different users can use same dbname
            userdb = UserResources(user=request.user,dbname=request.POST['dbname'])
            command = ['python3',os.path.join(settings.BASE_DIR,'../MyFLdb.py'), 
                            '-p',request.user.password,userdb.dbusername(),userdb.fulldbname()]
            failed = subprocess.call(command)#,  shell=True)          
            if not failed: userdb.save() #Should only get saved if subprocess runs without errors
            else:
                raise Exception('Failed:'+' '.join(command))

        elif request.POST['submitaction'] == 'deletedb':
            userdb = UserResources.objects.get(dbname=request.POST['dbname'],user=request.user)
            subprocess.call(['python3',os.path.join(settings.BASE_DIR,'../MyFLdb.py'),
                            '-p',request.user.password,'--delete',userdb.dbusername(),userdb.fulldbname()]) 
            userdb.delete()

        elif request.POST['submitaction'] == 'addlocifile':
            primerfileform = PrimerFileForm(request.POST,request.FILES)
            if primerfileform.is_valid():
                process_primerfile(request.FILES['fileName'],dbname=primerfileform.cleaned_data['dbname'])
            else: newprimerfileform = False

        elif request.POST['submitaction'] == 'addlocus':
            primerFormSet = PrimerFormSet(request.POST)
            if primerFormSet.is_valid():
                primerFormSet.save()
            else: newprimerform = False
        
        elif request.POST['submitaction'] == 'addallelesfile':
            allelefileform = AlleleFileForm(request.POST,request.FILES)
            if allelefileform.is_valid():
                allelefileform.save()
            else: newallelefileform = False

        elif request.POST['submitaction'] == 'commitdb':
            databaseselectionform = DatabaseSelectionForm(request.POST)
            if databaseselectionform.is_valid():
                process_commitdb(databaseselectionform.cleaned_data.get('dbname'))
            else: newdatabaseselectionform = False
                            
    userdbs = UserResources.objects.filter(user=request.user)
    if newprimerform: primerFormSet = PrimerFormSet(queryset=Primer.objects.filter(dbname__user=request.user).order_by('dbname','locusName'))
                                                                        #queryset=Primer.objects.none())    #queryset=Primer.objects.filter
    if newprimerfileform: primerfileform = PrimerFileForm()
    if newallelefileform: allelefileform = AlleleFileForm()
    if newdatabaseselectionform: databaseselectionform = DatabaseSelectionForm()
    return render(request,'myflq/setup.html',{'myflq':True,'userdbs':userdbs,
                                                           'primerset':primerFormSet,
                                                           'primerfileform':primerfileform,
                                                           'allelefileform':allelefileform,
                                                           'databaseselectionform':databaseselectionform})
    

##Further functions for processing setup view
def process_primerfile(requestfile,dbname):
    for line in requestfile.readlines():
        line = line.decode().strip().split(',')
        primer = Primer(dbname = dbname,
                        locusName = line[0],
                        locusType = None if line[1] == 'SNP' else line[1],
                        forwardPrimer = line[2],
                        reversePrimer = line[3])
        primer.save()

def process_commitdb(dbname):
    #Prepare primers for commit
    import tempfile,os
    primerscsv = tempfile.NamedTemporaryFile(mode='wt',delete=False)
    for value in Primer.objects.filter(dbname=dbname).values():
        primerscsv.write(value['locusName']+','+(str(value['locusType']) if value['locusType'] else 'SNP')+
                         ','+value['forwardPrimer']+','+value['reversePrimer']+'\n')
    primerscsv.close()
    subprocess.check_call(['python3',os.path.join(settings.BASE_DIR,'../MyFLq.py'), '-p', dbname.user.password, 'add', '-k', primerscsv.name,
                    '-a',dbname.allelefiles.alleleFile.file.name, dbname.dbusername(), dbname.fulldbname(), 'default'])
    
    dbname.isAlreadyCommitted = True
    dbname.save()
    os.remove(primerscsv.name)


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
     
 
 
 
 
 
 
