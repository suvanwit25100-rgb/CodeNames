import streamlit as st
import gensim.downloader as api
import numpy as np
import random

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="SPYWORDS AI", layout="wide")
st.title("🕵️‍♂️ SPYWORDS: AI Spymaster")
st.markdown("An AI strategy game evaluating word-embedding vectors to minimize risk and maximize word association.")

# --- 2. LOAD THE AI MODEL (Word Vectors) ---
# We use @st.cache_resource so it only downloads/loads the 66MB model once!
@st.cache_resource
def load_model():
    with st.spinner("Downloading/Loading GloVe Word Vectors (this takes a minute the first time)..."):
        # glove-wiki-gigaword-50 is a fast, lightweight vector model
        return api.load("glove-wiki-gigaword-50")

model = load_model()

# --- 3. GAME BOARD SETUP ---
# A simplified list of nouns for our game board
BOARD_VOCAB = [
    "apple", "bank", "bat", "bear", "board", "bolt", "boot", "bow", "box", "bug",
    "car", "card", "cast", "chair", "charge", "club", "code", "cold", "cook", "crown",
    "dance", "day", "deck", "diamond", "dice", "dog", "engine", "eye", "face", "fall",
    "file", "fire", "fish", "fly", "foot", "force", "game", "gas", "glass", "hand",
    "heart", "hole", "horn", "ice", "key", "knight", "lab", "lap", "lead", "leaf"
]

def generate_board():
    board_words = random.sample(BOARD_VOCAB, 25)
    st.session_state.board = {
        "Red Team": board_words[0:8],
        "Blue Team": board_words[8:16],
        "Neutral": board_words[16:24],
        "Assassin": [board_words[24]]
    }

if "board" not in st.session_state:
    generate_board()

# --- 4. THE AI STRATEGY ENGINE (The core of your portfolio project) ---
def generate_clue(target_team, risk_aversion, max_words_to_connect):
    targets = st.session_state.board[target_team]
    
    # The things we want to avoid
    opponent_team = "Blue Team" if target_team == "Red Team" else "Red Team"
    bad_words = st.session_state.board[opponent_team] + st.session_state.board["Neutral"]
    assassin = st.session_state.board["Assassin"][0]
    
    # All words currently on the board (rules dictate we can't use these as clues)
    board_set = set([word for category in st.session_state.board.values() for word in category])
    
    top_clues = []

    # Search the top 5,000 most common words in our AI's vocabulary
    vocab_subset = model.index_to_key[:5000]

    with st.spinner("AI is calculating vector distances..."):
        for potential_clue in vocab_subset:
            # Rule: Clue cannot be on the board or a direct substring of a board word
            if potential_clue in board_set or any(potential_clue in w or w in potential_clue for w in board_set):
                continue
            
            # 1. Calculate REWARD (Similarity to our team's words)
            target_sims = sorted([model.similarity(potential_clue, t) for t in targets], reverse=True)
            # We average the similarity of the top N words we are trying to connect
            reward = np.mean(target_sims[:max_words_to_connect])
            
            # 2. Calculate PENALTY (Similarity to enemy/neutral words)
            penalty = max([model.similarity(potential_clue, bw) for bw in bad_words])
            
            # 3. Calculate RISK (Similarity to the Assassin word)
            death_risk = model.similarity(potential_clue, assassin)
            
            # 4. STRATEGY FORMULA
            # Score = Reward - Penalty - (Risk Aversion * Death Risk)
            score = reward - (0.5 * penalty) - (risk_aversion * death_risk)
            
            # Save the clue and its score
            top_clues.append((score, potential_clue))

    # Sort all valid clues by their strategy score in descending order
    top_clues.sort(key=lambda x: x[0], reverse=True)
    
    # Pick a random clue from the top 10 to ensure variety while keeping quality high
    pool_size = min(10, len(top_clues))
    if pool_size > 0:
        best_score, best_clue = random.choice(top_clues[:pool_size])
        
        # Find which target words this clue connects to best
        connected = [t for t in targets if model.similarity(best_clue, t) > 0.4]
        best_connections = connected[:max_words_to_connect]
        
        return best_clue, best_score, best_connections
        
    return None, 0, []


# --- 5. THE USER INTERFACE ---
col1, col2 = st.columns([1, 3])

with col1:
    st.header("⚙️ Spymaster Controls")
    target_team = st.selectbox("You are playing as:", ["Red Team", "Blue Team"])
    
    st.markdown("### AI Strategy Parameters")
    risk_aversion = st.slider("Risk Aversion (Alpha)", min_value=0.5, max_value=5.0, value=2.0, step=0.5, 
                              help="Higher values make the AI terrified of the Assassin word.")
    words_to_connect = st.slider("Target Words to Connect", min_value=1, max_value=3, value=2,
                                 help="How greedy the AI is. Connecting 3 words is harder and riskier.")
    
    if st.button("Generate Clue ✨", use_container_width=True, type="primary"):
        clue, score, connections = generate_clue(target_team, risk_aversion, words_to_connect)
        st.success(f"**Best Clue:** {clue.upper()}")
        st.info(f"**Intended Targets:** {', '.join(connections)}")
        st.caption(f"Strategy Score: {score:.3f}")

    if st.button("Shuffle Board 🔄", use_container_width=True):
        generate_board()
        st.rerun()

with col2:
    st.header("🗺️ The Game Board")
    
    # Display the board beautifully
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    
    with b_col1:
        st.error(f"🔴 Red Team ({len(st.session_state.board['Red Team'])})")
        for w in st.session_state.board['Red Team']: st.write(f"- {w.capitalize()}")
            
    with b_col2:
        st.info(f"🔵 Blue Team ({len(st.session_state.board['Blue Team'])})")
        for w in st.session_state.board['Blue Team']: st.write(f"- {w.capitalize()}")
            
    with b_col3:
        st.warning(f"⚪ Neutrals ({len(st.session_state.board['Neutral'])})")
        for w in st.session_state.board['Neutral']: st.write(f"- {w.capitalize()}")
            
    with b_col4:
        st.header("💀 ASSASSIN")
        st.subheader(f"**{st.session_state.board['Assassin'][0].upper()}**")