from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from collections import Counter
import os

app = Flask(__name__)
CORS(app, origins=["https://basstarrica.github.io"])

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
    return send_from_directory('.', 'onlineindex.html')

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
        word_upper = word.upper()

        # Exclude words with any excluded letters
        if any(ch in excluded for ch in word_upper):
            continue

        # Check correct positions (green)
        if any(word_upper[pos] != val for pos, val in correct_positions.items()):
            continue

        # Check wrong positions (yellow)
        if any(word_upper[pos] in wrong for pos, wrong in wrong_positions.items()):
            continue

        # Check included letters (green + yellow), allowing for duplicates
        required_counts = Counter()
        for letter in included:
            # Count how many times this letter appears in correct and wrong positions
            correct_count = sum(1 for pos, val in correct_positions.items() if val == letter)
            wrong_count = sum(1 for pos, wrongs in wrong_positions.items() if letter in wrongs)
            required_counts[letter] = correct_count + wrong_count

        word_letter_counts = Counter(word_upper)
        if any(word_letter_counts[letter] < required_counts[letter] for letter in included):
            continue

        filtered.append(word_upper)

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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)





