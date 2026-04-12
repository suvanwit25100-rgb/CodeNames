"""
AI Word Similarity Engine (Self-Contained)
===========================================
A lightweight word-embedding approximation that runs fully offline.
Uses a curated semantic similarity graph + TF-IDF character n-gram features
to compute word relatedness without requiring large model downloads.

This replaces the GloVe dependency for environments without internet access,
while preserving the strategy engine's core behavior.
"""

import numpy as np
from itertools import combinations
import hashlib

# ─────────────────────────────────────────────────────────
# SEMANTIC SIMILARITY GRAPH
# Hand-curated word associations organized by semantic field
# ─────────────────────────────────────────────────────────

SEMANTIC_FIELDS = {
    "nature_plants": ["apple", "leaf", "tree", "flower", "rose", "garden", "plant",
                      "forest", "pine", "palm", "mushroom", "berry", "corn", "seed"],
    "nature_water": ["ocean", "river", "wave", "rain", "flood", "stream", "coral",
                     "harbor", "dock", "port", "anchor", "sailor", "whale", "dolphin",
                     "shark", "fish", "frog", "turtle", "sink", "submarine"],
    "nature_sky": ["cloud", "moon", "sun", "star", "storm", "lightning", "wind",
                   "eagle", "hawk", "owl", "crow", "bird", "flight", "jet", "rocket",
                   "space", "orbit", "launch"],
    "animals_wild": ["bear", "wolf", "lion", "tiger", "fox", "deer", "elephant",
                     "rabbit", "snake", "spider", "dragon", "bull", "stag"],
    "animals_domestic": ["dog", "cat", "horse", "bird", "bug", "worm", "fish"],
    "weapons_combat": ["sword", "blade", "knife", "arrow", "bow", "bullet", "gun",
                       "bomb", "missile", "strike", "war", "soldier", "guard",
                       "shield", "helmet", "armor", "knight", "battle", "fight"],
    "spy_espionage": ["spy", "agent", "code", "cover", "signal", "shadow",
                      "silence", "mask", "thief", "plot", "secret", "mission",
                      "decode", "cipher", "cloak", "disguise"],
    "royalty_power": ["king", "queen", "prince", "crown", "throne", "palace",
                      "castle", "knight", "bishop", "emperor", "royal", "reign",
                      "court", "president", "capital"],
    "food_sweet": ["cake", "candy", "chocolate", "sugar", "honey", "cream",
                   "cherry", "pie", "jam", "vanilla", "peach", "mango"],
    "food_savory": ["bread", "cheese", "steak", "pepper", "salt", "sauce",
                    "egg", "butter", "toast", "potato", "olive", "ginger", "carrot"],
    "food_fruit": ["apple", "cherry", "grape", "lemon", "lime", "orange",
                   "peach", "plum", "berry", "mango", "walnut"],
    "tools_hardware": ["hammer", "nail", "screw", "wrench", "drill", "saw",
                       "bolt", "pipe", "wire", "chain", "hook", "pump",
                       "valve", "plug", "switch", "iron", "steel"],
    "music_art": ["piano", "guitar", "drum", "trumpet", "opera", "dance",
                  "song", "melody", "rhythm", "concert", "theater"],
    "light_fire": ["fire", "flame", "torch", "lamp", "candle", "match",
                   "blaze", "flash", "light", "glow", "ray", "laser", "burn",
                   "heat", "smoke", "ash"],
    "cold_ice": ["ice", "frost", "cold", "snow", "freeze", "winter",
                 "chill", "glacier", "arctic", "polar"],
    "body_human": ["hand", "heart", "eye", "face", "bone", "foot", "head",
                   "arm", "leg", "blood", "soul", "life", "death"],
    "building_structure": ["wall", "bridge", "tower", "dome", "fence", "gate",
                           "barn", "cabin", "church", "temple", "tomb", "vault",
                           "fort", "base", "camp", "jail", "cell", "den", "loft"],
    "transport_vehicle": ["car", "truck", "train", "boat", "ship", "plane",
                          "jet", "rocket", "sled", "wheel", "engine", "track",
                          "pilot", "captain"],
    "container_object": ["box", "bottle", "bucket", "cup", "glass", "plate",
                         "pan", "bowl", "bag", "chest", "barrel", "crate", "jar"],
    "game_play": ["card", "dice", "game", "play", "board", "round", "ace",
                  "score", "win", "bet", "trick", "slot", "club", "deck"],
    "science_tech": ["lab", "lens", "telescope", "screen", "robot", "code",
                     "engine", "laser", "mercury", "gravity", "pulse", "signal",
                     "data", "network"],
    "money_value": ["bank", "coin", "gold", "diamond", "pearl", "medal",
                    "capital", "charge", "contract", "deal", "bond", "scale",
                    "fortune", "ring", "crown"],
    "fabric_cloth": ["thread", "string", "rope", "net", "web", "tape",
                     "belt", "glove", "hat", "boot", "shoe", "vest", "cloak"],
    "time_abstract": ["time", "night", "day", "dawn", "cycle", "spring",
                      "fall", "change", "revolution", "march", "race", "rush"],
    "motion_force": ["force", "gravity", "crash", "blast", "boom", "break",
                     "slip", "slide", "snap", "grip", "press", "push",
                     "pull", "launch", "shot", "hit", "strike", "charge"],
    "document_write": ["paper", "pen", "file", "note", "stamp", "sign",
                       "book", "page", "letter", "draft", "mark", "print",
                       "press", "seal", "contract"],
    "magic_fantasy": ["witch", "dragon", "curse", "charm", "angel", "giant",
                      "pirate", "ghost", "spell", "magic", "dream", "fate",
                      "void", "shadow"],
    "emotion_sense": ["grace", "honor", "heart", "soul", "dream", "love",
                      "fear", "silence", "charm", "touch", "sense"],
    "medical": ["doctor", "nurse", "pill", "needle", "cell", "blood",
                "bone", "heart", "pulse", "check", "lab"],
    "education": ["school", "library", "coach", "judge", "class", "book",
                  "lesson", "student", "teacher", "exam"],
    "place_location": ["field", "park", "yard", "ranch", "mine", "pit",
                       "cave", "den", "gym", "office", "shop", "stadium",
                       "nursery", "mill", "bar"],
}


