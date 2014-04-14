#MyFLq version 1.0 
[My Forensic Loci queries]

Open source, straightforward analysis tool for forensic DNA samples.

The tool expects a loci csv-file (similar to [loci.csv](https://github.com/beukueb/myflq/blob/master/src/loci/myflqpaper_loci.csv)), a validated-allele csv-file for all the included loci  (similar to [alleles.csv](https://github.com/beukueb/myflq/blob/master/src/alleles/myflqpaper_alleles.csv)) and a fastq datafile, whereupon the datafile's profile is extracted.

The datafile can be a single-individual-source or multiple-individual-source sample. Profile results depend on both csv files. Loci.csv will determine the number of loci that will be analyzed; alleles.csv will determine the region of interest [ROI] of those loci.

##Custom loci.csv and alleles.csv
When custom loci.csv and alleles.csv are required, one can submit them on [MyFLhub](https://github.com/beukueb/myflq) (MyFLq repo on Github) with a pull request (ask a bioinformatician to help if you don't know how). The program will then be rebuild, and your files will be available to select within 24 hours.

If you do not want those files to be public, at this point, the only other option is, after installing [Docker](https://www.docker.io/), to pull and start the MyFLq container on your server with the following command:

    sudo docker run -p 0.0.0.0:80:8000 -i -t --entrypoint /myflq/webapp beukueb/myflq

If you want the webapp to run on another port than the standard webport 80, change that in the commandline.

MyFLq will then run as a local web application on the indicated port. For more information on this see [MyFLhub](https://github.com/beukueb/myflq)

In the future it will be possible to upload files (e.g. small csv's) to your BaseSpace projects. At that time you will be able to select personal files.

##Workflow on BaseSpace MyFLq
To start the app on BaseSpace simply launch it, which will direct you to the input form.

###Choose input settings

- Choose a sensible name or leave the default with date/time
- Select loci set.  
  The options are links to loci.csv-files that have been shared by users on [MyFLhub](htt\
ps://github.com/beukueb/myflq)
- Select allele database.  
  These are instead links to the alleles.csv-files.
- Sample: select the fastq file for analysis.  
  The fastq can be either single-end or paired-end.
- Save results to: the project where your results will be saved.
- General options for analysis:
 - *Negative reads filter*   
   Working with a ROI, immplies the possibility of having flanks that overlap in certain reads, therefore implying a negative ROI-length. With this option activated they are annotated in the locus stats, else they are represented as '[-]' together with the other allele candidates.
 - *Cluster information*  
   With this option activated, unique reads within a locus are compared to each other. Reads that differ little are annotated as such. Does require more processing time.
 - *Threshold*  
   Unique reads with an abundance lower than this value (in %), are discarded. It is reported in the locus stats how many reads were discarded in this way.
 - *Preview*  
   Analyzing very big fastq's can take a considerable amount of time. If you want a quick preview, select a random percentage of the file to analyze. For low values (2-10%), this will give you a quick analysis of the profile. If at this point all alleles indicate a clear single contributor and have at least 1000 loci per locus, it is probably not necessary to do an analysis on the full file.
- Alignment options  
  Different types of alignments occur during the process of analysis. With these options you can influence the processing.
 - *Primer buffer*  
   The number of bases at the end of the primer that will not be used for assigning the reads to loci. Choosing a higher buffer therefore means the locus assignment could be slightly less specific, but more reads will get assigned.
 - *Stutter buffer*  
   The stutters of the smallest allele for a locus are normally not in the database, and could have a negative-length ROI. Default value of this buffer is 1 to accomodate that. This allows all stutters to be seen as flanking out is performed with a flank 1 repeat unit smaller.
 - *Flankout*  
   If you see a large amount of negative reads in the analysis, or a high abundant unique read with very poor flanks, turn this feature off. The analysis will then be done between the primers. Previously unknown alleles can be discovered this way.
 - *Homopolymers compressed*  
   Long homopolymers in the flanks could stutter during PCR. This option annotates flanks of loci that were possibly affected by this.
 - *Flankout by alignment*  
   If this option is activated, flanks are removed with our alignment algorithm, instead of the k-mer based flexible flanking.

After selecting options, launch analysis.

###Review results.
When the analysis is done, BaseSpace will have automatically made a report with all the results.  
In the report, there is a link to the parameters chosen for this analysis ('Inputs'), then a quick visual overview of the analysis to indicate if it looks like a normal profile, followed by the detailed profile.

Suggested steps:

- Click on the image to download it, and visually go over it one locus at a time.
- For each locus, having the visual indication close by, go over the alleles and validate them by selecting the checkbox, or if the stats indicate poor quality, deselect them.

###Make profile and save it locally
- After reviewing all loci, click "Make profile" at the top of "Detailed profile".
- A new browser window will open with all the alleles in the profile. Save it locally.  
  (For now it is not possible to save it in your project, so choose a filename that refers to the project/result.) 
  
##More information
- Original paper: [My-Forensic-Loci-queries (MyFLq) framework for analysis of forensic STR data generated by massive parallel sequencing](http://dx.doi.org/10.1016/j.fsigen.2013.10.012)