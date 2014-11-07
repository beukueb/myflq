from celery import shared_task

@shared_task
def rmneTaskRequest(data,doAllowed,outDir):
    #Preparation
    from django.conf import settings

    #RMNE logic
    from rmne.bin.RMNE2_Core2 import PE0Lon,PE1Lon,PE2Lon,PE

    list_locus=[]
    for di in data:
        if 'locus' not in di.keys(): continue
        list_locus.append(di['locus'])
    list_locus=set(list_locus)

    list_of_lists_observed_freq=[]
    list_of_lists_nonobserved_freq=[]
    for locus_value in list_locus: 
        observed_freq=[]
        nonobserved_freq=[]
        for di in data:
                if 'locus' not in di.keys(): continue
                if di['locus']!=locus_value: continue
                if di['observed']==True:
                        observed_freq.append(di['frequency'])
                elif di['observed']==False:
        	        nonobserved_freq.append(di['frequency'])
        list_of_lists_observed_freq.append(observed_freq)
        list_of_lists_nonobserved_freq.append(nonobserved_freq)

    p1=PE0Lon(list_of_lists_observed_freq,list_of_lists_nonobserved_freq)
    p2=PE1Lon(list_of_lists_observed_freq,list_of_lists_nonobserved_freq)
    p3=PE2Lon(list_of_lists_observed_freq,list_of_lists_nonobserved_freq)

    result=[]
    xv=[]
    yv=[]
    RMNE=0
    for i in range(0,3):
        v=PE(p1,p2,p3,i)
        RMNE+=v[-1]
        xv.append(i)
        yv.append(RMNE)
        result.append([i,RMNE])
    import pickle
    pickle.dump(result,open(outDir+'result.pickle','wb'))

    from matplotlib import pylab as plt
    import matplotlib.pyplot as pyplot
    fig = pyplot.figure(dpi=60)
    ax = fig.add_subplot(1,1,1)
    col = (1/8.0, 1/8.0, 1/8.0)
    line, = plt.plot(xv, yv, '-', linewidth=2, color=col)
    line, = plt.plot(xv, yv, '-', linewidth=2, color=col, label='RMNE')
    ax.set_yscale('log')
    ax.legend(loc='lower right', shadow=True)
    plt.xlabel('Number of allowed drop-outs')
    plt.ylabel('RMNE Probability')
    plt.title('RMNE Probability')
    plt.savefig(outDir+"figure.png")
    plt.close()


    #Communicating back to webapp
    ##the figure should be saved first in png
    ##here a random figure is generated as a placeholder

    ##the 'finished' file should only contain the rmne result
    with open(outDir+'finished', 'w') as fout:
        fout.write('1')


#To experiment in: python manage.py shell:
#from rmne.forms import RFormSet
#formset = RFormSet(initial=[{'locus':'vwa','allele':'11','frequency':0.5}])
#
#Data input formset.cleaned_data
#[{'observed': False, 'locus': 'a', 'frequency': 0.3, 'allele': 'a'}, {'observed': True, 'locus': 'b', 'frequency': 0.5, 'allele': 'b'}, {}, {}, {}, {}, {}, {}, {}, {}]
#
