import re,pdb
minimumRepeatNumber = 3 #Minimum expected number of exact repeats
repeatex = {repeatsize:re.compile(r'([ACTG]{'+str(repeatsize)+r'})\1{'+str(minimumRepeatNumber)+r',}') for repeatsize in (4,5)}
out = open('stryxkit_new.csv','wt')
for line in open('stryxkit.csv'):
    #pdb.set_trace()
    line = line.strip().split(',')
    if line[1] == 'SNP':
        out.write(','.join(line)+'\n')
        continue
    maxResult = (4,minimumRepeatNumber) #Default value for STRs in case real value is not found
    for repeatsize in (4,5):
        for match in repeatex[repeatsize].finditer(line[-1]):
            if len(match.group())/repeatsize > maxResult[1]:
                maxResult = (repeatsize,len(match.group())/repeatsize)
    line[1] = str(maxResult[0])
    line[-2] = str(int(maxResult[1]))
    out.write(','.join(line)+'\n')
out.close()
                
