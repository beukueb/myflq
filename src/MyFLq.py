#!/bin/env python3

## MyFLq Interface functions to the MyFLdb produced tables

# MyFLq (My-Forensic-Loci-queries, developer Christophe Van Neste, CC BY-SA 3.0).
version = '1.0.1'

# Python support: version 3
# 
# This framework consists out of two parts: (1) A MySQL database backend that is
# populated by calibration data; (2) a Python frontend with functions for
# adding calibration data to the database, and performing the analysis of
# unknown samples.
# 
# The functions used in our MyFLq paper are listed in the table below.
# 
# Table: Relevant MyFLq functions. In order of appearance in the source file
# --------------------------------------------------------------------------
#                   Alignment | Performs a global alignment according to the Needleman-Wunsch algorithm, 
#                             | favoring stutter gaps of a certain repeat size for STR loci
#                   makeEntry | Adds a sequence to the MySQL database with validation info, such as allele name or number.
#            processLociNames | Processes the database table with validated allele sequences, determining primers 
#                             | and flanks for each locus.
#          processLociAlleles | Determines the region of interest for each validated allele present in the database.
#               Read.flankOut | Removes the flanks of a read.
#             Locus.processFQ | Fully processes a FASTQ file.
#                  makeReport | Prints out an xml file of the full analysis.
# ValidLocus.searchNewAlleles | Performs a strict analysis on a FASTQ file with known alleles, 
#                             | in order to add sequences to the database.
#                             | Makes a list of the sequences between the primers of each locus.
# 

### General functions

#General imports
from itertools import repeat
    
#Database functions
class Login: #Passwd and profiler depend on how you set up MySQL
    def __init__(self,user="testuser",passwd="testuser",database='testdb'):
        """
        Makes a callable object, that returns a connection with given credentials.
        """
        self.user=user
        self.passwd=passwd
        self.database=database
    def __call__(self,user=None,passwd=None,database=None):
        """
        When a call is made to a Login object, provided arguments are applied to the object attributes.
        Hence, future calls can be made without the argument and will give the same result.
        
        Returns the formed connection with the db using variablenames: conn, sql
        """
        if user: self.user=user
        if passwd: self.passwd=passwd
        if database: self.database=database

        try: import pymysql as MySQLdb
        except ImportError: import MySQLdb #py2#
        conn = MySQLdb.connect(host = "localhost",
                               user = self.user,
                               passwd = self.passwd,
                               db = self.database)
        sql = conn.cursor(MySQLdb.cursors.DictCursor)
        return (conn,sql)
    def testConnection(self):
        try:
            conn,sql = self()
            logout(conn,sql)
        except Exception as e: raise Exception(str(e.args))
        
login = Login()

def logout(conn,sql):
    """
    Logout from the database connection
    """
    sql.close()
    conn.commit()
    conn.close()

#Multiprocessing
import subprocess
def ipcluster(do='start',process=None,numberOfEngines=4):
    if do=='start':
        #return subprocess.Popen('ipcluster start -n '+str(numberOfEngines),shell=True)
        return [subprocess.Popen('ipcontroller')]+[subprocess.Popen('ipengine') for i in range(numberOfEngines)]
    elif do=='stop':
        #subprocess.call('ipcluster stop',shell=True)
        #process.poll()
        [(p.send_signal(subprocess.signal.SIGINT),p.poll()) for p in process]
    elif do=='restart':
        ipcluster('stop',process=process)
        return ipcluster('start',numberOfEngines=numberOfEngines)

#General DNA functions        
class LocusConflictError(Exception):
    """
    Errors related to loci
    """
    def __init__(self, value='Locus data present in the database, contains conflicting information',message=''):
        self.value = value
        self.message = message
    def __str__(self):
        return repr(self.value)

def getSeq(seqID,sql=None):
    """
    Returns the actual sequence for a certain seqID
    """
    #if not sql: conn,sql = login()
    #else: conn=None
    sql.execute("SELECT sequence FROM BASEseqs WHERE seqID = %s", (seqID))
    if sql.rowcount == 0: raise Exception("No such sequence in the database")
    seq = sql.fetchone()['sequence']
    #if conn: logout(conn,sql)
    return seq

#DNA functions
def complement(dna):
    """
    Returns the complement of a DNA string
    """
    return dna.translate(complement.dict)[::-1]
try: complement.dict=str.maketrans('ACTGactg','TGACtgac')
except AttributeError: #py2#
    import string
    complement.dict=string.maketrans('ACTGactg','TGACtgac')
#Test complement
#%timeit -n1000 s=complement(sequence)

def compress(dna):
    """
    Compresses all homopolymers in a DNA sequence to their base (including 'N' homopolymers)
    """
    return ''.join([dna[na] for na in range(len(dna)) if dna[na]!=dna[na-1] or na == 0])

def fastaReader(fd):
    """
    Expects an open file descripter from a multi-lined fasta
    and turns it into a one-lined fasta iterator
    Will only work with constructs: line in file
    and not with file.readline()
    """
    previousLine=''
    for line in fd:
        if previousLine.startswith('>'):
            lineToYield = previousLine
            previousLine = line
            yield lineToYield
        elif line.startswith('>'):
            lineToYield = previousLine
            previousLine = line
            if lineToYield: yield lineToYield
        else: previousLine = previousLine.replace('\n',line)
    yield previousLine
    
class Alignment:
    """
    Wrapper for alignments.
    Currently implemented in python, but needs to be optimized.
    Special for forensic STR loci => a STR-size locus specific stutter gap score
    """
    import numpy as np
    bases_dict_i = {'A':0,'C':1,'T':2,'G':3,'N':4} #indices for the bases in similarity_m
    #similarity_m, and gap penalties should depend on technology used
    similarity_m = np.matrix([[10,-1,-1,-1, 0], 
                              [-1,10,-1,-1, 0],
                              [-1,-1,10,-1, 0],
                              [-1,-1,-1,10, 0],
                              [ 0, 0, 0, 0, 0]])
    gapPenalty = -5
    stutterPenalty = -10
    scoresToBreadcrumbs = {0:4,1:2,2:1,3:6,4:3}
    def __init__(self,dna1,dna2,mode='global',stutter=False,gapPenalty=None):
        """
        Performs a global alignment according to Needleman-Wunsch algorithm, favouring stutter gaps if desired
        
        If mode == 'global': normal global alignment
        If mode == 'primer-search': local alignment is performed. 
            Primer should be given as dna1 and be expected closest to the left.
        If mode == 'flank-index': functionality for flankOut, incremental mismatch penalties
            Flank should be given as dna1 and be expected closest to the left.
            The alignment will be semi-global => global up to the point where the flank (dna1) ends
            Should not be used with 'stutter' option
        """
        np = self.np
        if gapPenalty: self.gapPenalty = gapPenalty
        #F matrix => i0xx = scores, i1xx = breadcrumbs (0=None;1=->;2=-->;4=L;3=v;6=V)
        F_m = np.zeros((2,len(dna1)+1,len(dna2)+1))
        self.F_m = F_m #for debugging
        self.stutter = stutter #for calculating differences
        #Fill first row and column
        if mode=='global':
            for i in range(1,len(dna1)+1): F_m[0,i,0],F_m[1,i,0] = i*self.gapPenalty , 1
            for j in range(1,len(dna2)+1): F_m[0,0,j],F_m[1,0,j] = j*self.gapPenalty , 3
        elif mode=='primer-search':
            for i in range(1,len(dna1)+1): F_m[0,i,0],F_m[1,i,0] = 0 , 1
            for j in range(1,len(dna2)+1): F_m[0,0,j],F_m[1,0,j] = 0 , 3
        elif mode=='flank-index':
            #Experimental: the concept is to have an incremental mismatch and/or match score, as we get nearer to
            #    the flank ending, where correct matching is more important.
            #    It is important to reflect on whether this incremental scheme should be applied to both flank and
            #    read strand, or only to the flank
            #    (i*(10 if i > 10 else i)) => gaps in the beginning are favoured in comparison to gaps further on
            for i in range(1,len(dna1)+1): F_m[0,i,0],F_m[1,i,0] = int((i*(np.sqrt(10) if i > 10 else np.sqrt(i)))
                                                                       *self.gapPenalty) , 1
            for j in range(1,len(dna2)+1): F_m[0,0,j],F_m[1,0,j] = 0 , 3
        #Fill
        for i in range(1,len(dna1)+1):
            #pdb.set_trace()
            for j in range(1,len(dna2)+1):
                if mode=='flank-index': #calculate scores to make them incremental in respect to flank position
                    scores = [F_m[0,i-1,j-1] + (np.sqrt(10) if i > 10 else np.sqrt(i))*
                              self.similarity_m[self.bases_dict_i[dna1[i-1]],self.bases_dict_i[dna2[j-1]]], #match: L
                              None, #stutter-delete: not useful for flank-index
                              F_m[0,i-1,j] + (np.sqrt(10) if i > 10 else np.sqrt(i))*self.gapPenalty, #delete: ->
                              None,#stutter-insert: not useful for flank-index
                              F_m[0,i,j-1] + (np.sqrt(10) if i > 10 else np.sqrt(i))*self.gapPenalty #insert: v
                              ]               
                else: #for global and primer-search mode
                    scores = [F_m[0,i-1,j-1] + 
                              self.similarity_m[self.bases_dict_i[dna1[i-1]],self.bases_dict_i[dna2[j-1]]],
                                  #match: L
                              None if not stutter or stutter > i else F_m[0,i-stutter,j] + self.stutterPenalty,
                                  #stutter-delete: -->
                              F_m[0,i-1,j] + self.gapPenalty,
                                  #delete: ->
                              None if not stutter or stutter > j else F_m[0,i,j-stutter] + self.stutterPenalty,
                                  #stutter-insert: V
                              F_m[0,i,j-1] + self.gapPenalty #insert: v
                              ] #stutters come before single gaps as they are preferred                
                    
                try: maxScore = max(scores)
                except TypeError: maxScore = max(filter(lambda x: x is not None,scores))
                maxCrumb = self.scoresToBreadcrumbs[scores.index(maxScore)]
                F_m[0,i,j],F_m[1,i,j] = maxScore,maxCrumb
        if mode=='flank-index':
            self.flankOutIndex = F_m[0,len(dna1),:].tolist().index(F_m[0,len(dna1),:].max()) - 1
                #debug# plus or minus 1 #depends on downstream use
            return
        
        #Follow the breadcrumbs
        alnment = []
        i,j=len(dna1),len(dna2)
        #Primer-search addendum => allows for best local alignment for primer
        if mode=='primer-search':
            if i < j:
                primerMax=max(F_m[0,-1,:])
                while primerMax != F_m[0,-1,j]: j-=1
            else: raise Exception('Primer should be first sequence given to alignment and shorter than other sequence')
        #end addendum
        while i >= 0 or j >= 0:
            if F_m[1,i,j] == 4:
                alnment.append([dna1[i-1],dna2[j-1]])
                i-=1
                j-=1
            elif F_m[1,i,j] == 1:
                alnment.append([dna1[i-1],'-'])
                i-=1                
            elif F_m[1,i,j] == 2:
                for s_i in range(stutter):
                    alnment.append([dna1[i-1],'-'])
                    i-=1
            elif F_m[1,i,j] == 3:
                alnment.append(['-',dna2[j-1]])
                j-=1
            elif F_m[1,i,j] == 6:
                for s_i in range(stutter):
                    alnment.append(['-',dna2[j-1]])
                    j-=1
            else: break
        self.alnment = alnment[::-1]
        self.score = F_m[0,-1,-1]
    def getDifferences(self):
        """
        Returns number of differences (one stutter counts for 1 difference)
        """
        if not self.stutter:
            return sum([len(set(a)) == 2 for a in self.alnment])
        else:
            differences = sum([len(set(a)) == 2 for a in self.alnment if not '-' in a])
            dna1 = ''.join([a for a,b in self.alnment])
            dna2 = ''.join([b for a,b in self.alnment])
            stutter = '-'*self.stutter
            differences+=dna1.count(stutter) + dna1.count('-') - (dna1.count(stutter)*self.stutter)
            differences+=dna2.count(stutter) + dna2.count('-') - (dna2.count(stutter)*self.stutter)
            return differences


# AlleleType => work in progress, not yet used

class AlleleType:
    def __init__(self,alleleType,subType=None,locusType='STR'):
        """
        Simple class that allows to work easily with alleleTypes.
        If STR locusType, alleTypes can be compared on size, else an exception is raised.
        It is assumed that only alleles of the same locus are being compared!
        For STR: == compares alleleTypes; <= compares alleleNumbers
        """
        self.locusType = locusType
        self.alleleType = str(alleleType)
        if locusType == 'STR':
            try: self.alleleNumber = float(alleleType)
            except ValueError: self.alleleNumber = None
        self.subType = subType
    def __str__(self):
        return self.alleleType + (('['+self.subType+']') if self.subType else '')
    def __repr__(self):
        return ('AlleleType(\''+ self.alleleType+'\',subType=\''+(self.subType if self.subType else '')+
                '\',locusType=\''+self.locusType+'\')')
    def __hash__(self):
        return self.__str__().__hash__()
    def __eq__(self,other):
        if self.alleleType=='NA' or other.alleleType=='NA':
            return False #Not assigned alleles cannot be equal to one another
        return (self.alleleType == other.alleleType) and (((not self.subType) and (not other.subType)) 
                                                           or self.subType == other.subType)
    def __lt__(self,other):
        if self.locusType != 'STR': raise Exception('< comparison of non-STR alleleTypes')
        return self.alleleNumber < other.alleleNumber
    def __le__(self,other):
        if self.locusType != 'STR': raise Exception('<= comparison of non-STR alleleTypes')
        return self.alleleNumber < other.alleleNumber or self.alleleNumber == other.alleleNumber


# #DNA mask
# 
# class DNAmask:
#     def __init__(self,dna,threshold=0.01):
#         """
#         Create a DNA mask
#         dna = list of bp dict's
#         """
#         dna = [{pa:aa[pa] for pa in aa if aa[pa]>=threshold} for aa in dna]
#         self.mask = ['N' if len(aa)==1 else aa for aa in dna]
#     def align(self,read):
#         pass

# ## <a id="entry">Functions for making entries to the database</a>

