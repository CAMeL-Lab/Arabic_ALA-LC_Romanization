.PHONY: clean extract_data lint requirements

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROFILE = default
PROJECT_NAME = LOC_transcribe
PYTHON_INTERPRETER = python3

ifeq (,$(shell which conda))
HAS_CONDA=False
else
HAS_CONDA=True
endif

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Install Python Dependencies
requirements: test_environment
	$(PYTHON_INTERPRETER) -m pip install -U pip setuptools wheel
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt


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
	python3 src/loc_transcribe.py predict seq2seq -t -s 1.0

align_seq2seq:
	python3 src/loc_transcribe.py predict seq2seq -b predictions_out/seq2seq/dev/seq2seq_size1.0.out predictions_out/mle_morph/dev/mle_morph_size1.0.out 



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


## evaluate full mle curve
evaluate:
	# python3 src/loc_transcribe.py evaluate predictions_out/mle_simple/dev/mle_simple_size1.0.out 
	# python3 src/loc_transcribe.py evaluate predictions_out/mle_simple/dev/mle_simple_size0.5.out
	# python3 src/loc_transcribe.py evaluate predictions_out/mle_simple/dev/mle_simple_size0.25.out
	# python3 src/loc_transcribe.py evaluate predictions_out/mle_simple/dev/mle_simple_size0.125.out
	# python3 src/loc_transcribe.py evaluate predictions_out/mle_simple/dev/mle_simple_size0.0625.out
	# python3 src/loc_transcribe.py evaluate predictions_out/mle_simple/dev/mle_simple_size0.03125.out
	# python3 src/loc_transcribe.py evaluate predictions_out/mle_simple/dev/mle_simple_size0.015625.out

	# python3 src/loc_transcribe.py evaluate predictions_out/mle_morph/dev/mle_morph_size1.0.out

	# python3 src/loc_transcribe.py evaluate predictions_out/morph/dev/morph.out
	python3 src/loc_transcribe.py evaluate predictions_out/simple/dev/simple.out



## redo custom part of pipeline
# train_mles
redo:  predict_translit predict_mles evaluate
	

sync_seq2seq_predictions_dev:
	rsync -av --progress tunnel-dalma:/scratch/fae211/LOC_transcribe/seq2seq/output/predictions/line2line-dev.out ./predictions_out/seq2seq/dev/

sync_seq2seq_predictions_test:
	rsync -av --progress tunnel-dalma:/scratch/fae211/LOC_transcribe/seq2seq/output/predictions/line2line-test.out ./predictions_out/seq2seq/test/

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

## Upload Data to hpc
sync_data_to_hpc: clean
	# --delete
	# rsync -av --progress ./ --exclude="data/*/*" --exclude="reports/*" tunnel-dalma:/scratch/fae211/LOC_transcribe --delete
	rsync -av --progress ./ --exclude="data/*" --exclude="reports/*" --exclude="MADAMIRA/*" --exclude="predictions_out/*" --exclude="evaluation/*" --exclude="models/*" tunnel-dalma:/scratch/fae211/LOC_transcribe --delete

## Download Data from hpc
sync_data_from_hpc:
	# rsync -av --progress --exclude="all_records" tunnel-dalma:/scratch/fae211/LOC_transcribe/data/ ./data/ 
	# rsync -av --progress tunnel-dalma:/scratch/fae211/LOC_transcribe/reports/ ./reports/
	rsync -av --progress --exclude="all_records" fae211@dalma.abudhabi.nyu.edu:/scratch/fae211/LOC_transcribe/data/ ./data/ 
	rsync -av --progress fae211@dalma.abudhabi.nyu.edu:/scratch/fae211/LOC_transcribe/reports/ ./reports/
	

## Set up python interpreter environment
create_env:
ifeq (True,$(HAS_CONDA))
		@echo ">>> Detected conda, creating conda environment."
ifeq (3,$(findstring 3,$(PYTHON_INTERPRETER)))
	conda create --name $(PROJECT_NAME) python=3.7
else
	conda create --name $(PROJECT_NAME) python=2.7
endif
		@echo ">>> New conda env created. Activate with:\nsource activate $(PROJECT_NAME)"
else
	$(PYTHON_INTERPRETER) -m pip install -q virtualenv virtualenvwrapper
	@echo ">>> Installing virtualenvwrapper if not already installed.\nMake sure the following lines are in shell startup file\n\
	export WORKON_HOME=$$HOME/.virtualenvs\nexport PROJECT_HOME=$$HOME/Devel\nsource /usr/local/bin/virtualenvwrapper.sh\n"
	@bash -c "source `which virtualenvwrapper.sh`;mkvirtualenv $(PROJECT_NAME) --python=$(PYTHON_INTERPRETER)"
	@echo ">>> New virtualenv created. Activate with:\nworkon $(PROJECT_NAME)"
endif


#################################################################################
# PROJECT RULES                                                                 #
#################################################################################



#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
