"""
SPYWORDS — Flask Backend & AI Strategy Engine
======================================================
A Codenames-inspired AI strategy game where word-embedding vectors
power the Spymaster's clue generation using cosine similarity,
risk-reward optimization, and configurable difficulty.
"""

from flask import Flask, render_template, jsonify, request, session
import numpy as np
import random
import uuid
from sklearn.decomposition import PCA
from word_bank import WORD_BANK
from ai_engine import WordSimilarityEngine

# ──────────────────────────────────────────────────────────────
# Flask App Setup
# ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "semantic-saboteur-2026-secret"

# ──────────────────────────────────────────────────────────────
# Load AI Model
# ──────────────────────────────────────────────────────────────
print("\n🧠 Initializing AI Similarity Engine...")
engine = WordSimilarityEngine()
print(f"✅ Engine ready! Vocabulary: {len(engine.index_to_key)} words\n")

# In-memory game storage
games = {}

# ──────────────────────────────────────────────────────────────
# Game Logic
# ──────────────────────────────────────────────────────────────

def create_new_game(difficulty="medium"):
    """Generate a fresh 5×5 game board with team assignments."""
    # Filter word bank to words in engine vocab
    valid_words = [w for w in WORD_BANK if w in engine]
    if len(valid_words) < 25:
        # Fallback: use whatever we have
        valid_words = list(engine.vocab)
    board_words = random.sample(valid_words, 25)

    # Standard Codenames: 9 red (goes first), 8 blue, 7 neutral, 1 assassin
    assignments = (
        ["red"] * 9 +
        ["blue"] * 8 +
        ["neutral"] * 7 +
        ["assassin"] * 1
    )
    random.shuffle(assignments)

    board = []
    for i, (word, team) in enumerate(zip(board_words, assignments)):
        board.append({
            "word": word,
            "team": team,
            "revealed": False,
            "position": i,
        })

    game = {
        "id": str(uuid.uuid4()),
        "board": board,
        "current_turn": "red",
        "phase": "spymaster",
        "red_remaining": 9,
        "blue_remaining": 8,
        "current_clue": None,
        "current_number": 0,
        "guesses_remaining": 0,
        "game_log": [],
        "game_over": False,
        "winner": None,
        "difficulty": difficulty,
        "clue_analysis": None,
    }
    return game


