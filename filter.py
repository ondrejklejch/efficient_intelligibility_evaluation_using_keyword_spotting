import sys
from collections import Counter

def get_ngrams(sentence, order):
  words = sentence.split()
  return [' '.join(words[i:i+order]) for i in range(0, len(words) - order + 1)]

def compute_overlap(src, tgt):
  src_ngrams = Counter(get_ngrams(src, 4))
  tgt_ngrams = Counter(get_ngrams(tgt, 4))

  total = 0.0
  overlap = 0.0
  for ngram, count in src_ngrams.items():
    total += count
    overlap += min(count, tgt_ngrams[ngram])

  return overlap / total

def count_repeated_words(text):
  ngrams = Counter(text.split())

  num_repeated = 0
  for _, count in ngrams.items():
    num_repeated += count - 1

  return num_repeated

sentences = []
with open(sys.argv[1], 'r') as f_in, \
    open(sys.argv[2], 'w') as f_out:
  for line in f_in:
    score, utt, text = line.strip().split(' ', 2)
    num_words = len(text.split())

    if float(score) > 0.2:
      continue

    if num_words < 7 or num_words > 10:
      continue

    num_repeated_words = count_repeated_words(text)
    if num_repeated_words > 0:
      continue

    overlap = 0.0
    if sentences:
      overlap = max([compute_overlap(text, s) for s in sentences])

    if overlap < 0.2:
      print(score, utt, text, file=f_out)
      sentences.append(text)

