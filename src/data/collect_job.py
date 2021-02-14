'''this program uses "collect_arabic_records.py" to collect records from the projects 3 data sources.'''

import os,sys
import logging

log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)


logging.info('ACO')
os.system('python3 src/data/collect_arabic_records.py data/all_records/aco/work -f marcxml_out -n aco') #aco

logging.info('umich')
os.system('python3 src/data/collect_arabic_records.py data/all_records/umich') #umich

logging.info('loc')
os.system('python3 src/data/collect_arabic_records.py data/all_records/loc') #loc
    
    