def generate_clue(game):
    """
    AI Spymaster Strategy Engine
    ─────────────────────────────
    Searches the word-vector vocabulary for the optimal clue word.

    Strategy Formula:
        Score = Reward − 0.5 × Penalty − α × AssassinRisk

    Where:
        Reward   = mean cosine similarity to top-N target words
        Penalty  = max cosine similarity to any opponent/neutral word
        Risk     = max cosine similarity to the assassin word
        α        = risk aversion coefficient (scales with difficulty)
    """
    team = game["current_turn"]
    difficulty = game["difficulty"]

    # Risk aversion (higher = safer, more obscure clues)
    risk_aversions = {"easy": 1.0, "medium": 2.0, "hard": 3.0}
    risk_aversion = risk_aversions.get(difficulty, 2.0)

    # Gather board words by category
    targets = [c["word"] for c in game["board"]
               if c["team"] == team and not c["revealed"]]
    opponent = "blue" if team == "red" else "red"
    opponent_words = [c["word"] for c in game["board"]
                      if c["team"] == opponent and not c["revealed"]]
    neutral_words = [c["word"] for c in game["board"]
                     if c["team"] == "neutral" and not c["revealed"]]
    assassin_words = [c["word"] for c in game["board"]
                      if c["team"] == "assassin" and not c["revealed"]]

    bad_words = opponent_words + neutral_words
    board_set = set(c["word"] for c in game["board"])

    max_connect = min(2, len(targets))

    best_clue = None
    best_score = -999
    best_connections = []
    all_candidates = []

    # Search all words in vocabulary (excluding board words)
    for potential_clue in engine.index_to_key:
        if potential_clue in board_set:
            continue
        if any(potential_clue in w or w in potential_clue for w in board_set):
            continue
        if len(potential_clue) < 3:
            continue

        try:
            # ── REWARD: similarity to our team's words ──
            target_sims = {t: engine.similarity(potential_clue, t)
                           for t in targets}
            sorted_sims = sorted(target_sims.values(), reverse=True)
            reward = float(np.mean(sorted_sims[:max_connect]))

            # ── PENALTY: similarity to opponent + neutral words ──
            if bad_words:
                bad_sims = [engine.similarity(potential_clue, bw) for bw in bad_words]
                penalty = max(bad_sims)
            else:
                penalty = 0.0

            # ── RISK: similarity to the assassin ──
            if assassin_words:
                assassin_sims = [engine.similarity(potential_clue, aw)
                                 for aw in assassin_words]
                death_risk = max(assassin_sims)
            else:
                death_risk = 0.0

            # ── STRATEGY SCORE ──
            score = reward - (0.5 * penalty) - (risk_aversion * death_risk)

            candidate = {
                "word": potential_clue,
                "score": round(float(score), 3),
                "reward": round(float(reward), 3),
                "penalty": round(float(penalty), 3),
                "death_risk": round(float(death_risk), 3),
                "target_sims": {k: round(float(v), 3) for k, v in target_sims.items()},
            }

            if len(all_candidates) < 5 or score > all_candidates[-1]["score"]:
                all_candidates.append(candidate)
                all_candidates.sort(key=lambda x: x["score"], reverse=True)
                all_candidates = all_candidates[:5]

            if score > best_score:
                best_score = score
                best_clue = potential_clue
                connected = [t for t, s in sorted(target_sims.items(),
                             key=lambda x: x[1], reverse=True) if s > 0.15]
                best_connections = connected[:max_connect]
        except Exception:
            continue

    number = len(best_connections) if best_connections else 1

    # Build similarity map for ALL unrevealed board words
    board_similarities = {}
    for card in game["board"]:
        if not card["revealed"] and best_clue:
            try:
                sim = engine.similarity(best_clue, card["word"])
                board_similarities[card["word"]] = {
                    "similarity": round(float(sim), 3),
                    "team": card["team"],
                }
            except Exception:
                board_similarities[card["word"]] = {
                    "similarity": 0,
                    "team": card["team"],
                }

    explanation = _build_explanation(best_clue, best_connections,
                                     board_similarities, assassin_words)

    analysis = {
        "clue": best_clue,
        "number": number,
        "score": round(float(best_score), 3),
        "connections": best_connections,
        "top_candidates": all_candidates,
        "board_similarities": board_similarities,
        "explanation": explanation,
    }
    return analysis


def _build_explanation(clue, connections, board_sims, assassin_words):
    """Generate a human-readable reasoning for the AI's clue choice."""
    if not clue:
        return "The AI could not find a suitable clue."

    parts = [f'The AI chose "{clue.upper()}"']

    if connections:
        conn_parts = []
        for word in connections:
            sim = board_sims.get(word, {}).get("similarity", 0)
            conn_parts.append(f"{word.upper()} ({sim:.2f})")
        parts.append(f" to connect: {', '.join(conn_parts)}")

    dangerous = [(w, d["similarity"]) for w, d in board_sims.items()
                 if d["team"] == "assassin"]
    if dangerous:
        most_dangerous = max(dangerous, key=lambda x: x[1])
        parts.append(
            f". It stays safe from assassin \"{most_dangerous[0].upper()}\""
            f" (similarity: {most_dangerous[1]:.2f})"
        )

    return "".join(parts) + "."


def end_turn(game):
    """Switch to the other team's spymaster phase."""
    game["current_turn"] = "blue" if game["current_turn"] == "red" else "red"
    game["phase"] = "spymaster"
    game["current_clue"] = None
    game["current_number"] = 0
    game["guesses_remaining"] = 0
    game["clue_analysis"] = None


def get_client_state(game):
    """Return game state safe to send to the browser."""
    return {
        "game_id": game["id"],
        "board": game["board"],
        "current_turn": game["current_turn"],
        "phase": game["phase"],
        "red_remaining": game["red_remaining"],
        "blue_remaining": game["blue_remaining"],
        "current_clue": game["current_clue"],
        "current_number": game["current_number"],
        "guesses_remaining": game["guesses_remaining"],
        "game_log": game["game_log"],
        "game_over": game["game_over"],
        "winner": game["winner"],
        "difficulty": game["difficulty"],
    }


# ──────────────────────────────────────────────────────────────
# API Routes
# ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/new-game", methods=["POST"])
def api_new_game():
    data = request.json or {}
    difficulty = data.get("difficulty", "medium")
    game = create_new_game(difficulty)
    games[game["id"]] = game
    session["game_id"] = game["id"]
    return jsonify(get_client_state(game))


