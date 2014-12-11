from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
from flad.models import Allele
from myflq.MyFLq import complement
from django.core.exceptions import ObjectDoesNotExist

def getsequence(request,fladid,xml=False):
    try: seq = getAllele(fladid).sequence
    except ObjectDoesNotExist:
        seq = ''
    kwargs = {'sequence':seq,
              'complement':complement(seq),
              'fladid':fladid,
              'flad':True}
    if xml: return render(request,'flad/seqid.xml',kwargs,
                          content_type="application/xhtml+xml")
    else: return render(request,'flad/seqid.html',kwargs)

def getid(request,seq,xml=False):
    try: fladid = getAllele(seq,seqid=True).fladid()
    except ObjectDoesNotExist:
        fladid = None
    kwargs = {'sequence':seq,
              'complement':complement(seq),
              'fladid':fladid,
              'flad':True}
    if xml: return render(request,'flad/seqid.xml',kwargs,
                          content_type="application/xhtml+xml")
    else: return render(request,'flad/seqid.html',kwargs)

@login_required
def addid(request,seq,xml=False):
    try: allele = getAllele(seq,seqid=True)    
    except ObjectDoesNotExist: #Add to database
        import random
        from django.db.models import Max
        randomSampleSpace = 1000
        id_max = Allele.objects.all().aggregate(Max('id'))['id__max']
        id_start = id_max - randomSampleSpace if id_max and id_max > randomSampleSpace else 1
        while Allele.objects.filter(id=id_start).exists(): id_start+=1
        chooseSet = set(range(id_start,id_start+randomSampleSpace)) - {a.id for a in Allele.objects.filter(id__gte=id_start)}
        id_chosen = random.sample(chooseSet,1)[0]
        allele = Allele(id=id_chosen,sequence=seq,user=request.user)
        allele.save()
    
    kwargs = {'sequence':seq,
              'complement':complement(seq),
              'fladid':allele.fladid(),
              'flad':True}
    if xml: return render(request,'flad/seqid.xml',kwargs,
                          content_type="application/xhtml+xml")
    else: return render(request,'flad/seqid.html',kwargs)

def getAllele(id,seqid=False):
    if seqid:
        try: allele = Allele.objects.get(sequence=id)
        except ObjectDoesNotExist:
            allele = Allele.objects.get(sequence=id)
    else: allele = Allele.objects.get(id=int(id[2:],base=16))
    return allele 
