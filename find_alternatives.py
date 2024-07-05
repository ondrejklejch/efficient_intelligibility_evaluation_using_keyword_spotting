import sys
import kenlm
import json
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer


stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

def are_words_too_similar(w1, w2):
  if w1 == w2:
    return True

  if w1.replace('z', 's') == w2:
    return True

  if w1.replace('s', 'z') == w2:
    return True

  if stemmer.stem(w1) == stemmer.stem(w2):
    return True

  return False

def load_similar_words(path):
  similar_words = defaultdict(list)
  with open(path, 'r') as f:
    for line in f:
      word, alternatives_json = line.strip().split(None, 1)
      for s, w in json.loads(alternatives_json):
        # Avoid homophones
        if s == 0:
          continue
  
        similar_words[word].append(w)

  return similar_words

def score_sentence(model, s):
  return sum(prob for prob, _, _ in model.full_scores(s))

def print_solution(lm_score, name, sentence, words, ppl, solution, f_out):
  if solution is None:
    return
  
  i = solution[0]
  ref = ' '.join(words[1:i] + ['*%s*' % words[i]] + words[i+1:-1])
  print(lm_score, name, sentence, file=f_out)
  print(f'ref: {ref} ({ppl:.2f})', file=f_out)
  for k, (w, s) in enumerate(solution[1]):
    sen = ' '.join(words[1:i] + ['*%s*' % w] + words[i+1:-1])
    print('  %d: %s (%.2f)' % (k, sen, s), file=f_out)
  
  print('', file=f_out)

def main(arpa_path, similar_words_path, text_path, output_path):
  model = kenlm.LanguageModel(arpa_path)
  similar_words = load_similar_words(similar_words_path)
  with open(text_path, 'r') as f, open(output_path, 'w') as f_out:
    for line in f:
      lm_score, name, sentence = line.strip().split(None, 2)
      words = ['<s>'] + sentence.split() + ['</s>']
      
      best_score = None
      solution = None
      for i in range(2, len(words) - 2):
        scores = []
        if words[i] not in similar_words:
          continue
  
        if len(words[i]) <= 3:
          continue
  
        for w in similar_words[words[i]]:
          if w in stop_words:
            continue

          if are_words_too_similar(words[i], w):
            continue

          # We don't want to select alternative that is too similar to some other word in the sentence.
          if any(are_words_too_similar(w, w1) for w1 in words[1:-1]):
            continue

          sen = ' '.join(words[:i] + [w] + words[i+1:])
          scores.append((w, score_sentence(model, sen)))
      
        # We don't want alternatives with similar stem
        sorted_scores = []
        for score in sorted(scores, key=lambda x: x[1], reverse=True):
          if any(are_words_too_similar(score[0], s[0]) for s in sorted_scores):
            continue
          sorted_scores.append(score)

        if len(sorted_scores) < 3:
          continue

        word_score = sorted_scores[3][1] if len(sorted_scores) >= 4 else sorted_scores[-1][1]
        if best_score is None or best_score < word_score:
          best_score = word_score
          solution = (i, sorted_scores[:4])
      
      ppl = score_sentence(model, ' '.join(words))
      print_solution(lm_score, name, sentence, words, ppl, solution, f_out)

if __name__ == '__main__':
  arpa_path = sys.argv[1]
  similar_words_path = sys.argv[2]
  text_path = sys.argv[3]
  output_path = sys.argv[4]

  main(arpa_path, similar_words_path, text_path, output_path)
