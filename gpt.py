import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from wordfreq import zipf_frequency
from PyMultiDictionary import MultiDictionary
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------ Setup ------------------
dictionary = MultiDictionary()
book = epub.read_epub('casanova.epub')

languages = ['en', 'fr', 'de', 'it', 'es', 'pl', 'ru']
text_content = []
seen_words = set()
word_data = []

# ------------------ Extract words ------------------
for item in book.get_items():
    if item.get_type() == ebooklib.ITEM_DOCUMENT:
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        text = soup.get_text()
        text = re.sub(r"[^\w\s']|(?<!\w)'|'(?!\w)", ' ', text)
        text = ' '.join(text.split())
        text_content.append(text)

# Combine all text into one big string
full_text = ' '.join(text_content)
words = full_text.lower().split()

print(f"Total words: {len(words)}")
unique_words = list(set(words))
print(f"Unique words: {len(unique_words)}")

# ------------------ Compute frequencies ------------------
word_freqs = []
for word in unique_words:
    if len(word) < 3 or not word.isalpha():
        continue
    freq = zipf_frequency(word, 'en', wordlist='large')
    if freq <= 3:  # only rare words
        word_freqs.append((word, freq))

# Sort rare words by frequency (rarest first)
word_freqs.sort(key=lambda x: x[1])
print(f"Rarest words: {len(word_freqs)}")

# Optional: limit to N words to save time
LIMIT = 1000
word_freqs = word_freqs[:LIMIT]

# ------------------ Define lookup function ------------------
definition_cache = {}

def lookup_word(word):
    if word in definition_cache:
        return definition_cache[word]

    for lang in languages:
        try:
            definition = dictionary.meaning(lang, word)
            if definition and definition[1] != '':
                definition_cache[word] = (word, lang, definition[1])
                return definition_cache[word]
        except Exception:
            continue

    definition_cache[word] = (word, None, '')
    return definition_cache[word]

# ------------------ Parallel dictionary lookups ------------------
results = []
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_word = {executor.submit(lookup_word, word): (word, freq) for word, freq in word_freqs}

    for i, future in enumerate(as_completed(future_to_word), 1):
        word, freq = future_to_word[future]
        try:
            word, lang, definition = future.result()
            results.append({
                'word': word,
                'frequency': freq,
                'language': lang,
                'definition': definition
            })
        except Exception as e:
            results.append({
                'word': word,
                'frequency': freq,
                'language': None,
                'definition': f'Error: {e}'
            })

        if i % 50 == 0:
            print(f"Processed {i}/{len(word_freqs)} words...")

# ------------------ Output ------------------
results = sorted(results, key=lambda x: x['frequency'])

with open('output2.txt', 'w', encoding='utf-8') as f:
    for obj in results:
        line = f"{obj['word']}: {obj['frequency']} ({obj['language']}) -> {obj['definition']}\n"
        f.write(line)

print("✅ Done! Results saved to output.txt")
