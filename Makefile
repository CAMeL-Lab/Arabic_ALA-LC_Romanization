
## Download Datasets
download_data:
	git clone https://github.com/NYULibraries/aco-karms/ data/raw_records/aco/
	wget -nc -P data/raw_records/umich http://www.lib.umich.edu/files/umich_bib.xml.gz
	gunzip data/raw_records/umich/*
	for val in {01..43}; do wget -nc -P data/raw_records/loc https://www.loc.gov/cds/downloads/MDSConnect/BooksAll.2016.part$$val.xml.gz; done  
	gunzip data/raw_records/loc/*


## extract parallel lines
extract_lines:
	python3 src/loc_transcribe.py extract 

## filter, clean, and split data into train dev test
data_set:
	python3 src/loc_transcribe.py preprocess --split


## train full mle learning curve
train_mles:
	python3 src/loc_transcribe.py train mle

# prep dataset and create dalma scripts
prep_seq2seq:
	python3 src/loc_transcribe.py train seq2seq --prep

# (dalma scripts) trains full learning curve and predicts dev
train_seq2seq: 
	python3 src/loc_transcribe.py train seq2seq --train

predict_seq2seq_test:
	python3 src/loc_transcribe.py predict seq2seq --predict_test -s 1.0

align_seq2seq:
	python3 src/loc_transcribe.py predict seq2seq -b predictions_out/seq2seq/dev/seq2seq_size1.0.out predictions_out/mle_morph/dev/mle_morph_size1.0.out 
	python3 src/loc_transcribe.py predict seq2seq -b predictions_out/seq2seq/dev/seq2seq_size1.0.out predictions_out/mle_simple/dev/mle_simple_size1.0.out
	python3 src/loc_transcribe.py predict seq2seq -b predictions_out/seq2seq/dev/seq2seq_size1.0.out predictions_out/morph/dev/morph.out 

align_seq2seq_test:
	python3 src/loc_transcribe.py predict seq2seq -b predictions_out/seq2seq/test/seq2seq_size1.0.out predictions_out/mle_morph/test/mle_morph_size1.0.out 
	python3 src/loc_transcribe.py predict seq2seq -b predictions_out/seq2seq/test/seq2seq_size1.0.out predictions_out/mle_simple/test/mle_simple_size1.0.out
	python3 src/loc_transcribe.py predict seq2seq -b predictions_out/seq2seq/test/seq2seq_size1.0.out predictions_out/morph/test/morph.out 


predict_translit:
	python3 src/loc_transcribe.py predict simple dev
	python3 src/loc_transcribe.py predict morph dev 

predict_translit_test:
	python3 src/loc_transcribe.py predict translit_simple test 
	python3 src/loc_transcribe.py predict translit_morph test 

## predict full mle curve
predict_mles:
	python3 src/loc_transcribe.py predict mle dev -m models/mle/size1.0.tsv -b predictions_out/simple/dev/simple.out  
	python3 src/loc_transcribe.py predict mle dev -m models/mle/size0.5.tsv -b predictions_out/simple/dev/simple.out
	python3 src/loc_transcribe.py predict mle dev -m models/mle/size0.25.tsv -b predictions_out/simple/dev/simple.out
	python3 src/loc_transcribe.py predict mle dev -m models/mle/size0.125.tsv -b predictions_out/simple/dev/simple.out
	python3 src/loc_transcribe.py predict mle dev -m models/mle/size0.0625.tsv -b predictions_out/simple/dev/simple.out
	python3 src/loc_transcribe.py predict mle dev -m models/mle/size0.03125.tsv -b predictions_out/simple/dev/simple.out
	python3 src/loc_transcribe.py predict mle dev -m models/mle/size0.015625.tsv -b predictions_out/simple/dev/simple.out
	python3 src/loc_transcribe.py predict mle dev -m models/mle/size1.0.tsv -b predictions_out/morph/dev/morph.out


predict_mles_test:
	python3 src/loc_transcribe.py predict mle test -m models/mle/size1.0.tsv -b predictions_out/simple/test/simple.out 
	python3 src/loc_transcribe.py predict mle test -m models/mle/size1.0.tsv -b predictions_out/morph/test/morph.out  



## evaluate full mle curve
evaluate:
	#eval seq2seq dev aligned
	python3 src/loc_transcribe.py evaluate predictions_out/aligned_seq2seq/dev/seq2seq_size1.0Xmle_morph_size1.0.out data/processed/dev.tsv 
	python3 src/loc_transcribe.py evaluate predictions_out/aligned_seq2seq/dev/seq2seq_size1.0Xmle_simple_size1.0.out data/processed/dev.tsv 
	python3 src/loc_transcribe.py evaluate predictions_out/aligned_seq2seq/dev/seq2seq_size1.0Xmorph.out data/processed/dev.tsv 
	
	#eval mle_morph dev
	python3 src/loc_transcribe.py evaluate predictions_out/mle_morph/dev/mle_morph_size1.0.out
	
	#eval morph dev
	python3 src/loc_transcribe.py evaluate predictions_out/morph/dev/morph.out

	
	#eval mle_simple curve
	python3 src/loc_transcribe.py evaluate predictions_out/mle_simple/dev/mle_simple_size1.0.out 
	python3 src/loc_transcribe.py evaluate predictions_out/mle_simple/dev/mle_simple_size0.5.out
	python3 src/loc_transcribe.py evaluate predictions_out/mle_simple/dev/mle_simple_size0.25.out
	python3 src/loc_transcribe.py evaluate predictions_out/mle_simple/dev/mle_simple_size0.125.out
	python3 src/loc_transcribe.py evaluate predictions_out/mle_simple/dev/mle_simple_size0.0625.out
	python3 src/loc_transcribe.py evaluate predictions_out/mle_simple/dev/mle_simple_size0.03125.out
	python3 src/loc_transcribe.py evaluate predictions_out/mle_simple/dev/mle_simple_size0.015625.out

	#eval simple dev
	python3 src/loc_transcribe.py evaluate predictions_out/simple/dev/simple.out

	#eval seq2seq dev curve
	python3 src/loc_transcribe.py evaluate predictions_out/seq2seq/dev/seq2seq_size1.0.out
	python3 src/loc_transcribe.py evaluate predictions_out/seq2seq/dev/seq2seq_size0.5.out
	python3 src/loc_transcribe.py evaluate predictions_out/seq2seq/dev/seq2seq_size0.25.out
	python3 src/loc_transcribe.py evaluate predictions_out/seq2seq/dev/seq2seq_size0.125.out
	python3 src/loc_transcribe.py evaluate predictions_out/seq2seq/dev/seq2seq_size0.0625.out
	python3 src/loc_transcribe.py evaluate predictions_out/seq2seq/dev/seq2seq_size0.03125.out
	python3 src/loc_transcribe.py evaluate predictions_out/seq2seq/dev/seq2seq_size0.015625.out

	#eval seq2seq test aligned
	python3 src/loc_transcribe.py evaluate predictions_out/aligned_seq2seq/test/seq2seq_size1.0Xmle_morph_size1.0.out data/processed/test.tsv 
	python3 src/loc_transcribe.py evaluate predictions_out/aligned_seq2seq/test/seq2seq_size1.0Xmle_simple_size1.0.out data/processed/test.tsv 
	python3 src/loc_transcribe.py evaluate predictions_out/aligned_seq2seq/test/seq2seq_size1.0Xmorph.out data/processed/test.tsv

	#eval mle_morph test
	python3 src/loc_transcribe.py evaluate predictions_out/mle_morph/test/mle_morph_size1.0.out data/processed/test.tsv 

	#eval morph test
	python3 src/loc_transcribe.py evaluate predictions_out/morph/test/morph.out data/processed/test.tsv 

	#eval simple test
	python3 src/loc_transcribe.py evaluate predictions_out/simple/test/simple.out data/processed/test.tsv 

	#eval seq2seq test
	python3 src/loc_transcribe.py evaluate predictions_out/seq2seq/test/seq2seq_size1.0.out data/processed/test.tsv 

	#eval mle_simple test
	python3 src/loc_transcribe.py evaluate predictions_out/mle_simple/test/mle_simple_size1.0.out data/processed/test.tsv 


## redo custom part of pipeline
# train_mles
redo:  predict_translit predict_mles evaluate
	

## update requirements
update_requirements:
	pipdeptree -f --warn silence | grep -v '[[:space:]]' > requirements.txt
	

## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using flake8
lint:
	flake8 src

