# Arabic ALA-LC Romanization Tool

## Authors

- [Fadhl Eryani](https://github.com/fadhleryani/)
- Nizar Habash

## Dependencies

### Basic dependencies
`pip3 install -r requirements.txt`

### MADAMIRA

To run the MADAMIRA morphological analyser and disambiguator, you must obtain a MADAMIRA distribution through here:

- http://innovation.columbia.edu/technologies/cu14012_arabic-language-disambiguation-for-natural-language-processing-applications

* database used is almor-msa-s31.db (see documentation/MADAMIRA-UserManual p6 for more info)

Info on Buckwalter Part-of-Speech tags: 
- see /documentation/ATB-POSGuidelines-v3.7.pdf

MADAMIRA and Java requirements
- MADAMIRA will not run on versions of Java above 9
- We used openjdk64-1.8.0.272.  You can install it using `brew install --cask adoptopenjdk8`, or download from the website: https://adoptopenjdk.net/ (!make sure to select jdk8)
- We recommend you use [JENV](here: https://www.jenv.be/)

### Seq2Seq

To run the Seq2Seq model, you must obtain a copy of 
[Seq2Seq Transliteration Tool](https://github.com/alishazal/seq2seq-transliteration-tool) 
along with listed dependencies

## 

