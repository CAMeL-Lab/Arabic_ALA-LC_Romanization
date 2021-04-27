# -*- coding: utf-8 -*-

# MIT License
#
# Copyright (c) 2018 New York University Abu Dhabi
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""This module contains a function for generating MADAMIRA XML configs.  The generate_config() function takes in a list of input sentences, and generates a config file ready for MADAMIRA analysis.
 NOTE: modified from original for LOC_transcribe
"""
from xml.sax.saxutils import escape

from jinja2 import Template
import six

feats = [
                    'bw',
                    'gloss',
                    'diac',
                    'lemma',
                    'asp',
                    'cas',
                    'gen', # mada only gives form gen/num... calima should be fgen/fnum
                    'mod',
                    'num', # mada only gives form gen/num... calima should be fgen/fnum
                    'per',
                    # 'rat',  # rationality does NOT match (calima vs mada)
                    'stt',  # this might not match..
                    'vox',
                    'pos',
                    'prc0',
                    'prc1',
                    'prc2',
                    'prc3',
                    'enc0',
                    ]
# {{ separate_punct }}"
#{{ preprocess }}
_MADAMIRA_CONFIG_TEMPLATE = Template('''<?xml version="1.0" encoding="UTF-8"?>
<madamira_input xmlns="urn:edu.columbia.ccls.madamira.configuration:0.1">
    <madamira_configuration>
        <preprocessing sentence_ids="false"
            separate_punct="false"
            input_encoding="UTF8"/>
        <overall_vars output_encoding="UTF8" dialect="MSA"
            output_analyses="TOP" morph_backoff="NOAN_PROP"/>  
        <requested_output>
            <req_variable name="PREPROCESSED" value="false" />
            <req_variable name="DIAC" value="true" />
            <req_variable name="STEM" value="true" />
            <req_variable name="GLOSS" value="true" />
            <req_variable name="LEMMA" value="true" />
            <req_variable name="ASP" value="true" />
            <req_variable name="CAS" value="true" />
            <req_variable name="ENC0" value="true" />
            <req_variable name="GEN" value="true" />
            <req_variable name="MOD" value="true" />
            <req_variable name="NUM" value="true" />
            <req_variable name="PER" value="true" />
            <req_variable name="POS" value="true" />
            <req_variable name="PRC0" value="true" />
            <req_variable name="PRC1" value="true" />
            <req_variable name="PRC2" value="true" />
            <req_variable name="PRC3" value="true" />
            <req_variable name="STT" value="true" />
            <req_variable name="VOX" value="true" />
            <req_variable name="LENGTH" value="true" />
            <req_variable name="OFFSET" value="true" />
            <req_variable name="NER" value="true" />
            <req_variable name="BPC" value="true" />
            <req_variable name="BW" value="true" />
        </requested_output>
        <tokenization>
        <scheme alias="MyD3">
            <!-- Same as D3 -->
            <scheme_override alias="MyD3"
                             form_delimiter="\u00B7"
                             include_non_arabic="true"
                             mark_no_analysis="false"
                             token_delimiter="D"
                             tokenize_from_BW="false">
                <split_term_spec term="PRC3"/>
                <split_term_spec term="PRC2"/>
                <split_term_spec term="PART"/>
                <split_term_spec term="PRC0"/>
                <split_term_spec term="REST"/>
                <!-- <split_term_spec term="ENC0"/> -->
                <token_form_spec enclitic_mark="+"
                                 proclitic_mark="+"
                                 token_form_base="WORD"
                                 transliteration="UTF8">
                    <!-- <normalization type="ALEF"/>
                    <normalization type="YAA"/>
                    <normalization type="DIAC"/>
                    <normalization type="LEFTPAREN"/>
                    <normalization type="RIGHTPAREN"/> -->
                </token_form_spec>
            </scheme_override>
        </scheme>
    </tokenization>
    </madamira_configuration>
    <in_doc id="ExampleDocument">
    {% for sentence in sentences %}
        <in_seg id="SENT_{{ sentence[0] }}">
            {{ sentence[1] }}
        </in_seg>
    {% endfor %}
    </in_doc>
</madamira_input>
''')


def _force_unicode(s):
    if isinstance(s, six.text_type):
        return s
    else:
        return s.decode('utf-8')


def _sentence_gen(sentences):
    for sentence in enumerate(sentences):
        yield (sentence[0], escape(_force_unicode(sentence[1])))


def generate_config(sentences, separate_punct=True):
    """Generate a MADAMIRA XML config given a list of sentences.

    Arguments:
        sentences {list} -- the list of sentences to be diacritized.

    Keyword Arguments:
        separate_punct {bool} -- separate punctuation (default: {False}).

    Returns:
        string -- the generated config.
    """

    return _MADAMIRA_CONFIG_TEMPLATE.render(
        sentences=_sentence_gen(sentences),
        preprocess=str(not separate_punct).lower(),
        separate_punct=str( separate_punct).lower())
