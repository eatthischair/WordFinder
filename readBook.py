import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from wordfreq import zipf_frequency
from PyMultiDictionary import MultiDictionary
import re


dictionary = MultiDictionary()


book = epub.read_epub('casanova.epub')

counter = 0
text_content = []
word_data = []
position = 0
languages = ['en', 'fr', 'de', 'it', 'es', 'pl', 'ru']
langPos = 0

seen_words = set()
unique_word_data = []


for item in book.get_items():
  if item.get_type() == ebooklib.ITEM_DOCUMENT:
      # Parse HTML content
      soup = BeautifulSoup(item.get_content(), 'html.parser')
      # Extract text, removing HTML tags
      text = soup.get_text()
      text = re.sub(r"[^\w\s']|(?<!\w)'|'(?!\w)", ' ', text)
      text = ' '.join(text.split())
      text_content.append(text)

      words = text.lower().split()

      for word in words:
        if word not in seen_words:
          seen_words.add(word)
          freq = zipf_frequency(word, 'en', wordlist='large')
          if freq <= 3:
              definition = dictionary.meaning(languages[langPos], word)
              print('def', word, definition)

              # If not English word, try other languages until get a result
              if definition[1] == '':
                  while definition[1] == '' and langPos < len(languages):
                      langPos += 1
                      definition = dictionary.meaning(languages[langPos], word)
                      if definition[1] != '':
                          langPos = 0
                          break


              word_obj = {
                  'word': word,
                  'frequency': freq,
                  'position': position,
                  'definition': definition
              }
              word_data.append(word_obj)

  position += 1
  print('pos', position, word_data)


# for word_obj in word_data:
#     if word_obj['word'] not in seen_words:
#         seen_words.add(word_obj['word'])
#         unique_word_data.append(word_obj)

# word_data = unique_word_data
word_data = sorted(word_data, key=lambda x: x['frequency'])

print('word data', word_data)

# with open('output.txt', 'w', encoding='utf-8') as f:
#         f.write('\n\n'.join(word_data))

with open('output.txt', 'w', encoding='utf-8') as f:
    # Convert each dictionary to a string representation
    output_lines = [f"{obj['word']}: {obj['frequency']} (position: {obj['position']})" for obj in word_data]
    f.write('\n'.join(output_lines))