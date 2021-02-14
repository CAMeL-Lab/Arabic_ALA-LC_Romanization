import pandas as pd
import argparse
from funcy import log_durations
import logging
from pathlib import Path
from camel_tools.utils.charsets import UNICODE_PUNCT_CHARSET
import repackage
repackage.up()
from data.make_dataset import depunc

project_dir = Path(__file__).resolve().parents[2]

def match(string1,string2):
    return string1==string2

def match_ignore_case(string1,string2):
    return str(string1).lower()==str(string2).lower()  ### figure out how to cast data frame to string from the start

def match_ignore_case_punc(string1,string2):
    string1 = depunc(str(string1).lower())
    string2 = depunc(str(string2).lower())
    return string1==string2

def match_ignore_case_punc_keep_hyphen(string1,string2):
    string1 = depunc(str(string1).lower(),keep_hyph=True)
    string2 = depunc(str(string2).lower(),keep_hyph=True)
    return string1==string2

class Word2Word():
    def __init__(self,dfrow,evalfuncs=[match,match_ignore_case,match_ignore_case_punc],additional_info=['sentID','comb.tag'],allow_misaligned=False):
            self.gold = str(dfrow['gold'])
            self.source = str(dfrow['source'])
            self.prediction = str(dfrow['prediction'])
            self.eval = pd.DataFrame(data= dict(map(lambda x: (x[0],pd.Series(x[1].split())),self.__dict__.items() )))
            
            for func in evalfuncs:
                self.eval[func.__name__] = self.eval.apply(lambda x: func(x['gold'],x['prediction']), axis=1)

            for column in additional_info:
                setattr(self,column,dfrow[column])
                self.eval[column] = dfrow[column]

            # misaligned gold/source
            if not len(self.gold.split())==len(self.source.split()):
                if allow_misaligned :
                    self.eval['aligned_source/gold'] = False
                    print(f'Misaligned gold/source sentID: {self.sentID}')
                else:
                    raise Exception(f'Misaligned gold/source on sentID: {self.sentID}')
            
            
            # misaligned prediction

            if not len(self.gold.split())==len(self.prediction.split()):
                self.eval['aligned_prediction'] = False
                # print(f'Misaligned gold/prediction sentID: {self.sentID}')         

class Sent2Sent():
    def __init__(self,golddf,prediction_lines,prediction_name=None,gold_name='rom',source_name='ar',additional_info=['sentID','comb.tag']):
        
        self.gold = golddf['rom'].values
        self.source = golddf['ar'].values
        self.prediction = prediction_lines
        

        if not len(self.gold) == len(self.prediction) :
            raise Exception('Unequal number of gold and prediction sentences')
        
        # sentence_dict = {'gold':self.gold,'source':self.source,'prediction':self.prediction}
        for column in additional_info:
            setattr(self,column,golddf[column].values)
        
        self.sent2sent = pd.DataFrame(data=self.__dict__)

        self.name = prediction_name
        self.additional_info = additional_info
        
    def calculate_word2word(self,evalfuncs=[match,match_ignore_case,match_ignore_case_punc]):
        sents = self.sent2sent.apply(lambda x: Word2Word(x,evalfuncs=evalfuncs,additional_info=self.additional_info),axis=1)
        word2word = pd.concat([sent.eval for sent in sents])
        sents
        for match in [column for column in word2word.columns if column.startswith('match')]:
            score = word2word[match].value_counts(normalize=True)[True]
            
            print(f'{self.name}\t{match}\t {score}')
        if 'aligned_prediction' in word2word.columns:
            count_misaligned = len(word2word[word2word['aligned_prediction']==False].drop_duplicates('sentID'))
        else:
            count_misaligned = 0
            
        print(f'{count_misaligned} misaligned sentences')
        setattr(self,'sents',sents)
        setattr(self,'word2word',word2word)
    
    def get_sent(self,sentID):
        if type(sentID)==list:
            return self.sent2sent[self.sent2sent['sentID'].isin(sentID)]
        else:
            return self.sent2sent[self.sent2sent['sentID'].isin([sentID])]
            
    def get_words(self,sentID):
        if type(sentID)==list:
            return self.word2word[self.word2word['sentID'].isin(sentID)]
        else:
            return self.word2word[self.word2word['sentID'].isin([sentID])]

    def write_to_file(self,path=None):
        if not path:
            path = f'evaluation/word2word-{self.name}.tsv'
        self.word2word.to_csv(path,sep='\t')

def score_invariable_order(s1,s2):
    s1 = s1.split()
    s2 = s2.split()
    l1 = len(s1)
    l2 = len(s2)
    if l1!=l2:
        raise('sentences are of different lengths')
    
    d = {}
    for t1 in s1:
        if t1 in d:
            d[t1] += 1
        else:
            d[t1] = 1

    for t2 in s2:
        if t2 in d:
            d[t2] -= 1
        else:
            d[t2] = -1

    score = sum([x for x in d.values() if x<0])

    # difference = []
    # for t,c in d.items():
    #     # if c >0:
    #     #     difference.extend(['+'+t]*abs(c))
    #     if c<0:
    #         difference.extend(['-'+t]*abs(c))
    #     else:
    #         pass
    

    # return difference
    score = (l1+score)/l1
    return round(score,2)




def score_match(matchcolumn,to_string=True):
    if to_string:
        score = matchcolumn.value_counts(normalize=True).to_string()
        print(matchcolumn.name)
        print(score)
        logging.info(f'score for: {matchcolumn.name}\n{score}')
    else:
        return matchcolumn.value_counts(normalize=True)
    


@log_durations(logging.info)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('predictions', help='path to prediction lines')
    parser.add_argument('gold', help='path to tsv containing gold "rom" column')
    parser.add_argument('-o','--out',help= 'output directory for evaluation')
    args = parser.parse_args()

    logging.info(f'evaluating {args.predictions} ...')

    

    # load predictions
    # predictions = pd.read_table(args.predictions,header=None)[0]
    with open(args.predictions,'r') as p:
        predictions = [x.strip() for x in p.readlines()]
        predictions = pd.Series(predictions)

    # load gold tsv
    gold_df = pd.read_csv(args.gold,delimiter='\t')

    name = args.predictions.split('/')[-1]
    evaluation = Sent2Sent(gold_df, predictions, name)
    
    evaluation.calculate_word2word()
    
    evaluation.write_to_file(args.out)


if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt,filename='reports/evaluate.log',filemode='a')

    main()