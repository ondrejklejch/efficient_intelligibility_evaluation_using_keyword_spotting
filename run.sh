#!/bin/bash

set -e

stage=0
lexicon_path='assets/cmudict.dict'
arpa_path='assets/4gram_small.arpa.gz'
input_path='input.txt'
ngram_overlap_path='ngram_overlap.txt'
similar_words_path='similar_words.txt'
output_path='output.txt'

mkdir -p assets
if [ ! -f $lexicon_path ]; then
  wget -O $lexicon_path https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict
fi

if [ ! -f $arpa_path ]; then
  wget -O $arpa_path http://kaldi-asr.org/models/5/4gram_small.arpa.gz
fi

if [ $stage -le 0 ]; then
  echo Computing n-gram overlap
  python3 compute_ngram_overlap.py $arpa_path $input_path $ngram_overlap_path
fi

if [ $stage -le 1 ]; then
  echo Mining similar words
  python3 prepare_similar_words.py $lexicon_path $arpa_path $ngram_overlap_path $similar_words_path
fi

if [ $stage -le 2 ]; then
  echo Selecting alternative words
  python3 find_alternatives.py $arpa_path $similar_words_path $ngram_overlap_path $output_path
fi
