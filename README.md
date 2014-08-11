#MyFLq version 1.0 
[My Forensic Loci queries]

Open source, straightforward analysis tool for forensic DNA samples.

The tool expects a loci csv-file (similar to [loci.csv](https://github.com/beukueb/myflq/blob/master/src/loci/myflqpaper_loci.csv)), a validated-allele csv-file for all the included loci  (similar to [alleles.csv](https://github.com/beukueb/myflq/blob/master/src/alleles/myflqpaper_alleles.csv)) and a fast[a/q] datafile, whereupon the datafile's profile is extracted. To download the loci.csv and alleles.csv files, right-click the 'RAW' button and choose 'save as...'. These files can be opened using a regular text editor such as 'Textpad' (Windows) or 'gedit' (Linux).

The datafile can be a single-individual-source or multiple-individual-source sample. Profile results depend on both csv files. Loci.csv will determine the number of loci that will be analyzed; alleles.csv will determine the region of interest [ROI] of those loci.

## Options for running MyFLq
### From the Github repo

MyFLq is developed as a Django application. It requires the installation of several dependencies (including MySQL) before it can be used.  Detailed instructions can be found in the file [INSTALL](https://github.com/beukueb/myflq/blob/src/MyFLsite/INSTALL.md).

Setup:

    git clone https://github.com/beukueb/myflq.git
    cd myflq/src/MyFLsite/
    python3 manage.py syncdb


To start the webapp (e.g. on Ubuntu):

    sudo systemctl start rabbitmq
    celery -A MyFLsite worker -l info &
    python3 manage.py runserver 0.0.0.0:8000


### As a Docker container
A more convenient way to try MyFLq may be to use the available docker container. Docker is easily installed (see [here](https://www.docker.io/) for instructions). To download and start the MyFLq container, issue the following command:

    sudo docker run -p 0.0.0.0:80:8000 -i -t --entrypoint webapp beukueb/myflq

In case you already have a service using the standard webport 80 on your computer, you can adjust the command line to run the webapp on another free port. 
MyFLq will then run as a local web application on the indicated port.

### Illumina BaseSpace
MyFLq is also accessible directly from the Illumina BaseSpace environment.

#### Custom loci.csv and alleles.csv
When custom loci.csv and alleles.csv are required on BaseSpace, one can submit them on [MyFLhub](https://github.com/beukueb/myflq) (MyFLq repo on Github) with a pull request (ask a bioinformatician to help if you don't know how). The program will then be rebuild, and your files will be available to select within 24 hours.

If you do not want those files to be public, you can copy paste them into the respective textbox in the input form. In this case pay close attention to the format of your *.csv files. There should not be any whitespace, unless at the end of a line or within a commented line. The easiest way to achieve this is to open your .csv file in a standard text editor of your choice (e.g. 'Textpad' in Windows or 'gedit' in Linux), to select (CTRL+A) and copy (CTRL+C) its entire contents and to paste them (CTRL+V) in the allocated text field on BaseSpace MyFLq (see 'Choose input settings' below).

When choosing to use custom loci and alleles input files, you have to make sure that both files contain information for the same loci/alleles. That is, the alleles.csv file needs to contain only allele information for every locus specified in the loci.csv file and vice versa. If this is not the case, an error will be generated. 

In the future it will be possible to upload files (e.g. small csv's) to your BaseSpace projects. At that time you will be able to select personal files.

##Workflow on BaseSpace MyFLq
To start the app on BaseSpace simply launch it, which will direct you to the input form.

###Choose input settings

- Choose a sensible name or leave the default with date/time
- Select loci set.  
  The options are links to loci.csv-files that have been shared by users on [MyFLhub](htt\
ps://github.com/beukueb/myflq). You can also copy paste your custom file in the textbox.
- Select allele database.  
  These are instead links to the alleles.csv-files. You can copy paste your custom file in the textbox.
- Sample: select the fastq file for analysis.  
  The fastq can be either single-end or paired-end and should be available on BaseSpace.
- Save results to: the project where your results will be saved.
- General options for analysis:
 - *Threshold*  
   Unique reads with an abundance lower than this value (in %), are discarded. It is reported in the locus stats how many reads were discarded in this way.
 - *Preview*  
   Analyzing very big fastq's can take a considerable amount of time. If you want a quick preview, select a random percentage of the file to analyze. For low values (2-10%), this will give you a quick analysis of the profile. If at this point all alleles indicate a clear single contributor and have at least 1000 reads per locus, it is probably not necessary to do an analysis on the full file.
- Alignment options  
  Different types of alignments occur during the process of analysis. With these options you can influence the processing.
 - *Primer buffer*  
   The number of bases at the end of the primer that will not be used for assigning the reads to loci. Choosing a higher buffer therefore means the locus assignment could be slightly less specific, but more reads will get assigned. 10 is a recommended maximum setting.
 - *Stutter buffer*  
   The stutters of the smallest allele for a locus are normally not in the database, and could have a negative-length ROI. Default value of this buffer is 1 to accomodate that. This allows all stutters to be seen as flanking out is performed with a flank 1 repeat unit smaller.
 - *Flankout*  
   If you see a large amount of negative reads  in the analysis (this can be derived from the locus statistics), or a high abundant unique read with very poor flanks, turn this feature off. The analysis will then be done between the primers. Previously unknown alleles can be discovered this way.
 - *Homopolymers compressed*  
   Long homopolymers in the flanks could stutter during PCR. This option annotates flanks of loci that were possibly affected by this.
 - *Flankout by alignment*  
   If this option is activated, flanks are removed with our alignment algorithm, instead of the k-mer based flexible flanking.

After selecting options, launch analysis.

###Review results.
When the analysis is done, BaseSpace will have automatically made a report with all the results. This report can be found in the project folder in which your results were saved.  

The report primarily shows the visual profile. Initially it shows the overview of all analyzed loci. 

Functionality:

- On the X-axis (with the loci names), you can zoom in and move the axis to go over all the loci.
- Putting the mouse on an allele candidate bar, shows all information for that candidate. Clicking on a bar from an allele candidate that has an abundance higher than the threshold, will deselect it from the profile. Sequence aberrations can be removed by doing so.
- Selecting 'Absolute length' in the settings, will reorganize the graph. All allele candidates will now be plotted within each locus proportionate to their sequence length.
- Pushing 'Make profile' generates a table in a new window that contains only the allele candidates that were present with an abundance higher than the threshold and were not manually deselected from the profile.

Suggested steps:

- Set the threshold to a level appropriate for the sample noise.
- Inspect each red allele (unknown in the database), that is still higher in abundance than the threshold. If the abundance is not far removed from the threshold and the stats indicate poor quality, deselect them from the profile.
- In case it is known to be a single contributor sample, closely inspect all sequences from loci that have more than 2 alleles.

###Make profile and save it locally
- After reviewing all loci, click "Make profile".
- A new browser window will open with all the alleles in the profile. Save it locally by selecting 'Save as...' from your browser's "File" menu.
  (For now it is not possible to save it in your project, so choose a filename that refers to the project/result.) 
- If there is a locus with more than two alleles, it is indicated that based on the threshold this profile derives from a multi-contributor sample. If there is maximum two alleles per locus, the probability of that profile can be retrieved from the [ENFSI STRbase](http://strbase.org/) site.

###Test files
Click [here](https://cloud-hoth.illumina.com/s/t64TniA0EKQk) to get access to a project with forensic samples that can be used to try out MyFLq.
  

##Workflow for a local MyFLq installation
Start the app as described in the [Options for running MyFLq](https://github.com/beukueb/myflq#options-for-running-myflq) section.

###Register to create a user account
To use the application, you need to register.  This will enable the system to keep track of your analyses.

- Choose user name and password to complete the registration form.

###Login

- Fill in your user name and password in the upper right corner and click the login button.

###Workflow
After a succesfull login, you end up on the MyFLq workflow page displaying condensed instructions on how to proceed with the setup, analysis and results.  Detailed instructions can be found in the 'Help' section of the application.

In a nutshell:
####Setup loci and alleles
- __Database setup__: Create a new database for your analysis by supplying a name and clicking the '__Create db__' button.  Your database name should now be displayed with the option to delete it.
- __Primers setup__: Select your database from the Dbname pulldown.  Browse to select a loci file (CSV format), click the '__Upload__' button.  You will be redirected to the 'Setup' page, but the uploaded file will not be displayed in the current version of the software.
- __Adding alleles__: Select your database from the Dbname pulldown.  Browse to select an allele file (CSV format), click the '__Upload__' button.  Similar to the primers setup, you will be redirected to the 'Setup' page, but the uploaded file will not be displayed in the current version of the software.
- __Commit settings__: Select your database from the Dbname pulldown and click the '__Commit__' button to store your input into the database. Similar to the primers setup, you will be redirected to the 'Setup' page

####Analysis
- __Submit analysis request__: Select your database from the Dbname pulldown.  Browse to select a fastq file with the sequences you want to analyse, or alternatively choose a previously uploaded one.
- __General__ & __Alignment__: Adjust the parameters to your requirements or use the defaults.  See 'General options for analysis' under the 'Workflow on BaseSpace MyFLq' section for a detailed description.
Click the '__Submit__' button to add your analysis to the queue.
- __Progress__: A progress table now lists your analysis status and will be periodically refreshed.  When the analysis is completed, the entry is removed from the table and you can proceed to the 'Results' section.

####Results
- __All results__: The table shows the result sets for all completed analyses.  You can select a result set by clicking the radio button next to its status, then click the '__Visualize result__' button to display the data.
- __Analysis details__
    - __Parameters__: Summary of the analysis parameters as entered in the 'Setup loci and alleles' section
    - __Profile__: Report of the analysis.  See 'Review results' under the 'Workflow on BaseSpace MyFLq' section for a detailed description.

###Test files
A sample loci ([loci.csv](https://github.com/beukueb/myflq/blob/master/src/loci/myflqpaper_loci.csv)) and alleles ( [alleles.csv](https://github.com/beukueb/myflq/blob/master/src/alleles/myflqpaper_alleles.csv)) data file are available in the git repository.  You will need to supply your own Fastq sequence file to perform an analysis, or download it from the [BaseSpace project page](https://cloud-hoth.illumina.com/s/t64TniA0EKQk) after registering.

##More information
- Original paper: [My-Forensic-Loci-queries (MyFLq) framework for analysis of forensic STR data generated by massive parallel sequencing](http://dx.doi.org/10.1016/j.fsigen.2013.10.012)

