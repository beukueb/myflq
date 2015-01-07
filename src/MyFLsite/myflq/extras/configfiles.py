#All functions build to work with MyFLsite config files V2
import re
import pdb

def getLoci(lociFile,skipComments=True):
    loci = {}
    with open(lociFile) as lociFile:
        for line in lociFile:
            if skipComments and line.startswith('#'): continue
            line = line.strip().split(',')
            loci[line[0]] = line
    return loci

def V1toV2config(oldLociFile,alleleFile,newLociFile=None):
    """
    Transforms an old V1 loci config file into a MyFLsite V2 loci config file.
    If newLociFile is not given, oldLociFile is overwritten.
    """
    loci = getLoci(oldLociFile,skipComments=False)
    with open(alleleFile) as alleleFile:
        for locus in loci:
            alleleFile.seek(0)
            try:
                for line in alleleFile:
                    line = line.strip().split(',')
                    if line[0] == locus: raise StopIteration
                raise KeyError("Allele for locus not in alleleFile")
            except StopIteration:
                loci[locus]+=line[1:3]
    with open(newLociFile if newLociFile else oldLociFile,'wt') as lociFile:
        for locus in sorted(loci):
                print(','.join(loci[locus]),file=lociFile)
                
def reprime(lociFile, alleleFile=None, minimalPrimersize = 10, maxPrimersize = 30,
            maxStretch = 2, uniqueness = 0, replace=True):
    """
    Reprimes a loci configfile and optionally an allelefile.
    minimalPrimersize will be the minimal size for the primer if it is already unique
    maxStretch will be the maximal homopolymersize in the primer
    uniqueness is the amount of editing distance the primer will be different from any
     other substring in the configuration alleles
    """
    from myflq.MyFLq import complement
    loci = getLoci(lociFile)
    alleles = {loci[l][5] for l in loci} | {complement(loci[l][5]) for l in loci}
    if not replace: lociFile = lociFile.replace('.csv','_reprimed.csv')
    lociFile = open(lociFile,'wt')
    for locus in loci:
        for p in (2,3):
            locusSeq = loci[locus][5]
            locusComp = complement(loci[locus][5])
            if p == 3: locusSeq, locusComp = locusComp, locusSeq
            for i in range(minimalPrimersize,maxPrimersize+1):
                primer = locusSeq[:i]
                if locusSeq.count(primer) != 1 or locusComp.count(primer) != 0: continue
                unique = True
                for a in (alleles - {locusSeq,locusComp}):
                    if primer in a:
                        unique = False
                        break
                if unique: break
            if i != maxPrimersize: loci[locus][p] = primer
        print(','.join(loci[locus]),file=lociFile)
        
def guessRepeats(lociFile, outFile, minimumRepeatNumber = 3, possibleRepeatSizes = (4,5)):
    """
    Guesses the repeatsize for entries in loci file if unknown.
    lociFile format should be version 2 or later
    minimumRepeatNumber = minimum expected number of exact repeats
    """
    repeatex = {repeatsize:re.compile(
        r'([ACTG]{'+str(repeatsize)+r'})\1{'+
        str(minimumRepeatNumber)+r',}') for repeatsize in possibleRepeatSizes}
    outFile = open('stryxkit_new.csv','wt')
    for line in open(lociFile):
        #pdb.set_trace()
        line = line.strip().split(',')
        if line[1] == 'SNP':
            outFile.write(','.join(line)+'\n')
            continue
        maxResult = (4,minimumRepeatNumber) #Default value for STRs in case real value is not found
        for repeatsize in possibleRepeatSizes:
            for match in repeatex[repeatsize].finditer(line[-1]):
                if len(match.group())/repeatsize > maxResult[1]:
                    maxResult = (repeatsize,len(match.group())/repeatsize)
        line[1] = str(maxResult[0])
        line[-2] = str(int(maxResult[1]))
        outFile.write(','.join(line)+'\n')
    outFile.close()
                
