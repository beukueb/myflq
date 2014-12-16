#!/bin/env python3

#Form select options:
lociOptions = ['', #index 0 not used
               'myflqpaper_loci.csv', #index 1 
    ]

alleleOptions = ['', #index 0 not used
               'myflqpaper_alleles.csv', #index 1 
    ]

import json, subprocess
appsession = json.load(open('/data/input/AppSession.json'))
inform = {item['Name'][6:]:item for item in appsession['Properties']['Items'] if not 'Output' in item['Name']}

#Prepping MyFLdb #todo# => implement for files given by user
# if 'select-loci' in inform:
#     lociFile = '/myflq/loci/'+lociOptions[int(inform['select-loci']['Content'])]
# else: raise NotImplementedError
# if 'select-allele' in inform:
#     alleleFile = '/myflq/alleles/'+alleleOptions[int(inform['select-allele']['Content'])]
# else: raise NotImplementedError
if 'loci-textbox' in inform:
    lociFile = '/tmp/loci.csv'
    subprocess.check_call([
        'wget',
        '-O',
        lociFile,
        inform['loci-textbox']['Content'].strip()
    ])
else: lociFile = '/myflq/loci/'+lociOptions[int(inform['select-loci']['Content'])]
if 'alleles-textbox' in inform:
    alleleFile = '/tmp/alleles.csv'
    subprocess.check_call([
        'wget',
        '-O',
        alleleFile,
        inform['alleles-textbox']['Content'].strip()
    ])
else:
    if int(inform['select-allele']['Content']) == -1:
        import sys
        sys.path.append('/myflq')
        from MyFLq import complement
        alleleFile = '/tmp/alleles.csv'
        tmp = open(alleleFile,'wt')
        for line in open(lociFile):
            if line.strip().startswith('#'): continue
            line = line.strip().split(',')
            tmp.write('{},{},{}{}\n'.format(line[0],'?' if line[1]=='SNP' else '0',line[2],complement(line[3])))
        tmp.close()
    else: alleleFile = '/myflq/alleles/'+alleleOptions[int(inform['select-allele']['Content'])]

#MyFLdb command
command = ['python3',
           '/myflq/MyFLdb.py',
           '-p', 'passall',
           'admin','onetimedbuse'
    ]
failed = subprocess.call(command)
if failed: raise Exception('Setting up database failed')
#MyFLq filling database
subprocess.check_call([
        'python3',
        '/myflq/MyFLq.py',
        '-p', 'passall',
        'add', '-k', lociFile,
        '-a', alleleFile,
        'admin',
        'onetimedbuse', 'default'
        ])

#Prepare fastq
import os
sampleName = '/tmp/' + inform['sample-id']['Content']['Name'].replace(' ','') + '.fastq'
fastqfiles = []
for path, dirs, files in os.walk('/data/input/samples'):
    for file in files:
        fastqfiles.append(os.path.join(path, file))
subprocess.check_call('zcat -f ' + ' '.join(fastqfiles) + ' > ' + sampleName, shell=True)

#Prepare output dir
outDir = '/data/output/appresults/' + inform['project-id']['Content']['Id'] + '/' + inform['sample-id']['Content']['Name'].replace(' ','') + '/'
subprocess.check_call(['mkdir', '-p', outDir])

#Prepare options for MyFLq
command = ['python3',
           '/myflq/MyFLq.py',
           '-p', 'passall',
           'analysis',
           '--negativeReadsFilter', #if 'negativeReadsFilter' in inform, #For now always enabled, no added value/buggy
           '--primerBuffer', str(inform['primerBuffer']['Content']),
           '--flankOut' if 'flankOut' in inform else 'REMOVE',
           '--stutterBuffer', str(inform['stutterBuffer']['Content']),
           '--useCompress' if 'useCompress' in inform else 'REMOVE',
           '--withAlignment' if 'withAlignment' in inform else 'REMOVE',
           '--threshold', str(float(inform['threshold']['Content'])/100),
           '--clusterInfo', #if 'clusterInfo' in inform else 'REMOVE', #Makes no sense not to see this info for forensic analyst
           '--randomSubset' if str(inform['randomSubset']['Content']) == '100' else 'REMOVE',
           str(float(inform['randomSubset']['Content'])/100) if str(inform['randomSubset']['Content']) == '100' else 'REMOVE',
           '-r', outDir+'resultMyFLq.xml',
           '-s', '/myflq/resultMyFLq.xsl', #Should be either on same domain as xml file, or local
           '-v', outDir+'resultMyFLq.png',
           '--parallelProcessing', '0',
           sampleName,
           'admin', 'onetimedbuse', 'default'
    ]

while 'REMOVE' in command: command.remove('REMOVE')

print('Start processing with command: '+' '.join(command))
#try: 
subprocess.check_call(command)
#except subprocess.CalledProcessError: print('''Something went wrong with MyFLq.
#          Please send the above information bag to us,
#          or share this project with us, so we can debug it.''')

#Transform xml to html
subprocess.check_call(' '.join(['saxonb-xslt',
                       '-versionmsg:off',
                       '-a', ' -o',  outDir+'resultMyFLq.html',
                       outDir+'resultMyFLq.xml',
                       'appcontext=webapp'
                       ]), shell=True)

#Debug
#import sys
#print(sys.argv)
