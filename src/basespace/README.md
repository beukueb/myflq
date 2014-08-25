#MyFLq version 1.0 
[My Forensic Loci queries]

###Introduction
Routine use of massively parallel sequencing (MPS) for forensic genomics is on the horizon. The last few years, several programs have been developed to analyze forensic MPS data and generate DNA profiles. However, none have yet been tailored to the needs of the forensic analyst who does not possess an extensive bioinformatics background.
We developed our forensic MPS data analysis framework MyFLq into a user-friendly, web-based application. Data from forensic samples that are sequenced on an Illumina sequencer can be uploaded to Basespace during acquisition, and can subsequently be analyzed using the MyFLq application. Implemented features are an interactive graphical report of the results, an interactive threshold selection bar, and an allele length-based analysis in addition to the sequenced-based analysis. STR loci and SNP loci are both supported.

###Requirements
The tool expects a loci csv-file (similar to [loci.csv](https://raw.githubusercontent.com/beukueb/myflq/master/src/loci/myflqpaper_loci.csv)), a validated-allele csv-file for all the included loci  (similar to [alleles.csv](https://raw.githubusercontent.com/beukueb/myflq/master/src/alleles/myflqpaper_alleles.csv)) and a fastq datafile, whereupon the datafile's profile is extracted.

The datafile can be a single-individual-source or multiple-individual-source sample. Profile results depend on both csv files. Loci.csv will determine the number of loci that will be analyzed; alleles.csv will determine the region of interest [ROI] of those loci.

####Custom loci.csv and alleles.csv
When custom loci.csv and alleles.csv are required and it is no problem that they become public, one can submit them on the [support page](http://ugent-forensics.van-neste.be/). If you do not want those files to be public, you can copy paste them into the respective textbox in the input form. In this case pay close attention to the format of your *.csv files. There should not be any whitespace, unless at the end of a line or within a commented line.

###Choose input settings
Input settings are documented on the BaseSpace MyFLq form, or in the documentation on [MyFLhub](https://github.com/beukueb/myflq)

After selecting options, launch analysis.

###Review results.
The report primarily shows the visual profile.

Functionality:

- On the X-axis (with the loci names), you can zoom in and move the axis to go over all the loci.
- Putting the mouse on an allele candidate bar, shows all information for that candidate. Clicking on the bar will fix the information box for this candidate.
- Clicking on a checked "In profile" in the information box will deselect a candidate from the profile, even if its abundance is higher than the threshold.
- Selecting 'Absolute length' in the settings, will reorganize the graph. All allele candidates will now be plotted within each locus proportionate to their sequence length.

Suggested steps:

- Set the threshold to a level appropriate for the sample noise.
- In case it is known to be a single contributor sample, closely inspect all sequences from loci that have more than 2 alleles.

###Make profile and save it locally
- After reviewing all loci, click "Make profile".
- A new browser window will open with all the alleles in the profile. Save it locally.  
  (For now it is not possible to save it in your project, so choose a filename that refers to the project/result.) 
- If there is a locus with more than two alleles, it is indicated that based on the threshold this profile derives from a multi-contributor sample. If there is maximum two alleles per locus, the probability of that profile can be retrieved from the [ENFSI STRbase](http://strbase.org/) site.

###Test files
Click [here](https://basespace.illumina.com/s/0xvp6KW9GCfi) to get access to a project with forensic samples that can be used to try out MyFLq.