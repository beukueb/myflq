from celery import shared_task

@shared_task
def rmneTaskRequest(data,outDir):
    #Preparation
    from django.conf import settings

    #RMNE logic
    ##Filip
    from rmne.bin.rmne import testrmne
    print(testrmne)
    result = 0.0001
    
    #Communicating back to webapp
    ##the figure should be saved first in png
    ##here a random figure is generated as a placeholder
    from PIL import Image
    import numpy as np
    a = np.random.rand(300,300,3) * 255
    im_out = Image.fromarray(a.astype('uint8')).convert('RGBA')
    im_out.save(outDir+'figure.png')
    ##the 'finished' file should only contain the rmne result
    with open(outDir+'finished', 'w') as fout:
        fout.write(str(result))


#To experiment in: python manage.py shell:
#from rmne.forms import RFormSet
#formset = RFormSet(initial=[{'locus':'vwa','allele':'11','frequency':0.5}])
#
#Data input formset.cleaned_data
#[{'observed': False, 'locus': 'a', 'frequency': 0.3, 'allele': 'a'}, {'observed': True, 'locus': 'b', 'frequency': 0.5, 'allele': 'b'}, {}, {}, {}, {}, {}, {}, {}, {}]
#