@app.route("/api/generate-clue", methods=["POST"])
def api_generate_clue():
    game_id = session.get("game_id")
    if not game_id or game_id not in games:
        return jsonify({"error": "No active game"}), 400

    game = games[game_id]
    if game["game_over"]:
        return jsonify({"error": "Game is over"}), 400

    analysis = generate_clue(game)

    game["current_clue"] = analysis["clue"]
    game["current_number"] = analysis["number"]
    game["guesses_remaining"] = analysis["number"] + 1
    game["phase"] = "operative"
    game["clue_analysis"] = analysis

    game["game_log"].append({
        "type": "clue",
        "team": game["current_turn"],
        "clue": analysis["clue"].upper() if analysis["clue"] else "???",
        "number": analysis["number"],
    })

    return jsonify({
        **get_client_state(game),
        "analysis": analysis,
    })


@app.route("/api/guess", methods=["POST"])
def api_guess():
    game_id = session.get("game_id")
    if not game_id or game_id not in games:
        return jsonify({"error": "No active game"}), 400

    game = games[game_id]
    if game["game_over"] or game["phase"] != "operative":
        return jsonify({"error": "Not in guessing phase"}), 400

    data = request.json
    word = data.get("word")

    card = None
    for c in game["board"]:
        if c["word"] == word and not c["revealed"]:
            card = c
            break
    if not card:
        return jsonify({"error": "Invalid word"}), 400

    card["revealed"] = True
    game["guesses_remaining"] -= 1

    result = {
        "word": word,
        "team": card["team"],
        "correct": card["team"] == game["current_turn"],
        "game_over": False,
        "turn_over": False,
        "winner": None,
        "assassin_hit": False,
    }

    game["game_log"].append({
        "type": "guess",
        "team": game["current_turn"],
        "word": word,
        "result": card["team"],
        "correct": result["correct"],
    })

    if card["team"] == "red":
        game["red_remaining"] -= 1
    elif card["team"] == "blue":
        game["blue_remaining"] -= 1

    if card["team"] == "assassin":
        game["game_over"] = True
        game["winner"] = "blue" if game["current_turn"] == "red" else "red"
        result.update(game_over=True, winner=game["winner"], assassin_hit=True)
    elif game["red_remaining"] == 0:
        game["game_over"] = True
        game["winner"] = "red"
        result.update(game_over=True, winner="red")
    elif game["blue_remaining"] == 0:
        game["game_over"] = True
        game["winner"] = "blue"
        result.update(game_over=True, winner="blue")
    elif not result["correct"] or game["guesses_remaining"] <= 0:
        result["turn_over"] = True
        end_turn(game)

    return jsonify({
        **get_client_state(game),
        "result": result,
    })


@app.route("/api/pass-turn", methods=["POST"])
def api_pass_turn():
    game_id = session.get("game_id")
    if not game_id or game_id not in games:
        return jsonify({"error": "No active game"}), 400

    game = games[game_id]
    if game["game_over"]:
        return jsonify({"error": "Game is over"}), 400

    game["game_log"].append({"type": "pass", "team": game["current_turn"]})
    end_turn(game)
    return jsonify(get_client_state(game))


@app.route("/api/vector-plot", methods=["GET"])
def api_vector_plot():
    """Return 2D PCA projection of board words + clue."""
    game_id = session.get("game_id")
    if not game_id or game_id not in games:
        return jsonify({"error": "No active game"}), 400

    game = games[game_id]
    clue = game.get("current_clue")

    words, vectors, teams = [], [], []

    for card in game["board"]:
        vec = engine.get_vector(card["word"])
        words.append(card["word"])
        vectors.append(vec)
        teams.append(card["team"])

    if clue:
        words.append(clue)
        vectors.append(engine.get_vector(clue))
        teams.append("clue")

    if len(vectors) < 3:
        return jsonify({"error": "Not enough vectors"}), 400

    pca = PCA(n_components=2)
    coords = pca.fit_transform(np.array(vectors))

    points = []
    for i, (word, team) in enumerate(zip(words, teams)):
        points.append({
            "word": word,
            "team": team,
            "x": round(float(coords[i][0]), 4),
            "y": round(float(coords[i][1]), 4),
        })

    return jsonify({"points": points})


# ──────────────────────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🕵️  SPYWORDS is running at http://localhost:5050\n")
    app.run(debug=True, port=5050, use_reloader=False)
