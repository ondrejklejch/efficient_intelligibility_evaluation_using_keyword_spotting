import sys
import re
import gzip
import json
import glob
from abydos.distance import PhoneticEditDistance, Levenshtein
from phonecodes import phonecodes
from multiprocessing import Pool
from tqdm import tqdm


psd = PhoneticEditDistance()
lev = Levenshtein()

def most_similar(word, words, lexicon):
  most_similar_words = []
  for w in sorted(words):
    if word == w:
      continue

    # We don't want short alternatives
    if len(w) < 3:
      continue

    if abs(len(lexicon[word]) - len(lexicon[w])) > 2:
      continue

    if lev.dist_abs(lexicon[word], lexicon[w]) > 3:
      continue

    dist = psd.dist(lexicon[word], lexicon[w])
    if dist > 0.3:
      continue

    most_similar_words.append((dist, w))

  return word, list(sorted(most_similar_words))[:50]

def load_lexicon(path):
  lexicon = {}
  with open(path, 'r') as f:
    for line in f:
      word, pronunciation = line.strip().split('#')[0].split(None, 1)
      if word.endswith(')'):
        continue

      lexicon[word] = "".join(phonecodes.convert(pronunciation, "arpabet", "ipa").split())
      print(word, lexicon[word])

  return lexicon

def load_unigrams(path, lexicon):
  words = set()
  pattern = re.compile(r'\\1-grams:')
  with gzip.open(path, 'rt') as f:
    inside = False
    for line in f:
      line = line.lower().strip()
  
      if inside and line == "":
        inside = False
        break
  
      if inside:
        prob = float(line.split("\t")[0])
        word = line.split("\t")[1]
        if word in lexicon and prob >= -6:
          words.add(word)
  
      match = pattern.match(line)
      if match is not None:
        inside = True

  return words

def load_words(path, lexicon):
  words = set()
  with open(path, 'r') as f:
    for line in f:
      sentence = line.strip().split(None, 2)[2]
      for word in sentence.split():
        # We want to skip short words
        if len(word) <= 3:
          continue

        if word in lexicon:
          words.add(word)

  return words

def cb(data):
  word, unigrams, lexicon = data
  return most_similar(word, unigrams, lexicon)

def main(lexicon_path, arpa_path, text_path, output_path):
  lexicon = load_lexicon(lexicon_path)
  unigrams = load_unigrams(arpa_path, lexicon)
  words = load_words(text_path, lexicon) 

  with Pool(32) as p, open(output_path, 'w') as f:
    unigrams = list(sorted(unigrams))
    words = list(sorted(words))
    for word, most_similar in tqdm(p.imap(cb, ((w, unigrams, lexicon) for w in words)), total=len(words)):
      print(word, json.dumps(most_similar), file=f)

if __name__ == '__main__':
  lexicon_path = sys.argv[1]
  arpa_path = sys.argv[2]
  text_path = sys.argv[3]
  output_path = sys.argv[4]

  main(lexicon_path, arpa_path, text_path, output_path)