class WordSimilarityEngine:
    """
    Computes word similarity using:
    1. Semantic field co-occurrence (weighted by field specificity)
    2. Character n-gram overlap (for morphological similarity)
    3. A stable hash-based vector for consistent cosine similarity scores
    """

    def __init__(self):
        self.field_index = {}    # word → set of fields
        self.field_sizes = {}    # field → size
        self.vocab = set()
        self.vectors = {}        # word → numpy vector (for PCA etc.)
        self._build_index()
        self._build_vectors()

    def _build_index(self):
        """Build inverted index: word → which semantic fields it belongs to."""
        for field_name, words in SEMANTIC_FIELDS.items():
            self.field_sizes[field_name] = len(words)
            for word in words:
                self.vocab.add(word)
                if word not in self.field_index:
                    self.field_index[word] = set()
                self.field_index[word].add(field_name)

    def _word_hash_vector(self, word, dim=50):
        """Generate a deterministic pseudo-random vector from a word hash."""
        h = hashlib.sha256(word.encode()).digest()
        rng = np.random.RandomState(int.from_bytes(h[:4], 'big'))
        return rng.randn(dim).astype(np.float32)

    def _build_vectors(self):
        """Build a 50-dimensional vector for each word combining semantic + hash features."""
        all_fields = list(SEMANTIC_FIELDS.keys())

        for word in self.vocab:
            # 30 dims: semantic field membership (weighted by IDF)
            sem_vec = np.zeros(len(all_fields), dtype=np.float32)
            if word in self.field_index:
                for field in self.field_index[word]:
                    idx = all_fields.index(field)
                    # IDF weighting: smaller fields = more specific = higher weight
                    idf = np.log(len(self.vocab) / self.field_sizes[field])
                    sem_vec[idx] = idf

            # Pad or truncate to 30 dims
            if len(sem_vec) > 30:
                sem_vec = sem_vec[:30]
            else:
                sem_vec = np.pad(sem_vec, (0, 30 - len(sem_vec)))

            # 20 dims: hash-based vector for uniqueness
            hash_vec = self._word_hash_vector(word, dim=20)

            self.vectors[word] = np.concatenate([sem_vec * 2.0, hash_vec * 0.5])

            # Normalize
            norm = np.linalg.norm(self.vectors[word])
            if norm > 0:
                self.vectors[word] /= norm

    def similarity(self, word1, word2):
        """
        Compute similarity between two words (0 to 1 scale).
        Combines semantic field overlap + vector cosine similarity.
        """
        if word1 == word2:
            return 1.0

        # Semantic field overlap (Jaccard-like with IDF weighting)
        fields1 = self.field_index.get(word1, set())
        fields2 = self.field_index.get(word2, set())

        if fields1 and fields2:
            shared = fields1 & fields2
            union = fields1 | fields2

            if shared:
                # Weight by IDF (rarer fields = stronger signal)
                weighted_shared = sum(
                    np.log(len(self.vocab) / self.field_sizes[f])
                    for f in shared
                )
                weighted_union = sum(
                    np.log(len(self.vocab) / self.field_sizes[f])
                    for f in union
                )
                field_sim = weighted_shared / weighted_union if weighted_union > 0 else 0
            else:
                field_sim = 0.0
        else:
            field_sim = 0.0

        # Character n-gram similarity (captures morphological relatedness)
        ngram_sim = self._ngram_similarity(word1, word2)

        # Vector cosine similarity
        vec_sim = 0.0
        if word1 in self.vectors and word2 in self.vectors:
            vec_sim = float(np.dot(self.vectors[word1], self.vectors[word2]))
            vec_sim = max(0, vec_sim)  # Clamp negative

        # Weighted combination
        combined = (0.50 * field_sim) + (0.15 * ngram_sim) + (0.35 * vec_sim)
        return min(1.0, max(0.0, combined))

    def _ngram_similarity(self, w1, w2, n=3):
        """Character n-gram Jaccard similarity."""
        def ngrams(word):
            word = f"#{word}#"
            return set(word[i:i+n] for i in range(len(word) - n + 1))

        ng1 = ngrams(w1)
        ng2 = ngrams(w2)

        if not ng1 or not ng2:
            return 0.0
        return len(ng1 & ng2) / len(ng1 | ng2)

    def get_vector(self, word):
        """Get the word's vector (for PCA visualization)."""
        if word in self.vectors:
            return self.vectors[word]
        # Generate a hash vector for unknown words
        return self._word_hash_vector(word, dim=50)

    @property
    def index_to_key(self):
        """Return vocabulary list (for compatibility with gensim-like API)."""
        return list(self.vocab)

    def __contains__(self, word):
        return word in self.vocab
