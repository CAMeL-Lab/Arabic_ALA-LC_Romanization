# -*- coding: utf-8 -*-
"""
Goes through a directory with xml record file(s), collecting Arabic records into a single xml collection.
Records are considered Arabic if 2 conditions are met:
        1) 880 - alternative representation field contains any arabic characters
        2) 008 - language field is 'ara'

"""

import logging
from pathlib import Path
import pymarc
import pandas as pd
import os
import re
from camel_tools.utils.charsets import AR_LETTERS_CHARSET
import argparse
from funcy import log_durations
import sys
import repackage
repackage.up()
from utils import get_xml_paths

def has_ar(text):
    '''checks string for any arabic characters'''    
    for char in text:
        try:
            if char in AR_LETTERS_CHARSET:
                return  True
        except Exception as e:
            print(e)
            return False


def has_ar_880(record):
    '''checks record if it has 880 field (alternative representation), and if the field has any arabic in it'''
    alternate_representation = record.get_fields('880')
    if alternate_representation:
        for item in alternate_representation:
            if has_ar(str(item)):
                return True

def getlang008(record):
    '''returns the 3 letter language code of a record marked in the 008 field'''
    f = record.get_fields('008')
    if f:
        return f[0].value()[35:38]
    else:
        return 'na'


def pull_arabic(record,writer):
    '''checks if record is arabic and 1) appends to list of lines, 2) writes entire record into writer'''
    global counter880
    global counter008
    global counter
    counter += 1
    if getlang008(record)=='ara':        
        counter008 += 1
        if has_ar_880(record):
            writer.write(record)            
            counter880 += 1
            if counter880%1000==0:
                logging.info(f'{counter880} records collected...')


@log_durations(logging.info)
def main():
    '''parses args pointing to record xml paths, specifies output paths, and applies "pull_arabic"'''
    logger = logging.getLogger(__name__)
    logger.info('collecting arabic records and extracting parallel Arabic/Romanized representations')

    parser = argparse.ArgumentParser()
    
    parser.add_argument('input_directory',help='path to directory containing records')
    parser.add_argument('-f','--sub_directory_filter',help='select a particular subdirectory inside a complex directory structure')
    parser.add_argument('-n','--name',help='optional source name, otherwise take directory name')
    
    args = parser.parse_args()

    if args.name:
        name = args.name
    else:
        name = args.input_directory.split('/')[-1]
    logger.info(f'source: {name}')
    
    
    record_paths = get_xml_paths(args.input_directory, args.sub_directory_filter)

    writer = pymarc.XMLWriter(open(f'data/arabic_records/{name}.xml','wb'))

    for path in record_paths:
        xmlname = path.split('/')[-1].replace('.xml','')
        pymarc.map_xml(lambda record: pull_arabic(record,writer=writer), path)
    writer.close()

    global counter008
    global counter880
    logger.info(f'# of Arabic records ("ara" in language field 008): {counter008}')
    # logger.info(f'# of records collected (only those with Arabic script in alt representation field 880): {counter880}')


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]



    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    

    counter008 = 0 # records with ara in 008 
    counter880 = 0 # total records collected
    counter = 0
    main()
    
    
    logging.info(f'Read {counter} records')
    logging.info(f'Collected {counter880} records with parallel Arabic script representations')
