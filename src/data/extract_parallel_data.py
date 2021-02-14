'''
Extracts all linked lines from marcxml files (linked by marcfield 880 subfield 6)
'''
import os
import sys
import pymarc
import pandas as pd
import re
import logging
from funcy import log_durations
import argparse
import repackage
repackage.up()
from utils import get_xml_paths



def get_links6(record):
    ''' returns list of all the 880 alternative representation links from subfield '6' '''
    links6 = []
    for field in record.get_fields('880'):
        links6.append(field['6'])#.strip('/r').split('-'))
    return links6


def get_alternative_rep(record,link6):
    '''returns dict of all the subfield:alternative_representation for a particular linked field'''
    
    lines = {}
    for field in record.get_fields('880'):
        if field['6']==link6:
            for subfield in field:
                
                tag_key = subfield[0]
                tag_value = subfield[1]

                if tag_key in lines:
                    lines[tag_key].append(tag_value)
                else:
                    if tag_key!='6':
                        lines[tag_key] = [tag_value]
    return lines

def get_main_rep(record,link6):
    '''returns dict of all the subfield:main_representation for a particular linked field'''
    lines = {}
    linked_tag = re.sub(r'(\d+\-\d+).*',r'\1', link6).split('-')
    for field in record.get_fields(linked_tag[0]):
        link = field.get_subfields('6')
        if link and len(link)==1 and '-' in link[0]:
            link = link[0]
            if link.split('-')[1] == linked_tag[1]:
                for subfield in field:
                    tag_key = subfield[0]
                    tag_value = subfield[1]
                    if tag_key in lines:
                        lines[tag_key].append(tag_value)
                    else:
                        if tag_key!='6':
                            lines[tag_key] = [tag_value]
        else:
            pass # skip over badly formed records
    return lines
                

def parse_marc(record,source,index,):
    '''returns a pandas dataframe of parallel main/alternative representations contained in a record, skipping badly formed records and subfields.  
    if skip_bad is False the data frame will have an additional column called "link-error" marking bad entries '''
    parallel = []
    links = get_links6(record)
    for l in links:
        tag = l.split('-')[0]
        if "-" in l: #no hyphen means link is malformed so we skip entry
            link = linked_tag = re.sub(r'(\d+\-\d+).*',r'\1', l)[1]
        else:
            break
        rom = get_main_rep(record,l)
        ar = get_alternative_rep(record,l)
        
        try:
            parallel.append(pd.DataFrame(data={'link-error':False,'tag':tag,'link':link,'rom_raw':pd.Series(rom).explode(),'ar_raw':pd.Series(ar).explode(),'source':source,'recID':f'{source}-{index}'}).reset_index().rename(columns={'index':'subtag'}))
        except:
            parallel.append(pd.DataFrame(data={'link-error':True,'tag':tag,'link':link,'rom_raw':pd.Series(rom),'ar_raw':pd.Series(ar),'source':source,'recID':f'{source}-{index}'}).reset_index().rename(columns={'index':'subtag'}))

    return pd.concat(parallel)




@log_durations(logging.info)
def extract_lines(record_xml):
    index = 0
    parsed_all = []
    sourcename = record_xml.split('/')[-1].replace('.xml','')
    records = pymarc.parse_xml_to_array(record_xml)
    for r in records:
        index += 1
        parsed_record = parse_marc(r,source=sourcename,index=index)
        parsed_all.append(parsed_record)
        
        if index%1000 == 0:
            print(f"# of extracted records: {index} ...")
            # logging.info(f"# of extracted records: {index} ...")
    
    print(f"Extracted {index} records from {sourcename}.xml")
    logging.info(f"Extracted {index} records from {sourcename}.xml")
    return pd.concat(parsed_all)


@log_durations(logging.info)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_directory', default='data/arabic_records/', nargs='?', help='path to directory containing xml records')
    parser.add_argument('output', default='data/extracted_lines/extracted_lines.tsv', nargs='?', help= 'specify file for storing output')
    parser.add_argument('-f','--files', nargs='+', help= 'optionally specify which specific file(s) to extract from')
    args = parser.parse_args()

    

    data_paths = []
    if args.files:
        data_paths.extend(args.files)
    else:
        data_paths = get_xml_paths(args.input_directory)
        
    
    nl = '\n'
    

    extracted = []

    for path in data_paths:
        print(f"Extracting from: {path}")
        logging.info(f"Extracting parallel lines from: {path}")

        extracted.append(extract_lines(path))

    extracted = pd.concat(extracted)


    extracted.to_csv(args.output,sep='\t',index=False)
    
    print(f"Extracting parallel lines to {args.output}")
    logging.info(f"Extracting parallel lines to {args.output}")

if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt,filename='reports/extract_job.log',filemode='a')

    main()