#Function for adding samples to the database
def makeEntry(sequences,seqCounts,locusName,labID='NA',passphrase='NA',technology='Illumina',filterLevel=None,
              forwardP=None,reverseP=None,locusType=None,validatedInfo=None,manualRevision=False,population='NA'):
    """
    Is the starting function for adding new alleles (and all the relevant sequences for one locus of one pure profile) 
    to the database. Can be used directly, or by a function that calls it by means of an url api interface.
    The latter would be interesting for an organisation building a big MPS ready allele database, and has many 
    colloborators that need to add alleles to the database.
    
    The logic of these functions has to be followed.
    The MySQL database itself does not make all the necessary checks and balances, that these functions do.

    Sequences, seqCounts (and validatedInfo if provided) should be lists of equal length
    The different lists should be structured as follows:
        sequences     = [s1, s2, s3]
        seqCounts     = [c1, c2, c3]
        validatedInfo = [x1, x2, x3] (if provided)
    
    Validation info has to be provided for each sequence (s) at the same index in a list,
    the validation values can be:
        x == 'NA' => s is not validated
        x == 'a[:X[:R#repeat]]'
                => s is validated as an allele with allelenumber/name X, 
                            and if STR locus repeatsize of locus #repeat (in bp), e.g.:
                        x == 'a' => only validated as allele, no extra info
                        x == 'a:10.1'    => validated as allele 10.1
                        x == 'a:10.1:R4   => validated as allele 10.1 from a locus with a repeatsize of 4 bp
        x > 0   => s is a validated error of the allele (s) with index x
                    e.g. if s3 is a validated error of s2, x should equal 2
    If you are not sure on how to provide validation info, don't provide it!
    The framework is not ready yet to handle inconsistent validation info.
    """
    #Check conditions
    if not ((forwardP and reverseP) or (not forwardP and not reverseP)):
        raise Exception("either give both primers or neither")
    if type(sequences) != list: sequences=[sequences]
    if type(seqCounts) != list: seqCounts=[seqCounts]
    if validatedInfo and type(validatedInfo) != list: validatedInfo=[validatedInfo]
    if locusType is None:
        for v in validatedInfo:
            if ':R' in v:
                locusType = int(v[v.index(':R')+2:])
                break
    if len(sequences) != len(seqCounts) or (validatedInfo and len(validatedInfo) != len(sequences)):
        raise Exception("Number of sequences, sequences-counts and/or validation-info does not match")
    
    #Login to database
    conn,sql = login() #Necessary to have a unique connection as makeEntry makes use of MySQL LAST_INSERT_ID() 
                       #which is connection dependent
    
    #Check authentification of submitting institution
    sql.execute ("SELECT passphrase FROM laboratories WHERE labID = %s", (labID))
    if sql.rowcount == 0: raise Exception("Lab identifier not known, register first")
    elif sql.fetchone()['passphrase'] != passphrase: raise Exception("Passphrase for "+labID+" not correct!")
        
    #First table that needs to be updated is BASEseqs: take all seqID's for the sequences and primers
    seqIDs=[]
    if forwardP and reverseP: sequences+=[forwardP,reverseP]
    for seq in sequences:
        seqIDs.append(getSeqID(seq,sql))
    if forwardP and reverseP:
        reverseP, forwardP = seqIDs.pop(), seqIDs.pop()
        sequences.pop(),sequences.pop()
    
    #Second set of tables to be updated: BASEnames,BASEprimersets,BASEqual
    primersetID,qualID = makeLocusEntry(forwardP,reverseP,locusName,locusType,technology,filterLevel,sql=sql)
    
    #Third table that needs to be updated is BASEtrack
    sql.execute("INSERT INTO BASEtrack (locusName, qualID, labID, validated, manualRevision, nrSeqs, nrReads,                   population) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (locusName,qualID,labID,bool(validatedInfo),manualRevision,len(sequences),sum(seqCounts),population))
    #Fetch entryID from previous step
    #!!!Don't do any other sql inserts between updating BASEbasetrack and before fetching this entryID!!!
    sql.execute("SELECT LAST_INSERT_ID();")
    entryID=sql.fetchone()['LAST_INSERT_ID()']
    
    #Last table to update: BASEstat
    #todo# check following if
    if validatedInfo:
        alleleValidation=[v[2:] if 'a:' in str(v) and v != 'a:' else None for v in validatedInfo]
        validatedInfo=[0 if ('a:' in str(v) or str(v)=='a') else v for v in validatedInfo]
        validatedInfo=[-1 if v=='NA' else int(v) for v in validatedInfo]
    else:
        alleleValidation=[None for s in sequences]
        validatedInfo=[-1 for s in sequences]
    for seqID,seqCount,valid,avalid in zip(seqIDs,seqCounts,validatedInfo,alleleValidation):
        if valid and valid > 0: valid = seqIDs[valid-1] # -1 as list number is given and not python index
        sql.execute ("INSERT INTO BASEstat (entryID, seqID, primersetID,validated, alleleValidation, seqCount)                       VALUES (%s,%s,%s,%s,%s,%s)"
                    ,(entryID, seqID, primersetID, valid, avalid, seqCount))
        
    #Log out of database
    logout(conn,sql)
    return entryID

def makeLocusEntry(forwardP,reverseP,locusName,locusType,technology,filterLevel,sql=None):
    """
    Makes/checks table information that is more general than an individual sequence. It is therefore possible
    that the relevent tables don't need to be updated. In that case the function returns the necessary
    ID's for BASEstat and BASEtrack.
    """
    if not sql: conn,sql = login()
    else: conn=None

    #BASEnames
    sql.execute("SELECT locusType FROM BASEnames WHERE locusName = %s",(locusName))
    if not sql.rowcount:
        sql.execute("INSERT INTO BASEnames (locusName,locusType) VALUES (%s,%s)",(locusName,locusType))
    elif sql.fetchone()['locusType'] is None and locusType is not None:
        sql.execute("UPDATE BASEnames SET locusType = %s WHERE locusName = %s",(locusType,locusName))
    
    #BASEprimersets
    if not forwardP: primersetID = None
    else:
        if type(forwardP) != int: forwardP = getSeqID(forwardP,sql)
        if type(reverseP) != int: reverseP = getSeqID(reverseP,sql)
        sql.execute("SELECT primersetID FROM BASEprimersets WHERE forwardP = %s AND reverseP = %s AND locusName = %s",
                    (forwardP,reverseP,locusName))
        if not sql.rowcount:
            sql.execute("INSERT INTO BASEprimersets (forwardP,reverseP,locusName) VALUES (%s,%s,%s)",
                        (forwardP,reverseP,locusName))
            sql.execute("SELECT primersetID FROM BASEprimersets WHERE forwardP = %s AND reverseP = %s AND                          locusName = %s",(forwardP,reverseP,locusName))
        primersetID = sql.fetchone()['primersetID']
    
    #BASEqual
    if not technology and not filterLevel: qualID = None
    else:
        sql.execute("SELECT qualID FROM BASEqual WHERE technology <=> %s AND filterLevel <=> %s",
                    (technology,filterLevel))
        if not sql.rowcount:
            sql.execute("INSERT INTO BASEqual (technology,filterLevel) VALUES (%s,%s)",(technology,filterLevel))
            sql.execute("SELECT qualID FROM BASEqual WHERE technology <=> %s AND filterLevel <=> %s",
                        (technology,filterLevel))
            #             => use null-safe equality operator '<=>' to test for equality considering also NULL values
        qualID = sql.fetchone()['qualID']
        #sql.execute("SELECT LAST_INSERT_ID()")
        #qualID=sql.fetchone()['LAST_INSERT_ID()']
            
    if conn: logout(conn,sql)        
    return primersetID,qualID

def getSeqID(seq,sql=None):
    if not sql: conn,sql = login()
    else: conn=None
        
    sql.execute ("SELECT seqID FROM BASEseqs WHERE sequence = %s", (seq))
    if sql.rowcount == 0: 
        sql.execute ("INSERT INTO BASEseqs (sequence) VALUES (%s)", (seq))
        sql.execute ("SELECT seqID FROM BASEseqs WHERE sequence = %s", (seq))

    if conn: logout(conn,sql)
    return sql.fetchone()['seqID']

#Functions for adding users/laboratories
def addLab(labID,passphrase):
    conn,sql=login()
    sql.execute ("SELECT passphrase FROM laboratories WHERE labID = %s",(labID))
    if sql.rowcount != 0: raise Exception(
            "Lab identifier not unique, you either already registered or need to choose another identifier")
    else:
        sql.execute ("INSERT INTO laboratories (labID, passphrase) VALUES (%s,%s)", (labID,passphrase))
    logout(conn,sql)

def makeRandomPassphrase(minLength=8,maxLength=20):
    if maxLength > 40: raise Exception("The underlying database stores passphrases only up to 40 characters")
    import random
    length=random.randint(minLength,maxLength)
    passphrase=''
    for l in range(length): passphrase+=random.sample(makeRandomPassphrase.symbols,1)[0]
    return passphrase
makeRandomPassphrase.exsymbols={'"',"'",'\\','/','{','}','(',')','&','`'}
makeRandomPassphrase.symbols={chr(a+33) for a in range(94) if chr(a+33) not in makeRandomPassphrase.exsymbols}


#Functions for external connectivity to the database
def makeEntries(csvFilename):
    """
    Takes a csv file and inputs each line into the database.
    The csv should have the following format (header is optional)
    AlleleValidation is optional, but has to be provided at least once for each STR locus.
    For SNP loci it is recommended to always provide a name for the allele as validation (otherwise MyFLq will
    assign a random unqiue identifier only valid for the current database)
    
    The allelesequence has to contain the primer sequences as known to the database (it can also be longer)
    ============format-csv=====================
    #Locus,AlleleValidation,AlleleSequence
    FGA,13,GGCTGCAGGGCATAACATTA...
    Amelogenin,X,CCCTGGGCTCTGTAAAGAA...
    FGA,GGCTGCAGGGCATAACATTA...
    ===========================================
    For a full working example, see the documentation file: alleles_example.csv
    """
    for line in open(csvFilename):
        if line.strip().startswith('#'): continue
        try: locusName,validatedInfo,sequence = line.strip().split(',')
        except ValueError:
            locusName,sequence = line.strip().split(',')
            validatedInfo = None
        sequence = sequence.upper()
        makeEntry(sequence,0,locusName,validatedInfo='a:'+validatedInfo if validatedInfo else 'a',
                  manualRevision=True)
    
    
#    import xml.etree.ElementTree as ET
#    entries = ET.Element('entries')
#    labID = ET.SubElement(entries,'labID')
#    labID.text = 'labfbt'
#    labID.set('passphrase','labfbt')
#    while 1:
#        entry = ET.SubElement(entries,'entry')
#        while 1:
#            seq = ET.SubElement(entry,'sequence')
#            break
#        break
#    ET.ElementTree(entries).write(xmlFilename, encoding = "UTF-8", xml_declaration = True)       


# ## <a id="dbproc">Database processing: extracting references from base information</a>


#Functions for extracting relevant info from base tables (BASE*) and storing in processed tables LOCI[name/alleles]

#Main function elaborates on loci names, to update the table LOCInames
def processLociNames():
    #Get loci names for which an entry serves in LOCInames
    conn,sql = login()
    sql.execute("SELECT DISTINCT(locusName) AS locusName FROM BASEnames")
    locusNames = [s['locusName'] for s in sql.fetchall()]
    locusNames.sort()
    
    #Clear all rows #todo# should be implemented with updating rows in the future
    sql.execute("DELETE FROM LOCInames WHERE TRUE")
    for name in locusNames:
        #Collect known primersets for locus
        sql.execute("SELECT getSeq(forwardP) AS fP,getSeq(reverseP) AS rP FROM BASEprimersets WHERE locusName = %s",
                    (name))
        primersets = {(s['fP'],complement(s['rP'])) for s in sql.fetchall()} #Complement taken from reverse primer!!!
        
        #Collect known alleles for locus
        #todo# Include BASEtrack.manualRevision
        #Flanking region determination considers all and only validated alleles
        sql.execute("""SELECT getSeq(seqID) AS seq,alleleValidation FROM BASEtrack
                       JOIN BASEstat USING (entryID)
                       WHERE locusName = %s AND BASEstat.validated = 0""", (name))
        locAlleles={(s['seq'],s['alleleValidation']) for s in sql.fetchall()}
        
        #At this point all alleles for a locus are gathered and relevant information needs to be extracted:
         #Reference allele and primers
        reference_allele,(primerF,primerR) = getRefAllel(primersets,locAlleles)
        primerR = complement(primerR) #Revert primerR back to complementary strand
         #Locustype
        sql.execute("""SELECT locusType FROM BASEnames WHERE locusName = %s""", (name))
        locusType = sql.fetchone()['locusType']
        if locusType != 0 and ':R' in reference_allele[1]:
            reference_allele=(reference_allele[0],reference_allele[1][:reference_allele[1].index(':R')])
         #Initial flanking regions
        flank_forwardP,flank_reverseP = getLocusFlanks(locAlleles,primerF,primerR)
         #Calculate ref_length
        ref_length = len(reference_allele[0]) - len(primerF) - len(primerR) - len(flank_forwardP) - len(flank_reverseP)
        #Insert into LOCInames
        sql.execute("""INSERT INTO LOCInames (locusName,locusType,refseq,ref_forwardP,ref_reverseP,
        flank_forwardP,flank_reverseP,ref_length,ref_alleleNumber) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                    ,(name,locusType,reference_allele[0],primerF,primerR,flank_forwardP,flank_reverseP,
                      ref_length,reference_allele[1]))        
    logout(conn,sql)
    
def getRefAllel(primersets,locAlleles):
    """
    Analyses all primers and alleles of a locus, and returns a tuple: (reference_allele,(primerF,primerR))
    First dismisses primersets that are not present in all the alleles for the locus.
    Than takes a random reference allele with full annotation, and selects the primerpair with the largest
    range on the allele.
    Alleles that are in the opposite direction of the chosen primerset get complemented in locAlleles.
    """
    for primers in primersets.copy():
        if sum(((primers[0] in a[0] and primers[1] in a[0])
                or (complement(primers[0]) in a[0] and complement(primers[1]) in a[0]) 
                for a in locAlleles)) < len(locAlleles):
            primersets.remove(primers)
    if not primersets: raise LocusConflictError('No primersets that cover all locus alleles')

    #Take reference allele
    for allele in locAlleles:
        if allele[1]:
            referenceAllele = allele
            break
        
    #Find primerset with widest range
    try: primersets = {p:(referenceAllele[0].index(p[1])+len(p[1]))-referenceAllele[0].index(p[0]) for p in primersets}
    except NameError: raise LocusConflictError('No validated alleles with full annotation for locus')
    referencePrimers = max(primersets,key=lambda x:primersets[x])
        
    #Check allele orientation in respect of chosen primerset
    for allele in locAlleles.copy():
        if referencePrimers[0] not in allele[0]:
            locAlleles.remove(allele)
            locAlleles.add((complement(allele[0]),allele[1]))
    if referencePrimers[0] not in referenceAllele[0]: referenceAllele = (complement(referenceAllele[0]),
                                                                         referenceAllele[1])   
    return referenceAllele,referencePrimers

def getLocusFlanks(locAlleles,primerF,primerR):
    """
    The initial determination of flanking regions for a locus, can be straightforward.
    Starting from the reference primers we indicate the flanks that remain common between all alleles.
    The current implementation does not take acount of the possibility of different primer sets for a locus,
    which could lead to the exlusion of alleles with specific primerset SNP's
    primerR is expected to be on the alternate strand and gets complemented within the function.
    """
    #todo# Implementation for a locus with different primersets 
    #(also possible to implement higher up the function stack)
    #Only allele seqs serve from locAlleles
    locAlleles={l[0] for l in locAlleles}
    #Set primerR complement
    primerR=complement(primerR)
    #Test if primers are present and cut them out (if necessary take complement sequence); split seq's in two flanks
    forwardFlanks = set()
    reverseFlanks = set()
    for seq in locAlleles:
        if not (seq.count(primerF) == seq.count(primerR) == 1):
            seq=complement(seq)
            if not (seq.count(primerF) == seq.count(primerR) == 1):
                raise LocusConflictError('Conflicting primers for this locus. Handling not yet implemented')
        seq=seq[seq.index(primerF)+len(primerF):seq.index(primerR)]
        forwardFlanks.add(seq)
        reverseFlanks.add(complement(seq))
    #Get maximal possible size for right and left flanks
    maxOneWay = min({len(s) for s in forwardFlanks})
    maxOverlap = int(maxOneWay/2) #In case the flanks would overlap they can only be half of the max-size
    returnFlanks = []
    for flanks in (forwardFlanks,reverseFlanks):
        for consensus in range(maxOneWay+1):
            if len({s[:consensus] for s in flanks}) != 1: break
        if consensus != maxOneWay: consensus-=1
        returnFlanks.append(flanks.pop()[:consensus])
    #Check if flanks don't overlap, if they do, reduce them
    if (len(returnFlanks[0]) + len(returnFlanks[1])) > maxOneWay:
        if len(returnFlanks[0]) <= (maxOverlap+(maxOneWay%2)):
            returnFlanks[1] = returnFlanks[1][:maxOneWay-len(returnFlanks[0])]
        elif len(returnFlanks[1]) <= maxOverlap:
            returnFlanks[0] = returnFlanks[0][:maxOneWay-len(returnFlanks[1])]
        else:
            returnFlanks[0] = returnFlanks[0][:maxOverlap+(maxOneWay%2)]
            returnFlanks[1] = returnFlanks[1][:maxOverlap]
    return (returnFlanks[0],returnFlanks[1])


#Functions for filling population statistics tables: LOCIalleles and LOCIalleles_CE

#LOCIalleles
def processLociAlleles(flush=True):
    """
    Extract all validated alleles for all loci within the main database tables
    """
    conn,sql = login()
    if flush: sql.execute("DELETE FROM LOCIalleles WHERE TRUE")
    
    #Select loci:
    sql.execute('SELECT * FROM LOCInames')
    for locus in sql.fetchall():
        locusName = locus['locusName']
        sql.execute("""SELECT getSeq(seqID) AS seq,alleleValidation FROM BASEtrack
                       JOIN BASEstat USING (entryID)
                       WHERE locusName = %s AND BASEstat.validated = 0""", (locusName))
        locAlleles={(s['seq'],s['alleleValidation']) for s in sql.fetchall()}
        for allele,alleleNomen in locAlleles:
            allele = flankOutAllele(locus,allele)
            alleleNumber = calculateAlleleNumber(allele,locus)
            sql.execute("SELECT COUNT(*) FROM LOCIalleles WHERE locusName = %s AND alleleSeq = %s", (locusName,allele))
            count=sql.fetchone()['COUNT(*)']
            if count == 0:
                sql.execute("INSERT INTO LOCIalleles (locusName,alleleNumber,alleleSeq) VALUES (%s,%s,%s)",
                            (locusName,alleleNumber,allele))
                #Set version in alleleNomen for STR alleles with same number
                if locus['locusType'] != 0:
                    sql.execute("SELECT COUNT(*) FROM LOCIalleles WHERE locusName = %s AND alleleNumber = %s", 
                                (locusName,alleleNumber))
                    alleleCount=sql.fetchone()['COUNT(*)']
                    alleleNomen='['+chr(ord('a')+alleleCount-1)+']' 
                        #todo# only intended to work up to 26 same alleleNumber types
                    sql.execute("""UPDATE LOCIalleles SET alleleNomen = %s WHERE locusName = %s AND alleleSeq = %s""",
                                (alleleNomen,locusName,allele))
            elif count > 1:
                raise LocusConflictError('Too many same alleles in LOCIalleles:                 every combination locusName-allele sequence should be unique')
            #If not STR locus
            if not alleleNumber and alleleNomen:
                sql.execute("""UPDATE LOCIalleles SET alleleNomen = %s WHERE locusName = %s AND alleleSeq = %s""",
                            (alleleNomen,locusName,allele))
    logout(conn,sql)

#Flankout allele
def flankOutAllele(locus,allele):
    """
    Expects: a dictionary 'locus' with the same keys as LOCInames' columns, and the allele seq
    Returns allele seq in the LOCInames orientation with flanks and primers removed
    """
    #Check allele strand orientation
    if complement(locus['ref_forwardP']) in allele and locus['ref_reverseP'] in allele: allele=complement(allele)
    
    #Cut out primers
    if locus['ref_forwardP'] not in allele or complement(locus['ref_reverseP']) not in allele:
        raise LocusConflictError('Ref primers not in allele for '+locus['locusName'])
    allele=allele[allele.index(locus['ref_forwardP'])+len(locus['ref_forwardP']):
                  allele.index(complement(locus['ref_reverseP']))]
    
    #Cut out flanking regions
    #todo# flanks need to be defined more fuzzy allowing for snp's and indels
    if locus['flank_forwardP'] not in allele or complement(locus['flank_reverseP']) not in allele:
        raise LocusConflictError('Flank primers not in allele for '+locus['locusName'])
    allele=allele[len(locus['flank_forwardP']):len(allele)-len(locus['flank_reverseP'])]
    
    return allele

#Calculate alleleNumber
def calculateAlleleNumber(regionOfInterest,locus):
    """
    Calulate alleleNumber for STR loci.
    Expects: a dictionary 'locus' with the same keys as LOCInames' columns, and the allele seq
    Expects allele regionOfInterest, i.c. flanked out allele based on locusDict[locus]
    
    This function is also used by Analysis. In case of stutterBuffer a correctionfactor is calculated.
    """
    if not locus['locusType']: return None
    correctionFactor = 0
    try:
        correctionFactor+=len(locus['removed_from_flank_forwardP'])
        correctionFactor+=len(locus['removed_from_flank_reverseP'])
    except KeyError: pass #correction not needed
        
    regionOfInterest=len(regionOfInterest) - correctionFactor
    if regionOfInterest == locus['ref_length']: alleleNumber = locus['ref_alleleNumber']
    else:
        if '.' not in locus['ref_alleleNumber']:
            ref_length = int(locus['ref_length'])
            ref_alleleNumber = int(locus['ref_alleleNumber'])
        else:
            ref_length = (int(locus['ref_length'])-
                          int(locus['ref_alleleNumber'][locus['ref_alleleNumber'].index('.')+1:]))
            ref_alleleNumber = int(locus['ref_alleleNumber'][:locus['ref_alleleNumber'].index('.')])
        ref_difference = regionOfInterest - ref_length
        ref_offset = (regionOfInterest - ref_length  )%locus['locusType']
        alleleNumber = str( ref_alleleNumber + int(ref_difference/locus['locusType'])
                            - (1 if (ref_difference<0 and ref_offset) else 0) ) #correction when regionOfInterest < ref_length
        if ref_offset != 0: 
            alleleNumber += '.'+str((regionOfInterest - ref_length  )%locus['locusType'])
    return alleleNumber
    
#Calculate population frequencies for LOCIalleles
#todo#

#Make an entry for all alleleNumbers/locus within LOCIalleles_CE
#todo# need interface to another database with this information, or literature databank where to extract it

# #Bootstrapping functions
# #todo# functions that reavuluate flanking regions based on:
# #    'which rare alleles could be exluded and the benefit this brings to avoiding errors in a locus profile'

# ## <a id="samples">Analysis of (un)known samples</a>

#### General class and functions for working with reads

# #Most of the functions and methods in this section are intended to be run only once on a dataset of reads.
# #If you want to reanalyze the same dataset differently, you have to restart from the beginning.

#General Fastq reads
class Read:
    def __init__(self,fastqEntry):
        """
        Expects a list of length 4 with the typical lines of 1 Fastq entry (def-line1,seq,def-line2,qual)
        """
        #self.id=fastqEntry[0].split()[0][1:] #Fastq read-ID => can be commented out if not used
        self.seq=fastqEntry[1].strip()
        self.qual=fastqEntry[3].strip()
        #Dictionary in which to register quality events:
        self.qualLog={'originalStrand':True, 
                        'withinFlanks':False #Boolean to indicate if sequence has been extracted from flanks
                        } 
        self.locus=None #Locus to which the read belongs. None if not yet assigned, False if no locus matches
    def __str__(self):
        return self.seq
    __repr__=__str__
    def __contains__(self,subseq):
        return subseq in self.seq
    def __len__(self):
        return len(self.seq)
    
    def assignLocus(self,locusDict,extraMethod=None):
        """
        Determines to which locus the read belongs.
        Limited by the loci present in locusDict.
        Possibilities for extraMethod:
            => ('k-mer',x) with x the size of the k-mer used for identifying loci primers
            => ('refseq-k-mer',x)
        """
        for locus in locusDict:
            countF=self.seq.count(locusDict[locus]['ref_forwardP'])
            countR=self.seq.count(complement(locusDict[locus]['ref_reverseP']))
            countFc=self.seq.count(complement(locusDict[locus]['ref_forwardP']))
            countRc=self.seq.count(locusDict[locus]['ref_reverseP'])
            #todo# check indices => forward primer logically has to come before reverse in the sequence
            if (countF+countR+countFc+countRc) > 2 or max(countF,countR,countFc,countRc) > 1:
                if 'ambiguousLocus' in self.qualLog:
                    self.qualLog['ambiguousLocus'].append((locus,(countF,countR,countFc,countRc)))
                else: self.qualLog['ambiguousLocus']=[(locus,(countF,countR,countFc,countRc))]
            elif (countF == countR == 1) or (countFc == countRc == 1): #could use exclusive or here => '^'
                if 'ambiguousLocus' in self.qualLog: self.qualLog['ambiguousLocus'].append(locus)
                elif self.locus:
                    self.qualLog['ambiguousLocus']=[self.locus,locus]
                    self.locus = False #Assigned false as it cannot be determined which locus
                else:
                    self.locus = locus
                    if countFc == countRc == 1:
                        self.seq = complement(self.seq)
                        self.qual = self.qual[::-1]
                        self.qualLog['originalStrand'] = False
        if self.locus is None: self.locus = False
        if not extraMethod: return self
        
        #Extra method for reads that were not assigned yet to a locus
        if not self.locus and not 'ambiguousLocus' in self.qualLog:
            kmerSize = extraMethod[1]
            kID = {self.seq[i:i+kmerSize] for i in range(len(self.seq)-kmerSize+1)}
            
            #Add loci primer kID's if necessary, including reverse strand orientation
            if extraMethod[0]=='k-mer' and not 'primer-kIDs' in locusDict[list(locusDict.keys())[0]]:
                for locus in locusDict.keys():
                    locusDict[locus]['primer-kIDs']={'forward':{locusDict[locus]['ref_forwardP'][i:i+kmerSize]
                                        for i in range(len(locusDict[locus]['ref_forwardP'])-kmerSize+1)},
                                     'reverse_complement':{locusDict[locus]['ref_reverseP'][i:i+kmerSize] 
                                        for i in range(len(locusDict[locus]['ref_reverseP'])-kmerSize+1)}}
                    locusDict[locus]['primer-kIDs']['forward_complement']={complement(l) 
                                                                for l in locusDict[locus]['primer-kIDs']['forward']}
                    locusDict[locus]['primer-kIDs']['reverse']={complement(l) 
                                                        for l in locusDict[locus]['primer-kIDs']['reverse_complement']}
            elif extraMethod[0]=='refseq-k-mer' and not 'refseq-kIDs' in locusDict[list(locusDict.keys())[0]]:
                for locus in locusDict.keys():
                    locusDict[locus]['refseq-kIDs']={'forward':{locusDict[locus]['refseq'][i:i+kmerSize] 
                                                        for i in range(len(locusDict[locus]['refseq'])-kmerSize+1)}}
                    locusDict[locus]['refseq-kIDs']['reverse']={complement(k) 
                                                                for k in locusDict[locus]['refseq-kIDs']['forward']}
            #pdb.set_trace()
            #Calculate loci scores
            if extraMethod[0]=='k-mer': lociScores = {locus: #=> per locus tuple score for forward and reverse strand
                          (len(locusDict[locus]['primer-kIDs']['forward'] & kID) - 
                           len(locusDict[locus]['primer-kIDs']['forward'] - kID) +
                           len(locusDict[locus]['primer-kIDs']['reverse'] & kID) - 
                           len(locusDict[locus]['primer-kIDs']['reverse'] - kID),
                           len(locusDict[locus]['primer-kIDs']['forward_complement'] & kID) - 
                           len(locusDict[locus]['primer-kIDs']['forward_complement'] - kID) +
                           len(locusDict[locus]['primer-kIDs']['reverse_complement'] & kID) - 
                           len(locusDict[locus]['primer-kIDs']['reverse_complement'] - kID))
                          for locus in locusDict}
            elif extraMethod[0]=='refseq-k-mer': lociScores = {locus:
                          (len(locusDict[locus]['refseq-kIDs']['forward'] & kID) - 
                           len(locusDict[locus]['refseq-kIDs']['forward'] - kID),
                           len(locusDict[locus]['refseq-kIDs']['reverse'] & kID) - 
                           len(locusDict[locus]['refseq-kIDs']['reverse'] - kID))
                          for locus in locusDict}
            maximumScore = sorted(lociScores.values(),key=lambda x:max(x))[-1]
            if [s for l in lociScores for s in lociScores[l]].count(max(maximumScore)) != 1: 
                self.qualLog['ambiguousLocus']='ambiguous k-mer locus assignment'
            else:
                for locus,scores in lociScores.items():
                    if scores == maximumScore:
                        self.qualLog['k-mer assignment'] = True
                        self.locus = locus
                        if max(maximumScore) == maximumScore[1]:
                            self.qualLog['originalStrand'] = False
                            self.seq = complement(self.seq)
                            self.qual = self.qual[::-1]
                        return self
        return self
    
    def primerOut(self,locusDict,keepDump=False):
        """
        Cuts out primers and everything before or after.
        Is called automatically by flankOut.
        #todo# reflect index <=> rindex, both for strict primers and k-mer assigned
        """
        try: forward_i = (self.seq.rindex(locusDict[self.locus]['ref_forwardP'])+
                          len(locusDict[self.locus]['ref_forwardP']))
        except ValueError:
            aln = Alignment(locusDict[self.locus]['ref_forwardP'],self.seq,mode='primer-search')
            forward_i = len([a[1] for a in aln.alnment if a[1]!='-'])
        except KeyError:
            if not self.locus: return #In case of not assigned reads
            else: raise
        try: reverse_i = self.seq.index(complement(locusDict[self.locus]['ref_reverseP']))
        except ValueError:
            #For reverse primer both primer and sequence are reversed to find position analogously to forward primer 
            #(closest to the center)
            aln = Alignment(complement(locusDict[self.locus]['ref_reverseP'])[::-1],self.seq[::-1],mode='primer-search')
            reverse_i = len(self.seq)-len([a[1] for a in aln.alnment if a[1]!='-'])
        if keepDump: self.qualLog['dumpedEnds']={'forwardP':{'seq':self.seq[:forward_i],'qual':self.qual[:forward_i]}
                                        ,'reverseP':{'seq':self.seq[reverse_i:],'qual':self.qual[reverse_i:]}}
        self.qual=self.qual[forward_i:reverse_i]
        self.seq=self.seq[forward_i:reverse_i]    
    
    def flankOut(self,locusDict,useCompress=False,withAlignment=False,keepDump=False,autoPrimerOut=True):
        """
        Cuts out the relevant part within the flanks, both the sequence itself and the quality scores
        Expects a locusDict that contains the locus to which the read belongs and the flanks to consider
        Also expects that the read already has been assigned to a locus, by which the sequence 
            should also be correctly oriented
        If useCompress, the homopolymer compression is applied in the flanks to avoid common homopolymer errors
        If keepDump, seq and qual parts that are removed are stored in qualLog if they need to be analyzed later
        If autoPrimerOut, primers are cut out before flanks (as database flanks do not contain primers).
            However, if using reference sequence k-mer assignment, this should be turned off if sequences are 
                not expected to contain the primers.
        """
        if self.qualLog['withinFlanks']: raise Exception("Read already flanked-out")
        if not self.locus: return #raise Exception("Reads have not yet been assigned or filtered")
        #Cut primers and everything before or after
        if autoPrimerOut: self.primerOut(locusDict,keepDump=keepDump)
        #Cut flanks
        #pdb.set_trace()
        try:
            indexF,qualF = Read.getFlankIndex(self.seq,locusDict[self.locus]['flank_forwardP'],'forward',
                                              useCompress=useCompress,withAlignment=withAlignment)
            indexR,qualR = Read.getFlankIndex(self.seq,locusDict[self.locus]['flank_reverseP'],'reverse',
                                              useCompress=useCompress,withAlignment=withAlignment)
            self.qualLog['cleanFlanks'] = (qualF,qualR) 
            if keepDump: self.qualLog['dumpedEnds'].update({
                            'flankF':{'seq':self.seq[:indexF],'qual':self.qual[:indexF]},
                            'flankR':{'seq':self.seq[indexR+1:],'qual':self.qual[indexR+1:]}})
            if indexF <= (indexR+1):
                self.seq=self.seq[indexF:indexR+1]
                self.qual=self.qual[indexF:indexR+1]
                self.qualLog['withinFlanks']=True
                if self.seq == '': self.seq='[RL]' #Reference length sequence
            else:
                self.qual=LocusConflictError(value='Negative length after flanking out',message=(self.seq,self.qual))
                self.seq='[-]' #Negative length sequence
        except IndexError:
            self.qual=LocusConflictError(value='Negative length after primer out')
            self.seq='[-]'
        #if 'N' in self.seq or 'n' in self.seq: self.locus = False #todo# better strategy for bad reads
    
    @staticmethod
    def getReads(fqFilename,randomSubset=None):
        """
        Processes the reads of a fastqfile with forensic loci.
        Returns reads iterator
        If fqFilename.endswith('fasta'):
            transforms a one-lined fasta to the fastq format expected 
            (seq line and quality line the same, so unusable for quality analysis)
        If randomSubset (float 0 < x < 1), a number approximating randomSubset*reads of reads is returned
        If it is desired that the exact same subset is generated => e.g.: from random import seed; seed(1000)
        """
        if randomSubset: from random import random
        legacy = True if fqFilename.endswith(('fasta','fasta.gz')) else False
        #Open gz compressed file
        if fqFilename.endswith('.gz'):
            import gzip
            fq=gzip.open(fqFilename, mode='rt')
        #Open normal file
        else: fq=open(fqFilename)
        #Fasta wrapper to generate one-lined fasta
        if legacy: fq = fastaReader(fq)

        fqcount=4 # == size of fq entry
        for line in fq:
            if (fqcount%4)==0: read=[line]
            else: read.append(line)
            if (fqcount%4)==3:
                if not randomSubset or (random() < randomSubset): yield Read(read)
            fqcount+=1
            if legacy and (fqcount%4)==2:
                read.append(read[0])
                read.append(read[1])
                if not randomSubset or (random() < randomSubset): yield Read(read)
                fqcount=4
        
    @staticmethod
    def selfAssignLocus(reads,locusDict,extraMethod=None):
        """
        Expects a iterable of Read instances. Calls their assignLocus method.
        Deprecated: use Analysis.processReads instead.
        """
        from warnings import warn
        warn("Deprecated: should use an Analysis object method to assign reads to loci")
        return [read.assignLocus(locusDict,extraMethod=extraMethod) for read in reads]
        
    @staticmethod
    def getFlankIndex(seq,flank,orientation,useCompress=False,withAlignment=False):
        """
        Expects: sequence, flank sequence, and orientation of flank (forward or reverse)
        The sequence itself always has to be given in forward orientation.
        Calculates the most likely index position of the first non-flanking base.
        Returns this index, and the quality indicating if exact flank, compressed exact flank or not.
        Assumes the starting position of the sequence and flank are the same (in forward orientation)
        If useCompress, the homopolymer compression is applied to avoid common homopolymer errors
        If withAlignment, the Alignment class is used with its flank index functionality
        """
        if not flank: #If no flank, return 0 as index, and None for quality
            return (0 if orientation != 'reverse' else len(seq),None)
        if orientation == 'reverse':
            seq=complement(seq)
            orientation=False
        if seq.startswith(flank):
            if orientation: return (len(flank),'clean')
            else: return (len(seq)-len(flank)-1,'clean')
        if useCompress:
            uncompressedSeq=seq
            seq=compress(seq)
            #Determine homopolymer length at end flank (Heuristic solution)
            flankEndHPL = -1 # starts with -1 as not to correct for single base 'homopolymer'
            for i in range(len(flank)-1,-1,-1):
                if flank[-1] != flank[i]: break
                flankEndHPL+=1
            flank=compress(flank)
            if seq.startswith(flank):
                for windex in range(len(flank),len(uncompressedSeq)):
                    if compress(uncompressedSeq[:windex]) == flank: break            
                if orientation: return (windex+flankEndHPL,'clean_compressed')
                else: return (len(uncompressedSeq)-(windex+flankEndHPL)-1,'clean_compressed')
        
        if withAlignment:
            #First an alignment is tried with a shorter sequence (just 10 bases longer than the flank)
            #If the found index is to close to the end (within last 5bp), the flank is searched on the full sequence
            #TODO# this could be implemented directly in Alignment
            windex = Alignment(flank,seq[:len(flank)+10],'flank-index').flankOutIndex
            if windex > len(flank)+5: windex = Alignment(flank,seq[:len(flank)+10],'flank-index').flankOutIndex
        else: #k-mer flank index finding algorithm
            stats=[]
            for flanki in range(len(flank),0,-1):
                #pdb.set_trace()
                stats.append([])
                for flankii in range(flanki-1,-1,-1):
                    findClosestI = seq.split(flank[flankii:flanki])
                    if len(findClosestI)==1: break #Did not find k-mer
                    closestI = -1
                    for fI in findClosestI:
                        if abs(closestI + (len(fI)+1) + (flanki-flankii-1) - (flanki-1) ) <= abs(closestI - (flanki-1)):
                            closestI += (len(fI)+1) + (flanki-flankii-1)
                        else: break
                    stats[-1].append(closestI+(len(flank)-flanki))
            #Score stats
            indexScores={}
            for i in range(len(stats)):
                for ii in range(len(stats[i])):
                    if stats[i][ii] not in indexScores: indexScores[stats[i][ii]]=0
                    indexScores[stats[i][ii]]+= int((i*ii)**(0.5))    
            #Winning index
            #pdb.set_trace()
            windex=sorted(indexScores,key=lambda x:indexScores[x],reverse=True)[0]
            
        if useCompress:
            compressedFlank=seq[:windex+1]
            for windex in range(windex,len(uncompressedSeq)):
                if compressedFlank == compress(uncompressedSeq[:windex+1]): break
            windex+=flankEndHPL
            seq=uncompressedSeq
            
        if orientation: return (windex+1,'unclean')
        else: return (len(seq)-(windex+1)-1,'unclean')
        #windex +1 because we search on the last flank base, but the first non-flank has to be returned
        #todo#make an alignment based on the proposed index (end-to-end) and return its quality

#Consensus read
class ConsensusRead:
    def __init__(self,readsList,consensusThreshold=0.99):
        """
        The instance represents the consensus of a set of reads
        The reads have to be in the same orientation and of the same length
        Positions without consensus are marked by an X
        """
        self.reads = readsList
        reads = [r.seq for r in readsList]
        readLength={len(r) for r in reads}
        if len()!=1: raise Exception('Reads not all of the same length')
        else: readLength=readLength.pop()
        self.consensus=[{} for i in range(readLength)]
        for r in reads:
            for i in range(readLength):
                try: self.consensus[i][r[i]]+=1
                except KeyError: self.consensus[i][r[i]]=1
        readNumber=float(len(reads))
        self.consensus=[{base:c[base]/readNumber for base in c} for c in self.consensus]
        self.seq=''.join([sorted(c,key=lambda x: c[x],reverse=True)[0] if max(c.values()) >= threshold else 'X' 
                          for c in self.consensus])
    
    @staticmethod
    def sortReadsPerLength(readsList):
        """
        Returns a dict with keys 'seq lengths' and values 'list of corresponding reads'
        """
        readsDict={}
        for r in readsList:
            try: readsDict[len(r.seq)].append(r)
            except KeyError: readsDict[len(r.seq)]=[r]
        return readsDict


#Loci
class Locus:
    def __init__(self,locusName,readsList=None,locusDict=None,threshold=0,stutterBuffer=False,maxCluster=50):
        """
        Extracts from a list of reads those reads that claim to belong to the locus.
        The Locus instance than offers methods for extracting alleles in the set of reads,
        calculate their abundances within the set, and perform quality checks.
        If stutterBuffer, flanks of reads are shortened by stutterBuffer x repeatsize of locus;
        this prevents having reads with negative length of a significant abundance.
        #todo# stutterbuffer could be implemented to work dynamically instead of statically
        maxCluster is the maximum number of uniques the locus will consider to try and analyze the relations
        """
        self.name = locusName
        self.info = locusDict[locusName] if locusDict else None
        if stutterBuffer and self.info['locusType']:
            self.stutterBuffer = stutterBuffer
        else: self.stutterBuffer=False #stutterBuffer standard False
        if readsList: self.reads = [read for read in readsList if read.locus == locusName]
        else: self.reads = []
        self.threshold = threshold
        self.maxCluster = maxCluster
    def __str__(self):
        return self.name
    def __repr__(self):
        return str(len(self.reads))+' reads in '+self.name
        
    def filterBadReads(self):
        """
        The list of reads for a locus can contain bad reads not useful for further analysis.
        This method removes them from the main locus self.reads and puts them in self.badReads
        #todo# for the moment only negative reads are being filtered, other quality checks could also be made
        #todo# before introducing k-mer assignment this was not necessary for negative length flanked out reads
        """
        self.badReads = [r for r in self.reads if r.seq == '[-]']
        self.reads = [r for r in self.reads if r.seq != '[-]']
    
    def correctForstutterBuffer(self):
        """
        DEPRECATED
        If stutterBuffer is applied only to see the smallest stutters, read-ends can to be corrected before 
        setting uniqueReads, to regroup pairs of reads that have mismatches compared to the database in the flank
        ends that were not removed.
        Flank qualities are changed to unclean if the ends get switched for the database-ends.
        This is not ideal, but the relevance and impact of stutterBuffer is small.
        #todo#stutterBuffer should just safe the stutters in qualLog,
                and then when writing xml out, they (consensus) should be reappended to uniqueSeq
        """
        for read in self.reads:
            if read.seq in ('[-]','[RL]'): continue
            if not read.seq.startswith(self.info['removed_from_flank_forwardP']):
                #forwardCorrected = True #todo# if both flank ends overlap the result is consistent but not optimal
                read.seq = (self.info['removed_from_flank_forwardP']+
                            read.seq[len(self.info['removed_from_flank_forwardP']):])
                read.qualLog['cleanFlanks'] = ('unclean',read.qualLog['cleanFlanks'][1])
            if not read.seq.endswith(complement(self.info['removed_from_flank_reverseP'])):
                read.seq = (read.seq[:len(read.seq)-len(self.info['removed_from_flank_reverseP'])]+
                            complement(self.info['removed_from_flank_reverseP']))
                read.qualLog['cleanFlanks'] = (read.qualLog['cleanFlanks'][0],'unclean')
    
    def setUniqueReads(self):
        """
        (Re)sets the uniqueReads attribute, by analyzing the Locus' reads
        Result will depend on the flankout process.
        """
        self.uniqueReads = {}
        self.uniqueForwards = {}
        for read in self.reads:
            try:
                self.uniqueReads[read.seq]+=1
                if read.qualLog['originalStrand']: self.uniqueForwards[read.seq]+=1
            except KeyError:
                self.uniqueReads[read.seq]=1
                self.uniqueForwards[read.seq] = 1 if read.qualLog['originalStrand'] else 0
    
    def setReadAbundances(self,thresholdLoop=True):
        """
        Calculate the abundances of unique flanked out reads, considering locus threshold. 
            (read abundance has to be greater than threshold)
        If uniqueReads has been determined without flanking out, abundancies will be calculated as such.
        If thresholdLoop: lowest abundant uniques are removed first, until no uniques are under the threshold
        """
        #pdb.set_trace()
        threshold = self.threshold
        #Calculate abundances
        if not thresholdLoop:
            totalReads=float(sum(self.uniqueReads.values()))
            filteredReads={read:self.uniqueReads[read] for read in self.uniqueReads 
                                    if self.uniqueReads[read]/totalReads > threshold}
        else:
            uniqueCounts=sorted(set(self.uniqueReads.values()),reverse=True)
            for minimumReadsForThreshold in uniqueCounts:
                filteredReads=[v for v in self.uniqueReads.values() if v >= minimumReadsForThreshold]
                totalReads = float(sum(filteredReads))
                if float(min(filteredReads))/totalReads <= threshold:
                    minimumReadsForThreshold = uniqueCounts[uniqueCounts.index(minimumReadsForThreshold)-1]
                    break
            filteredReads={read:self.uniqueReads[read] for read in self.uniqueReads 
                                    if self.uniqueReads[read] >= minimumReadsForThreshold}   
        totalFiltered=float(sum(filteredReads.values()))
        self.uniqueAbundances = {read:filteredReads[read]/totalFiltered for read in filteredReads}
   
    def getReadAbundances(self):
        """
        Return self.uniqueAbundances
        """
        try: return self.uniqueAbundances
        except AttributeError:
            self.setReadAbundances()
            return self.uniqueAbundances
    
    def calculateFlankStats(self,perFlank=False):
        """
        Analyses the quality of the flankout per unique read.
        Assigns it to the instance attribute flankStats, which is a dictionary with unique reads as keys, 
        and for values {clean:%, clean_compressed:%, unclean:%) if not perFlank.
        If perFlank, then the valuekeys are the original read quality tuples.
        """
        #pdb.set_trace()
        if perFlank:
            self.qualFlanks={ur:{'clean':0,'clean_compressed':0,'unclean':0,None:0} for ur in self.uniqueReads}
            for r in self.reads:
                if r.qualLog['cleanFlanks'] not in self.qualFlanks[r.seq]:
                    self.qualFlanks[r.seq][r.qualLog['cleanFlanks']] = 0
                self.qualFlanks[r.seq][r.qualLog['cleanFlanks']] += 1
        else:
            self.qualFlanks={ur:{'clean':0,'clean_compressed':0,'unclean':0,None:0} for ur in self.uniqueReads}
            for r in self.reads:
                for q in r.qualLog['cleanFlanks']: self.qualFlanks[r.seq][q]+=1
        #Transform to % per uniqueRead
        self.qualFlanks={k1:{k2:format(100.*float(self.qualFlanks[k1][k2])/float(sum(self.qualFlanks[k1].values())),
                                       '.1f')+'%' for k2 in self.qualFlanks[k1]} for k1 in self.qualFlanks}
    def compareKnownAlleles(self,sql=None):
        """
        Looks up if a region of interest is present in the database.
        Stores results in self.knownAlleles
        """
        self.knownAlleles = {}
        #if not sql: conn,sql = login()
        #else: conn = None
        for uR in self.uniqueReads:
            if uR == '[RL]': uRsql = '' #Necessary as database does not contain '[RL]' but empty strings for RL-alleles
            else: uRsql = uR
            #if self.stutterBuffer: #should no longer be necessary with Analysis stutter and flankOut temp db tables
            #    if (len(uR) < len(self.info['removed_from_flank_forwardP']) + 
            #        len(self.info['removed_from_flank_reverseP'])): uRsql = '[-]'
                #CHECK# next lines need to change with new temporary LOCIalleles table implementation
                #sql.execute('SELECT alleleNumber,alleleNomen FROM LOCIalleles WHERE locusName = %s \
                #             AND CONCAT(%s,alleleSeq,%s) = %s', (self.name,self.info['removed_from_flank_forwardP'],
                #            complement(self.info['removed_from_flank_reverseP']),uRsql))
            #else: 
            sql.execute('SELECT alleleNumber,alleleNomen FROM LOCIalleles WHERE locusName = %s AND alleleSeq = %s',
                        (self.name,uRsql))
            if sql.rowcount == 1:
                annotation = sql.fetchone()
                if annotation['alleleNumber']:
                    alleleNumber=str(annotation['alleleNumber'])
                    if alleleNumber.endswith('.0'): alleleNumber=alleleNumber[:-2]
                    self.knownAlleles[uR]=(alleleNumber,annotation['alleleNomen']) #number,subtype
                else: self.knownAlleles[uR]=str(annotation['alleleNomen'])
            elif sql.rowcount == 0: self.knownAlleles[uR]='NA'
            else: raise LocusConflictError('Too many alleles')
        #if conn: logout(conn,sql)
    
    def getUniqueSorted(self,reverse=False):
        """
        Returns sorted list of uniqueReads above threshold
        If reverse True, the sequences will be sorted from bigger to smaller
        """
        try: return self.uniqueSorted
        except AttributeError:
            self.uniqueSorted = sorted(sorted(self.uniqueAbundances,key = lambda x: len(x), reverse=reverse),
                                       key = lambda x: '[' in x, reverse=(not reverse))
            return self.uniqueSorted
    
    def clusterUniqueReads(self,maxDifferences=2): #todo# trueReadsPresent=True,errorSQL=False
        """
        Calculate clustering information for the unique reads.
        Clustering is performed stepwise, per allowed number of differences.
        A difference can be a SNP or an INDEL of 1 or as long as the locus type (relevant for STR loci)
        uniqueReads under threshold are not taken in consideration
        #todo# for loci with a lot of reads, could make it more linear by clustering in groups (e.g. 1:10;5:15,10:20 ..)
                would also require using more advanced heuristic to first cluster same-sized reads 
                (k-mer based or something else)
        """
        self.uniqueClusterInfo={}
        #Give each uR index
        index = 1
        for uR in self.getUniqueSorted():
            self.uniqueClusterInfo[uR]=(index,{})
            index+=1
        if len(self.uniqueClusterInfo) > self.maxCluster:
            raise Exception('More than '+str(self.maxCluster)+' sequences to cluster')
        uniqueSorted = self.getUniqueSorted()
        uniqueLength = len(uniqueSorted)
        for uRi in range(uniqueLength):
            uR = uniqueSorted[uRi]
            for uRmatchi in range(uRi+1,uniqueLength):
                uRmatch = uniqueSorted[uRmatchi]
                #Heuristics to avoid aligning unnecessary
                if uR == '[RL]' or uR == '[-]' or (self.info['locusType'] and
                                                   (len(uR)-len(uRmatch) > maxDifferences*self.info['locusType'])): break 

                if  uRmatch == '[-]' or (len(uRmatch)==len(uR) and sum([len(set((a,b))) == 2 
                                          for a,b in zip(uR,uRmatch)]) > maxDifferences): continue
                #Align to calculate differences
                differences = Alignment(uR,uRmatch,stutter=self.info['locusType']).getDifferences()
                if differences <= maxDifferences:
                    try: self.uniqueClusterInfo[uR][1][differences].append(self.uniqueClusterInfo[uRmatch][0])
                    except KeyError: self.uniqueClusterInfo[uR][1][differences]=[self.uniqueClusterInfo[uRmatch][0]]
                    try: self.uniqueClusterInfo[uRmatch][1][differences].append(self.uniqueClusterInfo[uR][0])
                    except KeyError: self.uniqueClusterInfo[uRmatch][1][differences]=[self.uniqueClusterInfo[uR][0]]
    
    def getClusterXMLForUnique(self,uniqueRead):
        """
        Returns XML element of cluster information for a unique read
        Higher up functions should put the call in a try-block
        """
        try: clusterInfo = self.uniqueClusterInfo[uniqueRead]
        except AttributeError:
            self.clusterUniqueReads()
            clusterInfo = self.uniqueClusterInfo[uniqueRead]
        import xml.etree.ElementTree as ET
        cluster = ET.Element('cluster-info')
        cluster.set('index',str(clusterInfo[0]))
        connections=0
        cluster.set('orders',str(len(clusterInfo[1])))
        for c in sorted(clusterInfo[1]):
            differences =  ET.SubElement(cluster,'differences')
            differences.set('amount',str(c))  
            for relative in clusterInfo[1][c]:
                related =  ET.SubElement(differences,'rel')
                related.set('index',str(relative))
                connections+=1
        cluster.set('connections',str(connections))
        cluster.tail = '\n\t'
        return cluster
    
    def analyze(self,badReadsFilter=False,clusterInfo=True,sql=None,verbose=False):
        """
        Performs all necessary analysis steps for a locus
        and saves the result in self.xml
        """
        import xml.etree.ElementTree as ET
        
        if verbose: print('Analyze',self.name)
        
        if badReadsFilter:
            self.filterBadReads()
        self.setUniqueReads()
        filteredReads = self.getReadAbundances()
        self.calculateFlankStats()
        self.compareKnownAlleles(sql=sql)
        #Make xml for locus
        self.xml = ET.Element('locus')
        self.xml.set('name',self.name)
        self.xml.set('reads',str(len(self.reads)))
        if badReadsFilter: self.xml.set('badReads',str(len(self.badReads)))
        self.xml.set('uniqueReads',str(len(self.uniqueReads)))
        self.xml.set('uniqueFiltered',str(len(filteredReads)))
        self.xml.set('readsFiltered',str(sum([self.uniqueReads[fR] for fR in filteredReads])))
        self.xml.text = '\n\t'
        self.xml.tail = '\n'
        for pR in self.getUniqueSorted(): #returns sorted list of filtered uniqueReads
            allele = ET.SubElement(self.xml,'alleleCandidate')
            allele.set('abundance',format(filteredReads[pR]*100.,'.2f')+'%')
            if type(self.knownAlleles[pR]) == tuple:
                allele.set('db-name',self.knownAlleles[pR][0])
                allele.set('db-subtype',self.knownAlleles[pR][1])
            else: allele.set('db-name',self.knownAlleles[pR])

            #Allele candidate length info
            if pR == '[-]': alleleSize = '-1'
            elif not self.info['locusType']: alleleSize = str(len(pR))
            else: alleleSize = calculateAlleleNumber(pR if pR != '[RL]' else '',self.info)
            allele.set('size',alleleSize)
            #end allele candidate length info
            allele.set('direction-distrib',format(100.*self.uniqueForwards[pR]/self.uniqueReads[pR],'.2f')+'%')
            allele.text='\n\t\t'
            allele.tail = '\n\t'
            alleleSub =  ET.SubElement(allele,'regionOfInterest')
            alleleSub.text = pR
            alleleSub.tail = '\n\t\t'
            alleleSub =  ET.SubElement(allele,'qualityFlanks')
            alleleSub.set('clean',self.qualFlanks[pR]['clean'])
            alleleSub.set('unclean',self.qualFlanks[pR]['unclean'])
            alleleSub.set('clean_compressed',self.qualFlanks[pR]['clean_compressed'])
            if not clusterInfo: alleleSub.tail = '\n\t'
            else:
                alleleSub.tail = '\n\t\t'
                if len(filteredReads) < self.maxCluster: #Maximum sequences to cluster
                    try: allele.append(self.getClusterXMLForUnique(pR))
                    except KeyError: print('Missing key (',pR,') in cluster-info') 
                else:
                    cluster = ET.SubElement(allele,'cluster-info')
                    cluster.set('remark','too many sequences to cluster')
                    cluster.tail = '\n\t'
        try: allele.tail = '\n'
        except NameError: print(self.name,'has no filtered alleles')
        return self
    
    @staticmethod
    def categorisePerLocus(locusDict,readsList,threshold=0,stutterBuffer=False):
        """
        Expects a locusDict with keys that represent all the loci to be analysed, 
        and the list of reads to categorise.
        Returns the set of loci
        """
        from warnings import warn
        warn("Deprecated")
        return {Locus(locusName,readsList,locusDict,threshold=threshold,stutterBuffer=stutterBuffer) 
                for locusName in locusDict}        

    @staticmethod
    def select(locusName,lociSet):
        """
        Static method to return the locus with locusName from a set of loci.
        """
        for locus in lociSet:
            if locus.name == locusName: return locus

    @staticmethod
    def getLocusDict(kitName=None,primerBuffer=False,sql=None):
        """
        Reads the MySQL table with locus relevant information, and returns it as a dict accessible by locusName
        """
        #if not sql: conn,sql=login()
        #else: conn = None
        if not kitName:
            sql.execute("SELECT * FROM LOCInames")
            locusDict={locus['locusName']:locus for locus in sql.fetchall()}
        else:
            sql.execute("SELECT locusName FROM LOCIkits WHERE kitName = %s",(kitName))
            locusDict={}
            for locus in sql.fetchall():
                sql.execute("SELECT * FROM LOCInames WHERE locusName = %s",(locus['locusName']))
                locusDict[locus['locusName']]=sql.fetchone()
        #if conn: logout(conn,sql)
        if primerBuffer:
            for l in locusDict:
                locusDict[l]['ref_forwardP']=locusDict[l]['ref_forwardP'][primerBuffer:]
                locusDict[l]['ref_reverseP']=locusDict[l]['ref_reverseP'][primerBuffer:]
        return locusDict   

    @staticmethod
    def makeLocusDict(inputType=None,submit=False,kitName=None):
        """
        Makes a locusDict similar to Locus.getLocusDict with user-provided information.
        Optionally provided by means of inputType: csv,xml format. => give tuple e.g. ('csv','csv_filename')
        
        If submit, each entry from the locusDict will be added to BASEtech.
        If kitName is provided, a sequencing kit will be added to LOCIkits.
        
        Important: ReversePrimer should be the actual primer sequence (5'-3' orientation on complementary strand)
        
        FORMATS
        -------
        csv -> e.g. file.csv. LocusType => either int for STR number, or SNP if non-STR locus
        ===================================================
        #Locus,LocusType,ForwardPrimer,ReversePrimer
        FGA,4,GGCTGCAGGGCATAACATTA,ATTCTATGACTTTGCGCTTCAGGA
        Amelogenin,SNP,CCCTGGGCTCTGTAAAGAA,ATCAGAGCTTAAACTGGGAAGCTG
        PentaD,5,GAAGGTCGAAGCTGAAGTG,ATTAGAATTCTTTAATCTGGACACAAG
        """
        locusDict={}
        if inputType and inputType[0] == 'csv':
            for line in open(inputType[1]):
                if line.strip().startswith('#'): continue
                line=line.strip()
                locus,locusType,primerF,primerR=line.split(',')
                primerF = primerF.upper()
                primerR = primerR.upper()
                try: locusType = int(locusType)
                except ValueError: locusType = 0
                locusDict[locus] = {'locusName':locus,'locusType':locusType,
                                    'ref_forwardP':primerF,'ref_reverseP':primerR}
        elif inputType and inputType[0] == 'locusDict':
            locusDict = inputType[1]
        elif inputType and inputType[0] == 'xml':
            NotImplemented
        else:
            while 1:
                locusName = input('LocusName: ')
                locusDict[locusName] = {'locusName':locusName}
                locusDict[locusName]['locusType'] = int(input('locusType: '))
                locusDict[locusName]['ref_forwardP'] = input('Forward primer: ')
                locusDict[locusName]['ref_reverseP'] = input('Reverse primer: ')
                if input('Continue adding loci? (Y/N) ') == 'N': break
        
        if submit:
            for locusName in locusDict: makeLocusEntry(locusDict[locusName]['ref_forwardP'],
                                                       locusDict[locusName]['ref_reverseP'],
                                                       locusName, locusDict[locusName]['locusType'],
                                                       technology=None,filterLevel=None)
        
        if kitName:
            conn,sql = login()
            sql.execute("SELECT * FROM LOCIkits WHERE kitName = %s",(kitName))
            if sql.rowcount != 0:
                if 'Y' == input("kitName ("+kitName+") already in use, overwrite? (Y/N) "):
                    sql.execute("DELETE FROM LOCIkits WHERE kitName = %s",(kitName))
                else: return locusDict
            for locusName in locusDict:
                sql.execute("INSERT INTO LOCIkits (kitName,locusName) VALUES (%s,%s)",(kitName,locusName))
            logout(conn,sql)
        return locusDict
            


# Analysis
#=========
class Analysis:
    #All parameters in the docstring need to be followed by '=>' on a line of their own, 
    #and if the default value (None/False) is different from expected type when used, the line should end with [type]
    #for automatic processing of commandline options
    def __init__(self,fqFilename,sampleName='',kitName='Illumina',maintainAllReads=True,negativeReadsFilter=True,
                 kMerAssign=False,primerBuffer=0,flankOut=False,stutterBuffer=1,useCompress=True,withAlignment=False,
                 threshold=0.005,clusterInfo=True,randomSubset=None,processNow=True,parallelProcessing=0,verbose=False):
        """
        Sets up an analysis of loci for a specific kit
            fqFilename => Fastq file on which to perform the analysis
            sampleName => In case it is a random fastq filename, a more descriptive sample reference
            kitname => name of the loci-kit (in database)
            maintainAllReads => saves also the full read list in the analysis object
            negativeReadsFilter => '[-]' reads are filtered 
                                    (negative reads result from either being bad reads, 
                                        or by being analyzed by an incomplete database)
            kMerAssign => include k-mer assignment possibilty for reads to be assigned to a locus 
                          (#TODO# if list, only for those lociNames), e.g.:
                kMerAssign=('k-mer',5) => primer k-mer assign with wordsize 5
                kMerAssign=('refseq-k-mer',5) => reference sequence k-mer assign with wordsize 5
            primerBuffer => int: shortens with int bp the primer (outer) in locusDict to assign
                                    more reads that have bad primerends (not tested using with kMerAssign)
            flankOut => bool, default True. 
                If False, only primerOut: this is usefull to explore for new alleles (non current-database alleles),
                                          or to explore the quality of the sample without flanking out
            stutterBuffer => int: shortens with int repeatsize the flanks (inner) in locusDict 
                             to be sure stutters are not over flanked out
            useCompress => compress method is also tried in flanking out
            withAlignment => flanking out is done with flanking alignment (see Alignment) instead of k-mer algorithm
            threshold => abundance level under which unique reads will be discarded
            clusterInfo => cluster filtered unique reads and provide info
            randomSubset => 0 < r < 1: takes a random subset of the reads for analysis (+-randomSubset * #reads) [float]
            processNow => bool, default True: processing is started during Analysis object setup
            parallelProcessing => False for single process, int for number of processes to use (ideally <= #cpu's)
            verbose => bool, default False: show progress
        """
        #Save analysis characteristics
        self.fqFilename = fqFilename
        self.sampleName = sampleName
        self.kitName = kitName
        self.maintainAllReads = maintainAllReads
        self.negativeReadsFilter = negativeReadsFilter
        self.kMerAssign = kMerAssign
        self.primerBuffer = primerBuffer
        self.flankOut = flankOut
        self.stutterBuffer = stutterBuffer
        self.useCompress = useCompress
        self.withAlignment = withAlignment
        self.threshold = threshold
        self.clusterInfo = clusterInfo
        self.randomSubset = randomSubset
        self.parallelProcessing = parallelProcessing
        self.verbose = verbose
        
        #Prepare analysis
        self.prepAnalysis()

        #Processing file containing reads
        if processNow:
            try: self.processFQ()
            finally:
                if self.parallelProcessing: ipcluster('stop',self.ipcluster_process)
            
    # def __del__(self):
    #     """
    #     Disconnects the sql attribute upon deletion of the Analysis instance
    #     """
    #     logout(self.conn,self.sql)
        
    def prepAnalysis(self,**kwargs):
        """
        Groups commands for general preparation to start analysis.
        Can be run again, to perform analysis with different parameters, which can be given as keyword arguments.
        E.g. analysis.prepAnalysis(flankOut=False), will prep the Analysis object again for processing without flankOut.
        See Analysis docstring for parameters
        """
        #Check if Analysis atributes need to be changed
        for kw in kwargs: self.__dict__[kw] = kwargs[kw]
        
        #Make sql connection for analysis (connection remains open until Analysis object is deleted)
        self.conn,self.sql = login()
        
        #Prepare locusDict for analysis
        self.locusDict = Locus.getLocusDict(kitName=self.kitName,primerBuffer=self.primerBuffer,sql=self.sql)
        self.preppedLocusDict = False
        if self.stutterBuffer or not self.flankOut: self.prepLocusDict()
        
        #Set up parallel processing if required
        if self.parallelProcessing == 'InsideEngine': return
        elif self.parallelProcessing: self.setupParallelProcessing()        
    
    def processFQ(self):
        """
        Processes the reads of a fastqfile with forensic loci.
        Returns the loci after performing all necessary analysis methods.
        """
        reads = self.processReads()
        
        #Make objects for the loci (not containing reads)
        self.loci = {locusName:Locus(locusName,None,self.locusDict,threshold=self.threshold,
                                     stutterBuffer=self.stutterBuffer) for locusName in self.locusDict}
        for read in reads:
            try: self.loci[read.locus].reads.append(read)
            except KeyError:
                if read.locus: raise
        
        #REMOVE LINE# if self.flankOut: #With new prepLocusDict should now work also for no flankOut situation
        for locus in sorted(self.loci): self.loci[locus].analyze(badReadsFilter=(self.negativeReadsFilter or
                                                                 bool(self.kMerAssign)), clusterInfo=self.clusterInfo,
                                                                 sql=self.sql,verbose=self.verbose)
        if self.maintainAllReads: self.reads = reads

    def processReads(self):
        """
        Makes an iterable of Read instances. Calls their assignLocus method.
        """
        reads = Read.getReads(self.fqFilename,self.randomSubset)
        #Subset reads for debugging
        #from itertools import islice
        #reads = islice(reads,100000)
        #gubed
        
        if self.parallelProcessing:
            return dview.map_sync(lambda x: analysis.processRead_px(x),reads)
        else: #Single process
            reads = [read.assignLocus(self.locusDict,extraMethod=self.kMerAssign) for read in reads]
            for read in reads:
                #For small reads, were the primers are larger than the read it self an exception will be returned
                #those reads should be marked as unsuitable
                #TODO# Implement this also for parallel processing
                try: read.flankOut(self.locusDict,useCompress=self.useCompress,withAlignment=self.withAlignment)
                except:
                    read.locus = False
            return reads

    def processRead_px(self,read):
        """
        Processes a read in a parallel computing context
        """
        read.assignLocus(self.locusDict,extraMethod=self.kMerAssign)
        read.flankOut(self.locusDict,useCompress=self.useCompress,withAlignment=self.withAlignment)
        return read
    
    def setupParallelProcessing(self):
        """
        Prepares ipengines for parallel processing
        """
        #Starting ipcluster
        self.ipcluster_process = ipcluster(numberOfEngines=self.parallelProcessing)
        #to restart => self.ipcluster_process = ipcluster('restart',self.ipcluster_process)
        
        import time
        from itertools import count
        time.sleep(1)
        from IPython.parallel import Client,Reference
        try: client = Client()
        except FileNotFoundError:
            time.sleep(1)
            client = Client()
        count = count()
        while len(client.ids) < self.parallelProcessing:
            time.sleep(1)
            if next(count) == 10: raise Exception('Not all ipengines registered within 10 seconds')
        
        global dview,lview
        dview = client[:]
        lview = client.load_balanced_view()
        
        #Prepping engines
        #debug
        #!ipython nbconvert --to python MyFLq.ipynb #TO REMOVE IN PRODUCTION VERSION
        #gubed
        dview.execute('from MyFLq import complement,Read,Analysis')
        dview.execute("analysis=Analysis(fqFilename=None,kitName='"+self.kitName
                      +"',maintainAllReads=False,negativeReadsFilter="+str(self.negativeReadsFilter)
                      +",kMerAssign="+str(self.kMerAssign)+",primerBuffer="+str(self.primerBuffer)
                      +",flankOut="+str(self.flankOut)+",stutterBuffer="+str(self.stutterBuffer)
                      +",useCompress="+str(self.useCompress)+",withAlignment="+str(self.withAlignment)
                      +",threshold=None,clusterInfo=None,processNow=False,parallelProcessing='InsideEngine')")
        #dview.push({'locusDict':self.locusDict}) #Engines now retrieve their own locusDict with same parameters
        #self.analysis_px = Reference('analysis') #only seems to work with dview.apply and not with dview.map

    def prepLocusDict(self):
        """
        For some Analysis options the locusDict needs to be altered compared to the database retrieved version.
        Also a new temporary LOCIalleles table is prepared, with alleles matching this altered locusDict.
        
        In case of no flankOut:
            flanks become empty strings and are stored in removed_from_flank*
        
        In case of stutterBuffer:
            For analysis purposes it is useful to observe the stutters.
            The maximal ROIs as implemented in the database, can create reads with a negative length,
            apparently causing the smallest alleles to be without stutters.
            To observe also the stutters of the smallest alleles, Analysis.prepLocusDict shortens the flanks,
            with Analysis.stutterBuffer x repeatSizeLocus.
        """
        if self.preppedLocusDict: return #Can only be executed once
        for locus in self.locusDict:
            if not self.flankOut:
                self.locusDict[locus]['flank_forwardP'],self.locusDict[locus]['removed_from_flank_forwardP'] = ('',
                                                                            self.locusDict[locus]['flank_forwardP'])
                self.locusDict[locus]['flank_reverseP'],self.locusDict[locus]['removed_from_flank_reverseP'] = ('',
                                                                            self.locusDict[locus]['flank_reverseP'])
                continue
            if not self.locusDict[locus]['locusType']: #Irrelevant for SNP loci if stutterBuffer and flankOut
                self.locusDict[locus]['removed_from_flank_forwardP'] = ''
                self.locusDict[locus]['removed_from_flank_reverseP'] = ''
            if len(self.locusDict[locus]['flank_forwardP']) > self.stutterBuffer*self.locusDict[locus]['locusType']:
                self.locusDict[locus]['removed_from_flank_forwardP'] = self.locusDict[locus]['flank_forwardP'][
                                                               -self.stutterBuffer*self.locusDict[locus]['locusType']:]
                self.locusDict[locus]['flank_forwardP'] = self.locusDict[locus]['flank_forwardP'][
                                                             :-self.stutterBuffer*self.locusDict[locus]['locusType']]
            else: self.locusDict[locus]['removed_from_flank_forwardP'] = ''
            if len(self.locusDict[locus]['flank_reverseP']) > self.stutterBuffer*self.locusDict[locus]['locusType']:
                self.locusDict[locus]['removed_from_flank_reverseP'] = self.locusDict[locus]['flank_reverseP'][
                                                              -self.stutterBuffer*self.locusDict[locus]['locusType']:]
                self.locusDict[locus]['flank_reverseP'] = self.locusDict[locus]['flank_reverseP'][
                                                             :-self.stutterBuffer*self.locusDict[locus]['locusType']]
            else: self.locusDict[locus]['removed_from_flank_reverseP'] = ''
        self.preppedLocusDict = True
        
        #Making temporary database table 
        if self.parallelProcessing == 'InsideEngine': return #Not necessary for Engines (currently!!)
        self.sql.execute("""
        CREATE TEMPORARY TABLE changedAlleleEnds (
        `locusName` CHAR(40) NOT NULL UNIQUE KEY COMMENT 'identification of the locus',
        `removed_from_flank_forwardP` TEXT(1000),
        `removed_from_flank_reverseP` TEXT(1000)        
        )
        COMMENT 'temporary table for recalculating alleles';
             """)
        for locus in self.locusDict:
            self.sql.execute("""INSERT INTO changedAlleleEnds 
            (locusName,removed_from_flank_forwardP,removed_from_flank_reverseP) VALUES (%s,%s,%s)""",
                             (locus,self.locusDict[locus]['removed_from_flank_forwardP'],
                              complement(self.locusDict[locus]['removed_from_flank_reverseP'])))
        #The next statement statement masquerades LOCIalleles
        #If this does not work with some SQL version, first make temporary table with another name, then masquerade.
        self.sql.execute("""
        CREATE TEMPORARY TABLE LOCIalleles
            SELECT LOCIalleles.locusName,alleleNumber,alleleNomen,
            CONCAT(removed_from_flank_forwardP,LOCIalleles.alleleSeq,removed_from_flank_reverseP) AS alleleSeq 
            FROM LOCIalleles JOIN changedAlleleEnds USING (locusName)
        """)

    #Make report
    def makeReport(self,fileName=False,stylesheet=False,appendLocusDict=True):
        """
        Expects a set of analyzed loci.
        Prints out, or saves to file fileName the XML results
        if stylesheet: css stylesheet is linked to XML results
            can be True, in which case a results.css will be expected in the same directory
            can also be an url (relative or absolute)
        """
        import xml.etree.ElementTree as ET
        import time, os
        if stylesheet and (type(stylesheet) is bool): stylesheet = 'results.css'

        #Set root with important analysis characteristics as attributes
        results = ET.Element('results')
        results.set('versionMyFLq',version)
        results.set('timestamp',format(time.time(),'.0f'))
        results.text = '\n'
        for locus in sorted(self.loci):
            results.append(self.loci[locus].xml)
        results.set('sample',os.path.basename(self.sampleName if self.sampleName else self.fqFilename))
        results.set('thresholdUsed',str(self.threshold))
        results.set('flankedOut',str(self.flankOut))
        if self.flankOut:
            results.set('homomerCorrection',str(self.useCompress))
            if self.stutterBuffer: results.set('stutterBuffer',str(self.stutterBuffer))
        
        #Append locusDict
        if appendLocusDict:
            locusDict = ET.SubElement(results,'lociDatabaseState')
            locusDict.set('info','this was the state of the locus information used for the present analysis')
            locusDict.text = locusDict.tail = '\n'
            for locus in sorted(self.locusDict):
                locusxml = ET.SubElement(locusDict,'locusInfo')
                locusxml.set('name',locus)
                locusxml.text = locusxml.tail = '\n'
                for info in sorted(self.locusDict[locus]):
                    infoxml = ET.SubElement(locusxml,info)
                    infoxml.text = str(self.locusDict[locus][info])
                    infoxml.tail = '\n'
        
        #Display
        if not fileName: print(ET.tostring(results).decode("utf-8"))
        elif not stylesheet: ET.ElementTree(results).write(fileName, encoding = "UTF-8", xml_declaration = True)
        else:
            file=open(fileName,'wt')
            file.write(ET.tostring(ET.ProcessingInstruction(
                                    'xml','version="1.0" encoding="UTF-8"')).decode("utf-8")+'\n')
            #file.write(ET.tostring(ET.ProcessingInstruction(
            #                        'xml-stylesheet','type="text/css" href="'+stylesheet+'"')).decode("utf-8")+'\n') #with simple css (deprecated)
            file.write(ET.tostring(ET.ProcessingInstruction(
                                    'xml-stylesheet','type="text/xsl" href="'+stylesheet+'"')).decode("utf-8")+'\n')
            file.write(ET.tostring(results).decode("utf-8"))
            file.close()
            
    def makeVisualProfile(self,filename=None,inSubplots=True,saveInList=False):
        """
        Makes a visual representation out of the analysis.
        If filename is given, saves the figure instead of displaying it.
        The filename extension should indicate the format => file.pdf for a pdf image.
        
        If saveInList is given a list => plot data is appended to this list for further processing.
        """
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        def float(x):
            import builtins #in python 2.7 __builtin__
            if type(x) == str and x[-1] == '%': return builtins.float(x[:-1])/100
            else: return builtins.float(x)
        
        #Plot characteristics
        width = 0.45         #the width of the bars
        width_space = 0.3    #space between columns
        height_space = 0.005 #space between stacked bars

        locusNumber = len(self.locusDict)
        subplots = [] #Will be used later to draw all plots
        
        for locus,locusCount in zip(sorted(self.loci),range(1,locusNumber+1)):
            #Initiate plot
            subplots.append({})
            subplots[-1]['locusCount'] = locusCount
            subplots[-1]['title'] = locus + ' #{}'.format(len(self.loci[locus].reads))
                        
            locus = self.loci[locus]
            
            #Caclculate bars
            bars=[] #List with subdicts {'abundance':, 'name':, 'length':}
            for allele in locus.xml:
                dbName=AlleleType(allele.get('db-name'),allele.get('db-subtype')[1:-1] 
                                  if allele.get('db-subtype') else None,
                                  locusType='STR' if locus.info['locusType'] else 'SNP')
                alleleSize=allele.find('regionOfInterest').text
                if alleleSize == '[RL]': alleleSize = ''
                if alleleSize == '[-]': alleleSize = -1.
                elif not locus.info['locusType']: alleleSize = len(alleleSize)
                else:                    
                    alleleSize = float(calculateAlleleNumber(alleleSize,locus.info))

                bars.insert(0,{})
                bars[0]['abundance'] = float(allele.get('abundance'))
                bars[0]['name'] = '' if dbName.alleleType == 'NA' else dbName.alleleType
                bars[0]['length'] = alleleSize
          
            #Sort bars on name and length => first name than length
            bars.sort(key=lambda x: x['abundance'],reverse=True)
            bars.sort(key=lambda x: x['name'],reverse=True)
            bars.sort(key=lambda x: x['length'])
            
            #Calculate indices
            ##database alleles (expected)
            left_e=[]
            height_e=[]
            bottom_e=[]
            ##non database alleles (unexpected)
            left_ue=[]
            height_ue=[]
            bottom_ue=[]
            
            #Common
            names = []
            ticks = []
            cumulHeight=0 #current bottom to use
            left=0        #current index to use
            
            for i in range(len(bars)):
                if not bars[i]['name']:
                    left_ue.append(left)
                    height_ue.append(bars[i]['abundance'])
                    bottom_ue.append(cumulHeight)
                    if not left in ticks:
                        ticks.append(left)
                        names.append(bars[i]['length'])
                else: #if database allele
                    left_e.append(left)
                    height_e.append(bars[i]['abundance'])
                    bottom_e.append(cumulHeight)
                    if not left in ticks:
                        ticks.append(left)
                        names.append(bars[i]['name'])
                    else:
                        if type(names[-1]) == str: names[-1]+='|'+bars[i]['name']
                        else: names[-1]=bars[i]['name']
                names = [str(n) for n in names]
                    
                if i < (len(bars)-1) and bars[i]['length'] == bars[i+1]['length']:
                    cumulHeight+=bars[i]['abundance']+height_space
                else:
                    cumulHeight=0 
                    left+=width+width_space 

            #Draw data
            subplots[-1]['rects_e'] = (left_e, height_e, width, bottom_e)
            subplots[-1]['rects_ue'] = (left_ue, height_ue, width, bottom_ue)
            subplots[-1]['ticks'] = ticks
            subplots[-1]['names'] = names
        if type(saveInList) == list:
            saveInList.append(subplots)
            return        
        
        #Draw plots
        fig = plt.figure()
        #fig.suptitle(sample+' profile',fontsize='x-large')
        if inSubplots:
            import matplotlib.gridspec as gridspec
            gs = gridspec.GridSpec(1,locusNumber,width_ratios=[len(sp['ticks']) for sp in subplots])
        
            for sp in subplots:
                ax = fig.add_subplot(gs[0,sp['locusCount']-1])
                #ax.set_title(sp['title'])
                ax.text(0,0.97,sp['title'],rotation=90,horizontalalignment='right')
                
                #ax.grid(True)
                ax.set_ylim([0, 1])
                if sp['locusCount']==1: ax.set_ylabel('Abundance')
                else: ax.set_yticklabels(())
                
                rects_e = ax.bar(*sp['rects_e'], color='#66FF33')
                rects_ue = ax.bar(*sp['rects_ue'], color='r')
                if len(set(sp['rects_e'][0]+sp['rects_ue'][0])) == 1:
                    try: curvalue = sp['rects_e'][0][0]
                    except IndexError: curvalue = sp['rects_ue'][0][0]
                    ax.set_xlim(curvalue-width_space,curvalue+width+width_space)
                ax.set_xticks(np.array(sp['ticks'])+width/2)
                ax.set_xticklabels(sp['names'],rotation=90,fontsize='small')
        else:
            ax = fig.add_subplot(111)
            ax.set_ylim([0, 1])
            ax.set_ylabel('Abundance')
            subplotStartLocation = 0
            ticks=[]
            names=[]
            for sp in subplots:
                ax.text(subplotStartLocation,0.005,sp['title'],rotation=90,horizontalalignment='left',
                        verticalalignment='bottom')
                subplotStartLocation+=1
                sp['rects_e'] = ([l+subplotStartLocation for l in sp['rects_e'][0]],
                                 sp['rects_e'][1],sp['rects_e'][2],sp['rects_e'][3])
                sp['rects_ue'] = ([l+subplotStartLocation for l in sp['rects_ue'][0]],
                                 sp['rects_ue'][1],sp['rects_ue'][2],sp['rects_ue'][3])
                ticks+=[t+subplotStartLocation for t in sp['ticks']] 
                names+=sp['names']
                subplotStartLocation+=len(set(sp['rects_e'][0]+sp['rects_ue'][0]))
                rects_e = ax.bar(*sp['rects_e'], color='#66FF33')
                rects_ue = ax.bar(*sp['rects_ue'], color='r')
            ax.set_xticks(np.array(ticks)+width/2)
            ax.set_xticklabels(names,rotation=90,fontsize='small')
            ax.set_xlim([0,subplotStartLocation])
 
        if filename:
            fig.set_size_inches(5*locusNumber,10)
            plt.savefig(filename)
            plt.close()
        else: plt.show()


# #3d profiles
# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# ax.set_zlim([0,10])
# for subplots,z_i,color in zip(generalSPs,(0,1),('#66FF33','b')):
#     subplotStartLocation = 0
#     for sp in subplots:
#         ax.text(subplotStartLocation,0.005,z_i,sp['title'],rotation=90,horizontalalignment='left',
#                         verticalalignment='bottom')
#         subplotStartLocation+=1+len(set(sp['rects_e'][0]+sp['rects_ue'][0]))
#         rects_e = ax.bar(sp['rects_e'][0],sp['rects_e'][1],width=sp['rects_e'][2],
#                          bottom=sp['rects_e'][3],zs=z_i,color=color)
#         rects_ue = ax.bar(sp['rects_ue'][0],sp['rects_ue'][1],width=sp['rects_ue'][2],
#                          bottom=sp['rects_ue'][3],zs=z_i,color='r')
# plt.show()

# More elaborate analyses
#========================
class DoubleAnalysis:
    def __init__(self,*args,**kwargs):
        """
        Takes the Analysis arguments, but performs the analysis twice.
            First without flankOut
            Second run with flankOut
        """
        if kwargs.keys() & {'flankOut','processNow'}: raise Exception('Some arguments not expected')
        import time, random
        self.randomSeed = time.time()
        self.analyses = {}
        random.seed(self.randomSeed)
        self.fullLengthA = self.analyses['full length'] = Analysis(*args,flankOut=False,**kwargs)
        random.seed(self.randomSeed)
        self.flankoutA = self.analyses['with flankOut'] = Analysis(*args,flankOut=True,**kwargs)
    def makePlots(self):
        subplotsL = []
        self.fullLengthA.makeVisualProfile(saveInList=subplotsL)
        self.flankoutA.makeVisualProfile(saveInList=subplotsL)
        
        import matplotlib.pyplot as plt
        import numpy as np
        import matplotlib.gridspec as gridspec
        gs = gridspec.GridSpec(2,len(self.fullLengthA.loci),width_ratios=[max(len(sp1['ticks']),len(sp2['ticks'])) 
                                                           for sp1,sp2 in zip(*subplotsL)])
        #Plot characteristics
        width = 0.45         #the width of the bars
        width_space = 0.3    #space between columns
        height_space = 0.005 #space between stacked bars
        fig = plt.figure()
        
        for subplots,i,leg in zip(subplotsL,range(2),('Full length','With flankout')):
            for sp in subplots:
                ax = fig.add_subplot(gs[i,sp['locusCount']-1])
                #ax.set_title(sp['title'])
                ax.text(0,0.97,sp['title'],rotation=90,horizontalalignment='right')
                
                #ax.grid(True)
                ax.set_ylim([0, 1])
                #if sp['locusCount']==1: ax.set_ylabel('Abundance')
                #else: 
                ax.set_yticklabels(())
                if sp['locusCount']==1: ax.text(0,1.01,leg,fontsize=16,horizontalalignment='left')
                
                rects_e = ax.bar(*sp['rects_e'], color='#66FF33')
                rects_ue = ax.bar(*sp['rects_ue'], color='r')
                if len(set(sp['rects_e'][0]+sp['rects_ue'][0])) == 1:
                    try: curvalue = sp['rects_e'][0][0]
                    except IndexError: curvalue = sp['rects_ue'][0][0]
                    ax.set_xlim(curvalue-width_space,curvalue+width+width_space)
                ax.set_xticks(np.array(sp['ticks'])+width/2)
                ax.set_xticklabels(sp['names'],rotation=90,fontsize='small')
        plt.show()


# Validation analysis

class ValidationAnalysis(Analysis):
    def __init__(self,fqFilename,kitName='Illumina',maintainAllReads=True,kMerAssign=False,primerBuffer=False,
                    threshold=0.005,thresholdAlleles=None,alleles=None,processNow=True,parallelProcessing=4):
        """
        #WORK IN PROGRESS
        #SHOULD BE ABLE TO USE FOR INDEPENDENT NEW ALLELE SEARCH ANALYSIS, OR FULL SEQUENCE ANALYSIS OF UNKNOWN SAMPLES
        ####################################################
        Inherites from Analysis, but offers extra tools: the possibility to submit the
        validated alleles to the database, and/or to introduce new loci to the database.
        Quality checks can be more precise when it is known which alleles should be present.
        
        threshold => level for unique reads
        alleles => a list with the alleles expected to be present
            allelesDict = a dict with the expected alleles for each locusName key (#todo#not implemented yet)
        thresholdAlleles => sets at which level reads will be added to the database as validated alleles
        
        #Flanks cannot be removed from reads that need to be added to the database
        
        How to provide allele validated info:
            'a[:X[:R#repeat]]'
                => sequence is validated as an allele with allelenumber/name X, 
                            and if STR locus repeatsize of locus #repeat (in bp), e.g.:
                        'a' => only validated as allele, no extra info
                        'a:10.1'    => validated as allele 10.1
                        'a:10.1:R4   => validated as allele 10.1 from a locus with a repeatsize of 4 bp
        """
        Analysis.__init__(self,fqFilename,kitName,maintainAllReads,kMerAssign=kMerAssign,primerBuffer=primerBuffer,
                        threshold=threshold,processNow=processNow,parallelProcessing=parallelProcessing,flankOut=False,
                        negativeReadsFilter=False,stutterBuffer=False,useCompress=False,clusterInfo=False)
        self.alleles = alleles
        self.thresholdAlleles = thresholdAlleles

    def processAlleles(self):
        #Adapt for ValidationAnalysis
        """
        Processes the loci to look for alleles.
        Diplays all alleles present in the data, with the option to submit to the database.
        """                    
        #for locus in self.loci.values(): locus.analyze(badReadsFilter=(self.negativeReadsFilter 
        #                                    or bool(self.kMerAssign)),clusterInfo=self.clusterInfo)
        for locusName in sorted(self.loci):
            locus = self.loci[locusName]
            locus.setUniqueReads()
            abundances=locus.getReadAbundances()
            abundances=[(a,abundances[a]) for a in sorted(abundances,key=lambda x: abundances[x],reverse=True)]
            print('\n',locus)
            for a in sorted(abundances,key=lambda x: len(x[0]),reverse=True):print(format(a[1],'.3f'),':',a[0])
            print('\nValidate alleles for',locus,'\n(type ?[:size] for extra STR info for particular allele):')
            repeat = True
            while repeat:
                for a in abundances:
                    submitFlag=False #flag to indicate if alleles have been submitted
                    print(format(a[1],'.3f'),':',a[0])
                    aV=input('Allele-validation: ')
                    #Possibility for quick analyses of sequence
                    while aV.startswith('?'):
                        print(ValidationAnalysis.analyzeSTRseq(a[0], 4 if ':' not in aV else int(aV[aV.index(':')+1:])))
                        aV=input('Allele-validation: ')
                    if not submitFlag and aV.startswith('a'): submitFlag=True
                    #Possibility to skip to next locus
                    if aV == 'c': break
                    self.alleleToSubmit(locusName,a[0],aV)
                action=input('Submit alleles? (Yes-all/Alleles-only/No/Sanger) ')
                if action == '' and submitFlag:
                    import time
                    time.sleep(2)
                    action=input('Submit alleles? ')
                if action in ('Y','A'):
                    if action == 'Y': self.submitAlleles(locusName)
                    else: self.submitAlleles(locusName,withErrorSeqs=False)
                    print('Alleles submitted.')
                while action == 'S':
                    sequence=input('Sequence: ')
                    aV=input('Allele-validation: ')
                    makeEntry(locus.info['ref_forwardP']+sequence+complement(locus.info['ref_reverseP']),
                              0,locus.name,'labfbt','labfbt',technology='Sanger',forwardP=locus.info['ref_forwardP'],
                              reverseP=locus.info['ref_reverseP'],validatedInfo=aV)
                    action=input('Continue Sanger submitting? (N/S) ')
                if action != 'R': repeat=False
            
    def quickSearch(self,kMerRefAssign):
        #needs to be adapted to work under ValidationAnalysis
        """
        Diplays all alleles present in the data.
        Assignment according to k-mer-index of a full reference sequence for each locus.
        This approach should only be used to get a first glance at sequences for a locus and determine good primers
        Reads are assigned to a locus based on the k-mer index of the locusdict refseq's
        Not for full valid locus assignment and filling the database!
        
        kMerRefAssign => k-mer word size
        """
        self.kMerAssign = ('refseq-k-mer',kMerRefAssign)
        reads = Read.getReads(self.fqFilename)
        #reads = self.processReads(reads) #needs other processing

        #Make objects for the loci (not containing reads)
        self.loci = {locusName:Locus(locusName,None,self.locusDict,threshold=self.threshold,
                                     stutterBuffer=self.stutterBuffer) for locusName in self.locusDict}
        #Assign reads and primerOut
        for read in reads:
            try: self.loci[read.locus].reads.append(read)
            except KeyError:
                if read.locus: raise
    
        for locusName in sorted(self.loci):
            locus = self.loci[locusName]
            locus.setUniqueReads()
            locus.uniqueReads=locus.uniqueReads.items()
            locus.uniqueReads.sort(key=lambda x:x[1],reverse=True)
        
    def alleleToSubmit(self,locusName,uniqueRead,alleleValidation):
        """
        Stores the sequences to be submitted to the database together with validation info
        Is a list of tuples, each tuple: (sequence, alleleValidation, seqcount)
        alleleValidation = 'a[:X[:R#repeat]]' | 'NA', respectively validated or not validated
        ('NA' is assigned automatically if alleleValidation == '')
        """
        fullSeq=(self.locusDict[locusName]['ref_forwardP']+uniqueRead
                 +complement(self.locusDict[locusName]['ref_reverseP']))
        try: self.submittables[locusName].append((fullSeq,alleleValidation if alleleValidation else 'NA',
                                                  self.loci[locusName].uniqueReads[uniqueRead]))
        except (AttributeError,KeyError) as e:
            if type(e)==AttributeError: self.submittables = {}
            self.submittables[locusName] = [(fullSeq,alleleValidation if alleleValidation else 'NA',
                                             self.loci[locusName].uniqueReads[uniqueRead])]
    
    def submitAlleles(self,locusName,withErrorSeqs=True,automatically=False):
        """
        Submits alleles for locusName. If automatically, with thresholdAlleles.
        Else, with the information in submittables
        """
        if automatically: return NotImplemented
        if not withErrorSeqs: self.submittables[locusName] = [s for s in self.submittables[locusName] if s[1] != 'NA']
        makeEntry([s[0] for s in self.submittables[locusName]],[s[2] for s in self.submittables[locusName]],locusName,
                  'labfbt','labfbt',technology='Illumina',filterLevel=self.threshold,
                  forwardP=self.locusDict[locusName]['ref_forwardP'],
                  reverseP=self.locusDict[locusName]['ref_reverseP'],
                  validatedInfo=[s[1] for s in self.submittables])

    @staticmethod
    def analyzeSTRseq(seq,repeatStructure=4):
        """
        Returns the likely STR number of the sequence
        repeatStructure can be an integer for STRs with a unique repeat,
        or a more complex repeatStructure (latter not yet implemented)
        """
        import re
        if type(repeatStructure) == int:
            #Extract possible k-mers:
            kmers = {seq[i:i+repeatStructure] for i in range(len(seq)) if i <= len(seq) - repeatStructure}
            maxRepeat = (0,None,True) #(repeatNumber,repeatSequence,uniqueRepeatMax)
            for kmer in kmers:
                stretches=re.finditer(r'('+kmer+r')+',seq)
                for stretch in stretches:
                    repeatNumber=len(stretch.group())/repeatStructure
                    if repeatNumber > maxRepeat[0]: maxRepeat=(repeatNumber,stretch.group(),True)
                    elif repeatNumber == maxRepeat[0]: maxRepeat=(maxRepeat[0],maxRepeat[1],False)
        return maxRepeat
        


# Commandline interface
#======================
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(prog='MyFLq',
                                     description='Run a MyFLq analysis or add kit/sequences to the database')
    
    subparsers = parser.add_subparsers(title='Analyze or add kit/sequence',
                                       description='''To use MyFLq either choose add or analyze.
                                       To see which further arguments are required with either:
                                       MyFLq.py add -h
                                       MyFLq.py analyze -h
                                       ''',
                                       help='MyFLq sub-commands')
    #Commandline options for adding to the database
    parser_add = subparsers.add_parser('add', help='add help')
    parser_add.add_argument('-k','--add-kit',const=True,
                            help='''Combination of loci to add to the database.
                            If no option is provided, it will be asked for. To automatically add a set of loci,
                            provide as an argument a 'file.csv' ''',
                            nargs='?')
    parser_add.add_argument('-a','--alleles',help='Validated alleles to add to the database')
    
    
    #Commandline options for performing an analysis
    import inspect,builtins #allows to dynamically ask for options
    sig = inspect.signature(Analysis.__init__) #needs python3.3
    doc = {d.split('=>')[0].strip():d.split('=>')[1] 
           for d in inspect.getdoc(Analysis.__init__).split('\n') if '=>' in d}
    parser_analysis = subparsers.add_parser('analysis', help='analysis help')
    noDynamicOptions = {'self','kitName','kMerAssign','maintainAllReads','processNow'}
    for param in sig.parameters: #needs python3.3
        if param in noDynamicOptions: continue 
        if sig.parameters[param].default == inspect._empty: #needs python3.3
            parser_analysis.add_argument(param,help=doc[param])
        else:
            defaultP = sig.parameters[param].default #needs python3.3
            typeP = (type(defaultP) if defaultP is not None else builtins.__dict__[doc[param].split()[-1].strip()[1:-1]])
            if typeP == bool:
                parser_analysis.add_argument('--'+param,action='store_true',help=doc[param])
            else:
                parser_analysis.add_argument('--'+param,type=typeP,default=defaultP,help=doc[param])
    parser_analysis.add_argument('--kMerAssign',type=int,
                                 help='''Instead of looking for exact primers, assign a read based on
                                 primer k-mer words of size int KMERASSIGN.
                                 This is only meant to be used exploratory. All reads will be assigned to some locus.''')
    parser_analysis.add_argument('-r','--report',const=True,nargs='?',
                                 help='Make report, optionally provide filename to save xml')
    parser_analysis.add_argument('-s','--stylesheet',const=True,nargs='?',
                                 help='Link report to stylesheet, optionally provide stylesheet url')
    parser_analysis.add_argument('-v','--visualProfile',const=True,nargs='?',
                                 help='Make visual profile, optionally provide filename to save figure')

    
    #General commandline options
    parser.add_argument('user', help='User with permission for the database')
    parser.add_argument('db', help='Database to use')
    parser.add_argument('kit', help='Combination of loci to use')
    parser.add_argument('-p','--password',help='MySQL user password (if not provided, will be asked for)')
    
    
    #Parse/process arguments
    args = parser.parse_args()
    #args = parser.parse_args(['analysis','-v','--stutterBuffer','0','--flankOut','False','--randomSubset','0.05',
    #        '--verbose','True','--useCompress','True','--withAlignment','True',#'--parallelProcessing','0',
    #        '/home/christophe/Documents/STR/Illumina/STR_Mixtures/9947ADNAADNAB2800MK562_S3_L001_R1_001.fastq',
    #        'testuser','testdb','Illumina','-p','testuser']) #debug
    if not args.password:
        import getpass
        try: args.password = getpass.getpass('MySQL password for '+args.user+': ')
        except EOFError: args.password = input('MySQL password for '+args.user+': ')

    #Check if user and password match => if user is authorised to make or change MyFLq databases
    login = Login(user=args.user,passwd=args.password,database=args.db)
    login.testConnection()
    
    #Program flow
    if 'add_kit' in args:
        if args.add_kit:
            if type(args.add_kit) == bool: Locus.makeLocusDict(submit=True,kitName=args.kit)
            else: Locus.makeLocusDict(('csv',args.add_kit),submit=True,kitName=args.kit)
        if args.alleles:
            makeEntries(args.alleles)
            processLociNames()      #In the future, when choosing a subset of dataset alleles for analysis
            processLociAlleles()    #this will have to be rewritten
    elif 'fqFilename' in args:
        #Prepare special arguments
        if args.kMerAssign:
            args.kMerAssign = ('k-mer',args.kMerAssign)
        else: del args.kMerAssign

        kwargs = {arg:args.__dict__[arg] for arg in args.__dict__ if arg in sig.parameters} #needs python3.3
        #kwargs = {arg:args.__dict__[arg] for arg in args.__dict__ if arg in sig[0]} #deprecated python 2.7
        #Start analysis
        #import pdb
        #pdb.set_trace()
        analysis = Analysis(kitName=args.kit,**kwargs)
        if not sum({len(analysis.loci[locus].uniqueAbundances) for locus in analysis.loci}):
            raise Exception('''There does't seem to be any valid reads in your fastq.
                               Either your fastq sample is not a forensic sample, or you may need to
                               choose a different loci.csv and alleles.csv file.
                            ''')
        if args.report:
            if type(args.report) == bool: analysis.makeReport()
            else: analysis.makeReport(fileName=args.report, stylesheet=args.stylesheet)
        if args.visualProfile:
            if type(args.visualProfile) == bool: analysis.makeVisualProfile()
            else: analysis.makeVisualProfile(filename=args.visualProfile)
    if 'verbose' in args and args.verbose:
        print(str(args).replace('Namespace(','(Parametes analysis: ')) #debug

# #Examples for commandline use
# ##Prepare database with MyFLdb.py
# MyFLdb.py testuser testdb    #delete database with: MyFLdb.py --delete testuser testdb
# 
# ##Adding kits/alleles to the database
# MyFLq.py add -k primers.csv -a alleles_example.csv testuser testdb Illumina
# 
# ##Running an analysis
# MyFLq.py analysis /home/christophe/Documents/STR/Illumina/STR_Mixtures/9947ADNAADNAB2800MK562_S3_L001_R1_001.fastq \
#                   testuser testdb Illumina

