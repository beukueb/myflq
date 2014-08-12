from django.test import TestCase, Client

# Run from site root dir with: python manage.py test myflq.tests
# Create your tests here.
from django.contrib.auth.models import User
class MyflqTestCase(TestCase):
    def setUp(self):
        #Setup test user and login
        user = User.objects.create_user(username='testUser', password='test')
        self.c = Client()
        self.c.login(username='testUser', password='test') #c.logout() when AnonymousUser needed

    def test_myflq_workflow(self):
        """
        Testing the general workflow
        Uploading config files for loci and alleles
        Running with test fastq
        """
        #Make test database
        response = self.c.post('/myflq/setup/', {'dbname': 'testdb','submitaction':'createdb'})
        optionValue = [i for i in response.content.decode().split('\n')
                       if 'option' in i and '>testdb<' in i][0].split('"')[1]
        self.assertEqual(response.status_code, 200, msg='Not able to create settings database')

        #Populate database and commit
        with open('../loci/myflqpaper_loci.csv','rb') as fp:
            self.c.post('/myflq/setup/', {'dbname': optionValue,'submitaction':'addlocifile','fileName': fp})

        with open('../alleles/myflqpaper_alleles.csv','rb') as fp:
            self.c.post('/myflq/setup/', {'dbname': optionValue,'submitaction':'addallelesfile','alleleFile': fp})
            
        response = self.c.post('/myflq/setup/', {'dbname': optionValue,'submitaction':'commitdb'})
        self.assertNotIn('error', str(response.content), msg='Commiting database not succeeded')

        #Run analysis
        import gzip, subprocess
        self.assertEqual(subprocess.call(["celery","status"]), 0, msg='Celery worker is not active. Cannot complete tests without')
        with gzip.open('../testing/test_subsample_9947A.fastq.gz','rb') as fp:
            response = self.c.post('/myflq/analysis/', {'dbname': optionValue,
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
            
        #Test if analysis ran succesfully
        import time
        time.sleep(60) #Waiting for small analysis to complete. Could be implemented by querying django site, until processed
        response = self.c.get('/myflq/results/')
        resultLine = [i for i in response.content.decode().split('\n') if 'test_subsample_9947A.fastq.gz' in i][0]
        self.assertIn('Finished', resultLine, msg='Analysis failed for some reason')


#Test AJAX
#c = Client()
#>>> c.get('/customers/details/', {'name': 'fred', 'age': 7},
#...       HTTP_X_REQUESTED_WITH='XMLHttpRequest')

#Live server test => pip install selenium (don't offer in docker version)
# from django.test import LiveServerTestCase
# from selenium.webdriver.firefox.webdriver import WebDriver

# class MySeleniumTests(LiveServerTestCase):
#     fixtures = ['user-data.json']

#     @classmethod
#     def setUpClass(cls):
#         cls.selenium = WebDriver()
#         super(MySeleniumTests, cls).setUpClass()

#     @classmethod
#     def tearDownClass(cls):
#         cls.selenium.quit()
#         super(MySeleniumTests, cls).tearDownClass()

#     def test_login(self):
#         self.selenium.get('%s%s' % (self.live_server_url, '/login/'))
#         username_input = self.selenium.find_element_by_name("username")
#         username_input.send_keys('myuser')
#         password_input = self.selenium.find_element_by_name("password")
#         password_input.send_keys('secret')
#         self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()
