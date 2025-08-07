from flask import Flask, request, jsonify, send_from_directory
from collections import Counter
import os

app = Flask(__name__)

# Load word lists
WORD_LISTS = {}
LETTER_FREQS = {}

def load_words(language):
    if language not in WORD_LISTS:
        filepath = f"{language}.txt"
        if not os.path.exists(filepath):
            return []
        with open(filepath, 'r', encoding='utf-8') as f:
            words = [line.strip().upper() for line in f if len(line.strip()) == 5]
            WORD_LISTS[language] = words
            LETTER_FREQS[language] = Counter("".join(words))
    return WORD_LISTS[language]

def word_score(word, freq_counter):
    return sum(freq_counter[c] for c in set(word))

# Serve the frontend
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# Filtering route
@app.route('/filter', methods=['POST'])
def filter_words():
    data = request.json

    language = data.get('language', 'english').lower()
    words = load_words(language)
    if not words:
        return jsonify({"error": f"Language '{language}' not supported."}), 400

    freq_counter = LETTER_FREQS[language]

    included = set(data.get('included', '').upper())
    excluded = set(data.get('excluded', '').upper())
    correct_positions = {int(k): v.upper() for k, v in data.get('correct_positions', {}).items()}
    wrong_positions = {int(k): set(v.upper() for v in lst) for k, lst in data.get('wrong_positions', {}).items()}

    filtered = []
    for word in words:
        if any(ch in excluded for ch in word):
            continue
        if not included.issubset(set(word)):
            continue
        if any(word[pos] != val for pos, val in correct_positions.items()):
            continue
        if any(word[pos] in wrong for pos, wrong in wrong_positions.items()):
            continue
        filtered.append(word)

    scored = sorted(
        [(w, word_score(w, freq_counter)) for w in filtered],
        key=lambda x: x[1],
        reverse=True
    )

    return jsonify({
        "count": len(filtered),
        "top_words": [w for w, s in scored if s == scored[0][1]] if scored else [],
        "all_scored": scored
    })

if __name__ == '__main__':
    app.run(debug=True)
