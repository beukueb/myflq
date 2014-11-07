from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from django.conf import settings

#Setup
from rmne.forms import RFormSet, RFormSet0, SettingsFileForm
from rmne.tasks import rmneTaskRequest

# Create your views here.
def calcform(request):
    rmneResultID = rmneResult = previousDO = None
    firstView = fileform = False

    if request.is_ajax():
        import os, json
        if os.path.exists(settings.MEDIA_ROOT+'rmne/'+request.GET['SESSIONID']+'/finished'):
            return HttpResponse(json.dumps({'finished':1}), 'application/json')
        else: return HttpResponse(json.dumps({'finished':0}), 'application/json')

    if not request.method == 'POST':
        formset = RFormSet()
        fileform = SettingsFileForm()
        firstView = True
        if 'SESSIONID' in request.GET:
            import pickle,os
            firstView = False
            rmneResultID = request.GET['SESSIONID']
            previousData = pickle.load(open(settings.MEDIA_ROOT+'rmne/'+
                                            rmneResultID+'/inputdata.pickle','rb'))
            previousDO = pickle.load(open(settings.MEDIA_ROOT+'rmne/'+
                                            rmneResultID+'/inputDOallowed.pickle','rb'))
            finishfile = settings.MEDIA_ROOT+'rmne/'+request.GET['SESSIONID']+'/finished'
            if os.path.exists(finishfile):
                #rmneResult = open(finishfile).read().strip()
                rmneResult = pickle.load(open(settings.MEDIA_ROOT+'rmne/'+request.GET['SESSIONID']+'/result.pickle','rb'))
            formset = RFormSet0(initial=previousData)
        
    elif request.POST['submitaction'] == 'Upload settings':
        fileform = SettingsFileForm(request.POST,request.FILES)
        if fileform.is_valid():
            #print(fileform.cleaned_data)
            formsetData = []
            for line in request.FILES['fileName'].readlines():
                line = line.decode().strip()
                if line.startswith('#'): continue
                line = line.split(',')
                formsetData.append({
                    'locus':line[0],
                    'allele':line[1],
                    'frequency':float(line[2]),
                    'observed':len(line)==4 and bool(line[3])
                })
                formset = RFormSet(initial=formsetData)
    else:
        formset = RFormSet(request.POST)
        if formset.is_valid():
            if request.POST['submitaction'] == 'Calculate':
                import os,uuid,pickle
                doAllowed = int(request.POST['dropoutsAllowed'])
                rmneResultID = uuid.uuid4().hex
                outDir = settings.MEDIA_ROOT+'rmne/'+rmneResultID+'/'
                try: os.mkdir(outDir)
                except FileNotFoundError:
                    os.system('mkdir -p '+settings.MEDIA_ROOT+'rmne')
                    os.mkdir(outDir)
                inputdata = [r for r in formset.cleaned_data if r]
                pickle.dump(inputdata,open(outDir+'inputdata.pickle','wb'))
                pickle.dump(doAllowed,open(outDir+'inputDOallowed.pickle','wb'))
                rmneTaskRequest.delay(inputdata,doAllowed,outDir)
                return HttpResponseRedirect('/rmne/?SESSIONID='+rmneResultID)
            else:
                #Alway adding 10 extra rows
                cleaned_data = [c for c in formset.cleaned_data if c]
                formset = RFormSet(initial=cleaned_data)

    return render(request,'rmne/calculation.html',{'myflq': False,
                                                   'rmneResultID': rmneResultID,
                                                   'rmneResult': rmneResult,
                                                   'firstView': firstView,
                                                   'previousDO': previousDO,
                                                   'formset': formset,
                                                   'fileform': fileform})
 


