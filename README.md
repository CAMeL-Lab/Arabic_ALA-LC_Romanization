# Arabic ALA-LC Romanization Tool

<!-- ## Publication

[Automatic Romanization of Arabic Bibliographic Records]() -->

## Authors

- [Fadhl Eryani](https://github.com/fadhleryani/)
- Nizar Habash

## Dependencies

### Basic dependencies
This project was developed using python 3.6, and tested in macOS and linux environments.  First you must install required packages:
`pip3 install -r requirements.txt`

### MADAMIRA

To run the MADAMIRA morphological analyser and disambiguator, you must have a MADAMIRA distribution in the project directory, which you can obtain from [here](http://innovation.columbia.edu/technologies/cu14012_arabic-language-disambiguation-for-natural-language-processing-applications)


The database used is almor-msa-s31.db (see `documentation/MADAMIRA-UserManual` p6 for more info).  If you have access to this database, you must have the database file inside `MADAMIRA/resources/` and setup the MADAMIRA config file located in `MADAMIRA/config/almor.properties` as follows:
- `ALMOR.text.MSA.database.name=almor-s31.db`


For info on the Buckwalter Part-of-Speech tag set used by MADAMIRA, see `/documentation/ATB-POSGuidelines-v3.7.pdf`

#### MADAMIRA and Java requirements
- MADAMIRA will not run on versions of Java above 9
- We used openjdk64-1.8.0.272.  You can install it using `brew install --cask adoptopenjdk8`, or download from the website: https://adoptopenjdk.net/ (make sure to select jdk8)
- We recommend you setup java using [JENV](here: https://www.jenv.be/)

### Seq2Seq

To run the Seq2Seq model, you must obtain a copy of Shazal & Usman's [Seq2Seq Transliteration Tool](https://github.com/alishazal/seq2seq-transliteration-tool).

`git clone https://github.com/alishazal/seq2seq-transliteration-tool.git seq2seq`

We ran our seq2seq systems with the GPU NVIDIA Tesla V100 PCIe 32 GB on NYU Abu Dhabi's High Performance Computing cluster, known as Dalma. We set the memory flag to 30GB. The .sh scripts that we ran can be seen in the file folder `/src/train/seq2seq_scripts/`.


## Data

Data for this project came from publicly available catalog databases stored in the [MARC (machine-readable cataloging) standard](https://www.loc.gov/marc/bibliographic/) xml format.  From those, we extracted, filtered, and cleaned parallel Arabic and Romanized entries and split them into Dev, Train, and Test sets.  If you are only interested in replicating our experimental setup, you only need the provided tsvs in `data/processed` and can skip the next section.

### Additional info on data sources extraction

Unless you are interested in exploring the source MARCxml dumps, or would like to apply our extraction and processing on different datasets, you can skip this section.

#### Data Sources

Arabic Collections Online (ACO):
`git clone https://github.com/NYULibraries/aco-karms/ data/raw_records/aco/`

Library of Congress (LOC): 
`for val in {01..43}; do wget -nc -P data/raw_records/loc https://www.loc.gov/cds/downloads/MDSConnect/BooksAll.2016.part$$val.xml.gz; done  
gunzip data/raw_records/loc/*`

University of Michigan (UMICH):
`wget -nc -P data/raw_records/umich http://www.lib.umich.edu/files/umich_bib.xml.gz
gunzip data/raw_records/umich/*`

## Running Arabic ALA-LC Romanization models

### 1. 

