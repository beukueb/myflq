#MyFLq version 1.0 [My Forensic Loci queries]
Open source, straightforward analysis tool for forensic DNA samples.

The tool expects a loci csv-file (similar to [loci.csv](https://github.com/beukueb/myflq/blob/master/src/loci/myflqpaper_loci.csv)), a validated-allele csv-file for all the included loci  (similar to [alleles.csv](https://github.com/beukueb/myflq/blob/master/src/alleles/myflqpaper_alleles.csv)) and a fastq datafile, whereupon the datafile's profile is extracted.

The datafile can be a single-individual-source or multiple-individual-source sample. Profile results depend on both csv files. Loci.csv will determine the number of loci that will be analyzed; alleles.csv will determine the region of interest [ROI] of those loci.

##Custom loci.csv and alleles.csv
When custom loci.csv and alleles.csv are required, one can submit them on [Github](https://github.com/beukueb/myflq) with a pull request (ask a bioinformatician to help if you don't know how). The program will then be rebuild, and your files will then be available to select within 24 hours.

If you do not want those files to be public, at this point, the only other option is to pull the MyFLq to your server with [Docker](https://www.docker.io/), afterwhich you can start it up, with the following command:
   sudo docker run beukueb/myflq localWebApp.sh

MyFLq will then run as a local web application on the indicated port. For more information on this see [MyFLhub](https://github.com/beukueb/myflq)

##Workflow on BaseSpace MyFLq
To start the app on BaseSpace simply launch it, which will direct you to the input form.

