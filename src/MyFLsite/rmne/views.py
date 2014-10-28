from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from django.conf import settings

#Setup
from rmne.forms import RFormSet, SettingsFileForm
from rmne.tasks import rmneTaskRequest

# Create your views here.
def calcform(request):
    rmneResultID = rmneResult = None
    firstView = fileform = False

    if request.is_ajax():
        import os, json
        if os.path.exists(settings.MEDIA_ROOT+'rmne/'+request.GET['SESSIONID']+'/finished'):
            return HttpResponse(json.dumps({'finished':1}), mimetype='application/json')
        else: return HttpResponse(json.dumps({'finished':0}), mimetype='application/json')

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
            finishfile = settings.MEDIA_ROOT+'rmne/'+request.GET['SESSIONID']+'/finished'
            if os.path.exists(finishfile):
                rmneResult = open(finishfile).read().strip()
            formset = RFormSet(initial=previousData)
        
    elif request.POST['submitaction'] == 'Upload settings':
        fileform = SettingsFileForm(request.POST,request.FILES)
        if fileform.is_valid():
            #print(fileform.cleaned_data)
            formsetData = []
            for line in request.FILES['fileName'].readlines():
                line = line.decode().strip().split(',')
                formsetData.append({
                    'locus':line[0],
                    'allele':line[1],
                    'frequency':float(line[2]),
                    'observed':len(line)==4
                })
                formset = RFormSet(initial=formsetData)
    else:
        formset = RFormSet(request.POST)
        if formset.is_valid():
            if request.POST['submitaction'] == 'Calculate':
                import os,uuid,pickle
                rmneResultID = uuid.uuid4().hex
                outDir = settings.MEDIA_ROOT+'rmne/'+rmneResultID+'/'
                try: os.mkdir(outDir)
                except FileNotFoundError:
                    os.system('mkdir -p '+settings.MEDIA_ROOT+'rmne')
                    os.mkdir(outDir)
                pickle.dump(formset.cleaned_data,open(outDir+'inputdata.pickle','wb'))
                rmneTaskRequest.delay(formset.cleaned_data,outDir)
                return HttpResponseRedirect('/rmne/?SESSIONID='+rmneResultID)
            else:
                #Alway adding 10 extra rows
                cleaned_data = [c for c in formset.cleaned_data if c]
                formset = RFormSet(initial=cleaned_data)

    #currently the templates are kept isolated from the rest of the MyFLq site
    #when fully integrated, calculation.html should extend again the general base_ajax.html
    return render(request,'rmne/calculation.html',{'myflq': False,
                                                   'rmneResultID': rmneResultID,
                                                   'rmneResult': rmneResult,
                                                   'firstView': firstView,
                                                   'formset': formset,
                                                   'fileform': fileform})
 


