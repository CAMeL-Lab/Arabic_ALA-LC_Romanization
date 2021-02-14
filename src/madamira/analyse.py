
import requests
from io import BytesIO
from lxml import etree
from .generate_config import feats, generate_config
import os
from pathlib import Path

project_dir = Path(__file__).resolve().parents[2]

class madaSentenceObject():
    def __init__(self,words,analysis,svm,toks):
        self.words = words #list of raw words (undiacritized and untokenized)
        self.analysis = dict(zip(words,analysis))  # dictionary with word keys and database analysis values
        self.svm = dict(zip(words,svm)) # dictionary with word keys and svm analysis values
        self.toks = toks # list of strings of diacritized '+' separated tokens #TODO: change to more meainigful name
        # print(self.toks)
        # print(self.words)
        
        # TODO: this requires fixing because all it does is makes sure there is analysis. ultimately theres no real need for svm method but removing it breaks everything
        for word in self.analysis:
            if self.analysis[word]:
                self.analysis[word]['svm'] = False
            else:
                self.analysis[word] = self.svm[word]
                self.analysis[word]['svm'] = True
        

    def __str__(self):
        return (self.words,self.analysis,self.svm,self.toks)

    def __repr__(self):
        return f'#WORDS#: {self.words}; #AN#: {self.analysis}; #SVM#: {self.svm}; #TOKS#: {self.toks}'

def write_xml(xml_string, write_path):
    with open(write_path,'w') as o:
        o.write(xml_string)

def load_analysis(xml_path):
    '''returns a parsetree to be parsed using parse_analyser_output()'''
    with open(xml_path,'r') as xml:
        xml = xml.read()
        loaded_parsetree = etree.iterparse(BytesIO(xml.encode('utf8')), events=('start', 'end'), load_dtd=False)
        return loaded_parsetree


def analyse_server(input_xml_config):
    ''' server mode: requires MADAMIRA server to be running''' #TODO: create a system call to start server (java -Xmx2500m -Xms2500m -XX:NewRatio=3 -jar MADAMIRA/MADAMIRA-release-20170403-2.1.jar -s)
    server_url="http://localhost:8223"
    response = requests.post(server_url, data=input_xml_config.encode('utf-8'))
    # print(response.content)
    loaded_parsetree = etree.iterparse(BytesIO(response.content), events=('start', 'end'), load_dtd=False) 
    return loaded_parsetree

def analyse_standalone(input_xml, output_xml,path_to_madamira=f'{project_dir}/MADAMIRA'): #TODO: check with Ossama!!!
    ''' analyzes input_xml config file and writes analysis to output_xml'''
    os.system('jenv global openjdk64-1.8.0.272')
    print(os.popen(f"{os.popen('jenv which java').read().strip()} -Xmx2500m -Xms2500m -XX:NewRatio=3 -jar {path_to_madamira}/MADAMIRA-release-20170403-2.1.jar -i {input_xml} -o {output_xml}").read())
    # os.system(f'java -Xmx2500m -Xms2500m -XX:NewRatio=3 -jar /Users/fae211/ba3sasah/LOC_transcribe/MADAMIRA/MADAMIRA-release-20170403-2.1.jar -i {input_xml} -o {output_xml}')


def generate_analyser_input(sentences):
    '''expects tokenized punctuation i.e using tokenize_skiphyph(sent)'''
    xml = generate_config(sentences)
    return xml

def parse_analyser_output(loaded_parsetree):  #TODO: is this the proper way to do this?
    '''a generator of madaSentenceObject sentences'''

    onsent = False
    onword = False
    onanalysis = False
    onsvm = False
    ontok = False

    for event,element in loaded_parsetree:
        
        # start sent
        if element.tag.endswith('out_seg') and event == 'start':
            onsent = True
            sentanalysis = []
            sentsvm = []
            senttok = []
            words = []
        elif onsent:

            # end sent
            if element.tag.endswith('out_seg') and event == 'end':
                onsent = False
                sentence = madaSentenceObject(words,sentanalysis,sentsvm,senttok) # save into madaSentenceObject class
                #
                #
                ###END OF LOOP
                yield sentence
                # sentences.append(sentence)
            
            # start word
            elif element.tag.endswith('word') and event == 'start':
                onword = True
                wordanalysis = []
                wordsvm = []
                wordtok = []
                words.append(element.get('word',''))
            elif onword:

                # end word
                if element.tag.endswith('word') and event == 'end':
                    onword = False  

                    sentanalysis.append(wordanalysis)
                    sentsvm.append(wordsvm)
                    senttok.append(wordtok)


                # start analysis    
                elif element.tag.endswith('analysis') and event == 'start':
                    onanalysis = True
                    analysis = {}

                elif onanalysis:
                    
                    # end analysis
                    if element.tag.endswith('analysis') and event == 'end':
                        onanalysis = False

                        wordanalysis = analysis

                    elif element.tag.endswith('morph_feature_set') and event == 'end':
                        
                        
                        for feat in feats:
                            analysis[feat] = element.get(feat,'')

                # start svm    
                elif element.tag.endswith('svm_prediction') and event == 'start':
                    
                    onsvm = True
                    svm = {}

                elif onsvm:
                    
                    # end svm
                    if element.tag.endswith('svm_prediction') and event == 'end':
                        onsvm = False

                        wordsvm = svm

                    elif element.tag.endswith('morph_feature_set') and event == 'end':                   
                        
                        for feat in feats:
                            svm[feat] = element.get(feat,'')
                
                # start tok    
                elif element.tag.endswith('tokenized') and event == 'start':
                    
                    ontok = True
                    tok = []

                elif ontok:
                    
                    # end tok
                    if element.tag.endswith('tokenized') and event == 'end':
                        ontok = False

                        wordtok = ''.join(tok)

                    elif element.tag.endswith('tok') and event == 'end':
                        
                        tok.append(element.get('form0',''))   

