import weights from "../detector_weights.json";

// Mirrors sklearn's default TfidfVectorizer token_pattern: r"(?u)\b\w\w+\b"
// (word characters, length >= 2). Must match exactly or the vocabulary lookup
// silently misses features.
const WORD_TOKEN = /[\p{L}\p{N}_]{2,}/gu;

function wordTokens(text) {
  return text.toLowerCase().match(WORD_TOKEN) || [];
}

function wordNgrams(tokens, nMin, nMax) {
  const grams = [];
  for (let n = nMin; n <= nMax; n += 1) {
    for (let i = 0; i + n <= tokens.length; i += 1) {
      grams.push(tokens.slice(i, i + n).join(" "));
    }
  }
  return grams;
}

// sklearn's char_wb analyzer: pad each whitespace-delimited word with a single
// space on both sides, then take all char n-grams that stay within that
// padded word (never crossing into the next word).
function charWbNgrams(text, nMin, nMax) {
  const words = text.toLowerCase().split(/\s+/).filter(Boolean);
  const grams = [];
  for (const word of words) {
    const padded = ` ${word} `;
    for (let n = nMin; n <= nMax; n += 1) {
      for (let i = 0; i + n <= padded.length; i += 1) {
        grams.push(padded.slice(i, i + n));
      }
    }
  }
  return grams;
}

function termCounts(grams) {
  const counts = new Map();
  for (const gram of grams) counts.set(gram, (counts.get(gram) || 0) + 1);
  return counts;
}

// Reproduces one TfidfVectorizer: sublinear_tf (1 + log(tf)), multiply by the
// stored IDF, then L2-normalize — sklearn's defaults, and what the pipeline
// was trained with.
function tfidfVector(counts, vec) {
  const values = new Map();
  let normSquared = 0;
  for (const [term, count] of counts) {
    const index = vec.vocabulary[term];
    if (index === undefined) continue;
    const tf = 1 + Math.log(count);
    const value = tf * vec.idf[index];
    values.set(index, value);
    normSquared += value * value;
  }
  const norm = Math.sqrt(normSquared) || 1;
  for (const [index, value] of values) values.set(index, value / norm);
  return values;
}

export function scoreText(text) {
  const tokens = wordTokens(text);
  const wordGrams = wordNgrams(tokens, weights.word.ngram_range[0], weights.word.ngram_range[1]);
  const charGrams = charWbNgrams(text, weights.char.ngram_range[0], weights.char.ngram_range[1]);

  const wordVec = tfidfVector(termCounts(wordGrams), weights.word);
  const charVec = tfidfVector(termCounts(charGrams), weights.char);

  // FeatureUnion concatenates in declaration order: word features first,
  // then char features offset by the word vocabulary size.
  let logit = weights.intercept;
  for (const [index, value] of wordVec) logit += value * weights.coef[index];
  for (const [index, value] of charVec) logit += value * weights.coef[weights.n_word_features + index];

  const probability = 1 / (1 + Math.exp(-logit));
  return probability;
}
