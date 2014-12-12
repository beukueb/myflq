from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.html import mark_safe

# Create your views here.
from flad.models import Allele,UsableReference
from myflq.MyFLq import complement
from django.core.exceptions import ObjectDoesNotExist

def getsequence(request,fladid,mode=False):
    try: seq = getAllele(fladid).sequence
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
    else: return render(request,'flad/seqid.html',kwargs)

def getid(request,seq,mode=False):
    try: fladid = getAllele(seq,seqid=True).fladid()
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
    else: return render(request,'flad/seqid.html',kwargs)

def validate(request,seq,mode=False):
    #Authenticate user
    response = authenticateUser(request)
    if response: return response

    #addid logic
    try: allele = getAllele(seq,seqid=True)    
    except ObjectDoesNotExist: #Add to database
        import random
        if UsableReference.objects.exists():
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
    else: return render(request,'flad/seqid.html',kwargs)

def unvalidate(request,id,mode=False):
    #Authenticate user
    response = authenticateUser(request)
    if response: return response

    #Allele should exist, otherwise an error from the user
    try:
        allele = getAllele(id,seqid=False if id.startswith('FA') else True)
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
    
def getAllele(id,seqid=False):
    if seqid:
        try: allele = Allele.objects.get(sequence=id)
        except ObjectDoesNotExist:
            allele = Allele.objects.get(sequence=id)
    else: allele = Allele.objects.get(id=int(id[2:],base=16))
    return allele 

def authenticateUser(request):
    """
    Authenticates also for programmatory access.
    A program cannot be easily redirected to login, but should receive a informative warning.
    """
    from django.contrib.auth.models import User
    try:
        if request.method == 'POST':
            request.user = User.objects.get(username=request.POST['user'])
            if not request.user.check_password(request.POST['password']): raise ObjectDoesNotExist
        elif request.GET:
            request.user = User.objects.get(username=request.GET['user'])
            if not request.user.check_password(request.GET['password']): raise ObjectDoesNotExist
    except ObjectDoesNotExist:
        return HttpResponse("User does not exist or password is incorrect.", content_type="text/plain")
        
    if not request.user.is_authenticated():
        return redirect('/accounts/login/?next=%s' % request.path)
