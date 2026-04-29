# Spywords: AI Spymaster Strategy Engine

Spywords is an AI-powered adaptation of the classic word-association game Codenames. This project moves beyond a simple "logic game" by utilizing **Natural Language Processing (NLP)** and **GloVe Word Embeddings** to power an autonomous AI Spymaster. 

## 🧠 The AI Engine: GloVe Word Vectors

Instead of relying on hardcoded word associations, Spywords uses **GloVe (Global Vectors for Word Representation)** — specifically the `glove-wiki-gigaword-50` model loaded via the Gensim library.

Word embeddings represent words as high-dimensional mathematical vectors. Words that appear in similar contexts in large bodies of text (like Wikipedia) have vectors that point in similar directions. By calculating the **Cosine Similarity** between these vectors, the AI can mathematically determine how "related" two words are.

## ⚙️ How Clues Are Generated

When you ask the AI Spymaster to generate a clue, it does not pick randomly. It executes a rigorous optimization algorithm to find the absolute best word to connect its team's targets while avoiding danger.

Here is the exact step-by-step process:

1. **Vocabulary Search:** The AI scans the top 10,000 most common words in its vocabulary.
2. **Rule Enforcement:** It instantly disqualifies any word currently on the board or any word that is a direct substring of a board word (to prevent illegal clues).
3. **Scoring Candidates:** For every valid potential clue, it calculates a **Strategy Score** using a risk-reward formula.
4. **Selection:** It sorts all candidates by their final score and randomly selects one from the top 5 to 10 candidates. This ensures high-quality clues while maintaining variety between turns.

## 🧮 The Strategy Formula: Why Certain Words Are Chosen

The AI chooses words by maximizing a mathematical score defined as:

`Score = Reward - (0.5 * Penalty) - (Risk Aversion * Death Risk)`

### 1. Reward (Target Similarity)
The AI calculates the cosine similarity between the potential clue and your team's unrevealed words. It sorts these similarities and takes the average of the top *N* targets it is trying to connect. 
*Goal: Find a word highly related to our team's words.*

### 2. Penalty (Opponent/Neutral Similarity)
The AI checks the potential clue against all enemy words and neutral words. The penalty is equal to the **maximum** similarity found. If the clue is too closely related to even a single enemy/neutral word, it gets heavily penalized.
*Goal: Avoid accidentally giving the other team a point or ending the turn early.*

### 3. Death Risk (Assassin Similarity)
The AI checks the potential clue against the Assassin word. The risk is equal to this similarity multiplied by a `Risk Aversion` coefficient (which scales based on difficulty). 
*Goal: Stay as far away from the game-ending Assassin word as mathematically possible.*

---

*By leveraging GloVe word embeddings and this optimization formula, Spywords provides a true AI opponent capable of nuanced, creative, and strategic word associations.*
