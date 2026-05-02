import nltk
from nltk.corpus import wordnet as wn

nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

words = ['crocuta', 'symmetry', 'polygynandrous', 'lion', 'predator', 'africa']

for word in words:
    synsets = wn.synsets(word)
    if synsets:
        print(f"Word: {word}")
        for s in synsets:
            print(f"  - {s.name()}: {s.lexname()}")
    else:
        print(f"Word: {word} (Not found in WordNet)")
