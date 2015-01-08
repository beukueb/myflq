from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.html import mark_safe

# Create your views here.
from flad.models import Allele,UsableReference,FLADkey
from myflq.MyFLq import complement,Alignment
from django.core.exceptions import ObjectDoesNotExist

def getsequence(request,flad,fladid,transform=False,mode=False):
    #Set up FLAD or FLAX
    if flad.lower() == 'flax': from flad.models import TestAllele as Allele
    else: from flad.models import Allele

    try:
        allele = Allele.search(fladid)
        seq = allele.sequence
        if transform:
            try: seq = allele.transform(transform)
            except StopIteration as e:
                allele = e.value
                seq = allele.getseq()
        fladid = allele.fladid()
    except ObjectDoesNotExist:
        seq = ''

    kwargs = {'sequence':seq,
              'complement':complement(seq),
              'fladid':fladid,
              'flad':True}
    if mode:
        if 'xml' in mode:
            return render(request,'flad/seqid.xml',kwargs,content_type="application/xhtml+xml")
        elif 'plain' in mode:
            return HttpResponse(kwargs['sequence'], content_type="text/plain")
    else: return render(request,'flad/seqid.html' if flad.lower() == 'flad'
        else 'flad/seqidx.html',kwargs)

def getid(request,flad,seq,mode=False):
    #Set up FLAD or FLAX
    if flad.lower() == 'flax': from flad.models import TestAllele as Allele
    else: from flad.models import Allele

    try: fladid = Allele.search(seq,seqid=True,closeMatch=True).fladid()
    except ObjectDoesNotExist:
        fladid = None
    kwargs = {'sequence':seq,
              'complement':complement(seq),
              'fladid':fladid,
              'flad':True}
    if mode:
        if 'xml' in mode:
            return render(request,'flad/seqid.xml',kwargs,content_type="application/xhtml+xml")
        elif 'plain' in mode:
            return HttpResponse(kwargs['fladid'], content_type="text/plain")
    else: return render(request,'flad/seqid.html' if flad.lower() == 'flad'
        else 'flad/seqidx.html',kwargs)

def validate(request,flad,seq,mode=False):
    #Set up FLAD or FLAX
    if flad.lower() == 'flax': from flad.models import TestAllele as Allele
    else:
        from flad.models import Allele
        #Authenticate user => only for FLAD
        response = authenticateUser(request)
        if response: return response

    #addid logic
    try: allele = Allele.search(seq,seqid=True)    
    except ObjectDoesNotExist: #Add to database
        import random
        if UsableReference.objects.exists() and flad.lower() == 'flad':
            chooseSet = {uR.id for uR in UsableReference.objects.all()}
            id_chosen = random.sample(chooseSet,1)[0]
            UsableReference.objects.get(id=id_chosen).delete()
        else:
            from django.db.models import Max
            randomSampleSpace = 1000
            id_max = Allele.objects.all().aggregate(Max('id'))['id__max']
            id_start = id_max - randomSampleSpace if id_max and id_max > randomSampleSpace else 1
            while Allele.objects.filter(id=id_start).exists(): id_start+=1
            chooseSet = set(range(id_start,id_start+randomSampleSpace)) - {a.id for a in Allele.objects.filter(id__gte=id_start)}
            id_chosen = random.sample(chooseSet,1)[0]
        allele = Allele(id=id_chosen,sequence=seq)
        allele.save()

    allele.users.add(request.user)
    allele.save()
    
    kwargs = {'sequence':seq,
              'complement':complement(seq),
              'fladid':allele.fladid(),
              'flad':True}
    if mode:
        if 'xml' in mode:
            return render(request,'flad/seqid.xml',kwargs,content_type="application/xhtml+xml")
        elif 'plain' in mode:
            return HttpResponse(kwargs['fladid'], content_type="text/plain")
    else: return render(request,'flad/seqid.html' if flad.lower() == 'flad'
        else 'flad/seqidx.html',kwargs)

def unvalidate(request,flad,id,mode=False):
    #Unvalidating not allowed for FLAD testing service FLAX
    if flad.lower() == 'flax':
        return render(request,'flad/messages.html',
                      {'message':mark_safe('''<span style="color:red;">
                      Not possible to unvalidate FLAX references 
                      with the site/API</span>''')})
    #Authenticate user
    response = authenticateUser(request)
    if response: return response

    #Allele should exist, otherwise an error from the user
    try:
        allele = Allele.search(id,seqid=False if id.startswith('F') else True)
        allele.users.remove(request.user)
        allele.save()
    except ObjectDoesNotExist:
        return render(request,'flad/messages.html',
                      {'error_message':mark_safe('There is no entry for <span style="color:red;">{}</span>'.format(id))})
    if allele.users.exists():
        return render(request,'flad/messages.html',
                      {'message':mark_safe('Your validation of <span style="color:red;">{}</span> has been removed.'.format(id))})
    else:
        uR = UsableReference(id=allele.id)
        uR.save()
        id = allele.fladid()
        seq = allele.sequence
        allele.delete()
        return render(request,'flad/messages.html',
                      {'message':mark_safe('Entry <span style="color:red;">{},{}</span> has been removed.'.format(id,seq))})

def error(request,api,flad):
    return render(request,'flad/messages.html',
                  {'message':'''Something is wrong with your 
                  FLAD request: {}'''.format(api)})

@login_required
def registration(request,flad):
    try: fladkey = FLADkey.objects.get(user=request.user)
    except:
        from myflq.MyFLq import makeRandomPassphrase
        fladkey = FLADkey(FLADkey=makeRandomPassphrase(20,30),user=request.user)
        fladkey.save()
    return render(request,'flad/registration.html',{'fladkey': fladkey.FLADkey,'flad':True})
    
def authenticateUser(request):
    """
    Authenticates also for programmatory access.
    A program cannot be easily redirected to login, but should receive a informative warning.
    """
    from django.contrib.auth.models import User
    try:
        #Check user credentials
        if request.method == 'POST':
            request.user = User.objects.get(username=request.POST['user'])
            if not request.user.check_password(request.POST['password']): raise ObjectDoesNotExist
        elif request.GET:
            request.user = User.objects.get(username=request.GET['user'])
            if not request.user.check_password(request.GET['password']):
                try:
                    fladkey = FLADkey.objects.get(user=request.user)
                    if fladkey.FLADkey != request.GET['password']: raise ObjectDoesNotExist
                except:
                    raise ObjectDoesNotExist
        #Check if user is priviliged
        if not request.user.userprofile.fladPriviliged: raise ObjectDoesNotExist
    except ObjectDoesNotExist:
        return HttpResponse("User does not exist or is not authorized, or password is incorrect.",
                            content_type="text/plain")
        
    if not request.user.is_authenticated():
        return redirect('/accounts/login/?next=%s' % request.path)
