import pandas as pd
import os
from pathlib import Path
import repackage
import argparse
repackage.up()
from data import make_seq2seq_dataset
from alignment import cross_align, align_wordsDF


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('prediction',help='file containing prediction sentences to be aligned')
    parser.add_argument('backoff',help='file containing backoff predictions to align to')
    parser.add_argument('output',help='output location')
    parser.add_argument('-d','--dont_backoff',action='store_false',help='align without backoff')
    args = parser.parse_args()
    
    print(args.__dict__)
    print(args.dont_backoff)
    print(type(args.dont_backoff))
    with open(args.prediction, 'r') as i:
        prediction = [x.strip() for x in i.readlines()]

    with open(args.backoff, 'r') as i:
        backoff = [x.strip() for x in i.readlines()]

    if len(prediction)!=len(backoff):
        raise Exception('unequal number of sentences between prediction and alignment backoff')

    aligned_predictions = []
    for idx, line in enumerate(prediction):
        aligned_sent = cross_align(backoff[idx],line,bckf=args.dont_backoff)
        aligned_predictions.append(aligned_sent)
    
    with open(args.output, 'w') as o:
        for line in aligned_predictions:
            o.write(f'{line}\n')

if __name__=="__main__":
    main()