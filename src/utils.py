import os
import pymarc
from functools import partial
import pandas as pd
import re
import numpy as np

def get_xml_paths(root,dir_filter=''):
    '''finds all xml files inside a deep directory, with an optional subdirectory filter, in this case all folder named marcxml_out in any directory'''
    paths = []
    for path,dir,files in os.walk(root):
        if dir_filter:
            if path.endswith(dir_filter):
                for file in files:
                    if  file.endswith('.xml'):
                         paths.append('/'.join([path,file]))
        else:
            for file in files:
                if  file.endswith('.xml'):
                    paths.append('/'.join([path,file]))

    return paths


def write_collection(records,write_location):
    '''writes an array/generator of records into an xml collection file'''
    writer = pymarc.XMLWriter(open(write_location,'wb'))
    for record in records:
        if type(record)==pymarc.record.Record:
            writer.write(record)
        else:
            raise Exception('attempted to pass non-record object into record writer')
    writer.close()




