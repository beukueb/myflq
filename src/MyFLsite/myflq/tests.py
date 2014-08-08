from django.test import TestCase, Client

# Create your tests here.
from django.contrib.auth.models import User
class MyflqTestCase(TestCase):
    def setUp(self):
        #Setup test user and login
        user = User.objects.create_user(username='testUser', password='test')
        c = Client()
        c.login(username='testUser', 'password': 'test'}) #c.logout() when AnonymousUser needed

    def test_myflq_workflow(self):
        """
        Testing the general workflow
        Uploading config files for loci and alleles
        Running with test fastq
        """
        #Make test database
        response = c.post('/myflq/setup/', {'dbname': 'testdb','submitaction':'createdb'})
        optionValue = [i for i in str(response.content).split('\\n')
                       if 'option' in i and '>testdb<' in i][0].split('"')[1]
        self.assertEqual(response.status_code, 200)

        #Populate database and commit
        with open('../loci/myflqpaper_loci.csv','rb') as fp:
            c.post('/myflq/setup/', {'dbname': optionValue,'submitaction':'addlocifile','fileName': fp})

        with open('../alleles/myflqpaper_alleles.csv','rb') as fp:
            c.post('/myflq/setup/', {'dbname': optionValue,'submitaction':'addallelesfile','alleleFile': fp})
            
        response = c.post('/myflq/setup/', {'dbname': optionValue,'submitaction':'commitdb'})
        self.assertTrue('error' not in str(response.content))

        #Run analysis
        import gzip, subprocess
        self.assertEqual(subprocess.call(["celery","status"]),0) #If 0, this means celery is active
        with gzip.open('../testing/test_subsample_9947A.fastq.gz','rb') as fp:
            response = c.post('/myflq/analysis/', {'dbname': optionValue,
                                                   'fastq': fp,
                                                   'negativeReadsFilter': 'on',
                                                   'clusterInfo': 'on',
                                                   'threshold': '0.05',
                                                   'primerBuffer': '0',
                                                   'stutterBuffer': '1',
                                                   'flankOut': 'on',
                                                   'useCompress': 'on',
                                                   'submitaction': 'analysisform'
                                               })
            
        #Test if analysis run succesfully
        response = c.get('/myflq/results/')
        resultLine = [i for i in str(response.content).split('\\n') if 'test_subsample_9947A.fastq.gz' in i][0]
        self.assertTrue('Finished' in resultLine)


#Test AJAX
#c = Client()
#>>> c.get('/customers/details/', {'name': 'fred', 'age': 7},
#...       HTTP_X_REQUESTED_WITH='XMLHttpRequest')
