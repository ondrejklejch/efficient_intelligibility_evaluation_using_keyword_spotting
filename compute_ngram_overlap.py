import sys
import re
import glob
import gzip
from collections import defaultdict


def get_ngrams(sentence, order):
  words = sentence.split()
  return [' '.join(words[i:i+order]) for i in range(0, len(words) - order + 1)]

def load_ngrams(path):
  ngrams = defaultdict(set)
  ngram_order_pattern = re.compile(r'\\(\d)-grams:')
  with gzip.open(path, 'rt') as f:
    inside = False
    for line in f:
      line = line.lower().strip()

      if inside and line == '':
        inside = False
        continue

      if inside:
        word = line.split('\t')[1]
        ngrams[order].add(word)

      match = ngram_order_pattern.match(line)
      if match is not None:
        order = int(match.group(1))
        inside = True

  return ngrams

def normalize_sentence(sentence):
  sentence = sentence.lower()
  for replacement in [('.', ' '), (',', ' '), ('!', ' '), ('?', ' '), ('-', ' '), ('"', ' '), (';', ' '), ('’', "'"), (':', ' ')]:
    sentence = sentence.replace(replacement[0], replacement[1])

  return ' '.join(sentence.split())

def compute_ngram_overlap(sentence, ngrams):
  score = 1.
  for order in [1, 2, 3, 4]:
    count = 0
    total = 0
    for ngram in get_ngrams(sentence, order):
      count += ngram in ngrams[order]
      total += 1

    score *= (float(count) / total + 1e-2) ** 0.25

  return score

def main(arpa_path, input_path, output_path):
  ngrams = load_ngrams(arpa_path)
  with open(input_path, 'r') as f_in, open(output_path, 'w') as f_out:
    for line in f_in:
      name, sentence = line.strip().split(None, 1)
      sentence = normalize_sentence(sentence)

      if not all(w in ngrams[1] for w in sentence.split()):
        continue

      if len(sentence.split()) < 4:
        continue

      score = compute_ngram_overlap(sentence, ngrams)
      print(f'{score:.2f} {name} {sentence}', file=f_out)


if __name__ == '__main__':
  arpa_path = sys.argv[1]
  input_path = sys.argv[2]
  output_path = sys.argv[3]

  main(arpa_path, input_path, output_path)
