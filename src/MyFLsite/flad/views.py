from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.html import mark_safe

# Create your views here.
from flad.models import Locus,Allele,FLADkey
from myflq.MyFLq import complement,Alignment
from django.core.exceptions import ObjectDoesNotExist

def getsequence(request,flad,fladid,transform=False,mode=False):
    #Set up FLAD or FLAX
    if flad.lower() == 'flax': from flad.models import TestAllele as Allele
    else: from flad.models import Allele

    try:
        allele = Allele.search(fladid)
    except ObjectDoesNotExist:
        allele = {'unknown':True,'fladid':fladid}

    kwargs = {'allele':allele,
              'flad':True}
    if mode:
        if 'xml' in mode:
            return render(request,'flad/seqid.xml',kwargs,content_type="application/xhtml+xml")
        elif 'plain' in mode:
            return HttpResponse(kwargs['sequence'], content_type="text/plain")
    else: return render(request,'flad/seqid.html' if flad.lower() == 'flad'
        else 'flad/seqidx.html',kwargs)

def getid(request,flad,locus,seq,mode=False,validate=False):
    #Set up FLAD or FLAX
    if flad.lower() == 'flax': from flad.models import TestAllele as Allele
    else: from flad.models import Allele

    try: allele = Allele.search(locus=locus,seq=seq,closeMatch=False)
    except ObjectDoesNotExist:
        #In the future, if not authenticated user, return closeMatch
        #Authenticate user => only for FLAD
        if flad.lower() == 'flad': 
            response = authenticateUser(request)
            if response: return error(request,response,True)
        allele = Allele.add(seq,locus,request.user)
        
    kwargs = {'allele':allele,
              'flad':True}
    if mode:
        if 'xml' in mode:
            return render(request,'flad/seqid.xml',kwargs,content_type="application/xhtml+xml")
        elif 'plain' in mode:
            return HttpResponse(kwargs['fladid'], content_type="text/plain")
    else: return render(request,'flad/seqid.html' if flad.lower() == 'flad'
        else 'flad/seqidx.html',kwargs)

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
        elif 'user' in request.GET:
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
        return "User does not exist or is not authorized, or password is incorrect."
        
    if not request.user.is_authenticated():
        return redirect('/accounts/login/?next=%s' % request.path)
