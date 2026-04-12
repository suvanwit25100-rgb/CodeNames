/**
 * SPYWORDS — Game Client (UX Enhanced + Sound)
 * ═════════════════════════════════════════════════════
 * Toast notifications, 3D card flips, confetti, sound FX,
 * dramatic clue pop-out, keyboard shortcuts, progress bars.
 */

/* ═══════════════════════════════════════
   SOUND ENGINE — Web Audio API Synthesizer
   No external audio files needed!
   ═══════════════════════════════════════ */
class SoundEngine {
    constructor() {
        this.ctx = null;
        this.enabled = true;
        this.volume = 0.3;
    }

    // Lazy-init AudioContext (browsers require user gesture)
    getCtx() {
        if (!this.ctx) {
            this.ctx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (this.ctx.state === 'suspended') this.ctx.resume();
        return this.ctx;
    }

    // ── Core oscillator helper ──
    playTone(freq, duration, type = 'sine', vol = this.volume, delay = 0) {
        if (!this.enabled) return;
        const ctx = this.getCtx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = type;
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(0, ctx.currentTime + delay);
        gain.gain.linearRampToValueAtTime(vol, ctx.currentTime + delay + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + delay + duration);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(ctx.currentTime + delay);
        osc.stop(ctx.currentTime + delay + duration);
    }

    // ── Noise burst (for whoosh/click) ──
    playNoise(duration, vol = 0.08, delay = 0) {
        if (!this.enabled) return;
        const ctx = this.getCtx();
        const bufferSize = ctx.sampleRate * duration;
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) data[i] = Math.random() * 2 - 1;
        const source = ctx.createBufferSource();
        source.buffer = buffer;
        const gain = ctx.createGain();
        const filter = ctx.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.value = 1200;
        filter.Q.value = 0.5;
        gain.gain.setValueAtTime(vol, ctx.currentTime + delay);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + delay + duration);
        source.connect(filter);
        filter.connect(gain);
        gain.connect(ctx.destination);
        source.start(ctx.currentTime + delay);
    }

    // ═══════════════════════════
    // GAME SOUND EFFECTS
    // ═══════════════════════════

    // Card flip: short whoosh
    cardFlip() {
        this.playNoise(0.15, 0.12);
        this.playTone(300, 0.08, 'sine', 0.06);
        this.playTone(600, 0.06, 'sine', 0.04, 0.04);
    }

    // Correct guess: pleasant ascending chime
    correct() {
        this.playTone(523, 0.12, 'sine', 0.2);      // C5
        this.playTone(659, 0.12, 'sine', 0.18, 0.1); // E5
        this.playTone(784, 0.2, 'sine', 0.2, 0.2);   // G5
    }

    // Wrong guess: descending low tones
    wrong() {
        this.playTone(350, 0.2, 'square', 0.1);
        this.playTone(280, 0.3, 'square', 0.08, 0.15);
    }

    // Assassin hit: dramatic low rumble
    assassin() {
        this.playTone(80, 0.6, 'sawtooth', 0.15);
        this.playTone(60, 0.8, 'square', 0.1, 0.1);
        this.playNoise(0.5, 0.15, 0.05);
        this.playTone(100, 0.3, 'sawtooth', 0.12, 0.3);
    }

    // Clue reveal: notification ding
    clueReveal() {
        this.playTone(880, 0.08, 'sine', 0.15);       // A5
        this.playTone(1108, 0.08, 'sine', 0.12, 0.08); // C#6
        this.playTone(1318, 0.15, 'sine', 0.18, 0.16); // E6
        this.playTone(1760, 0.25, 'sine', 0.12, 0.24); // A6
    }

    // Button click: subtle tap
    click() {
        this.playTone(800, 0.04, 'sine', 0.06);
        this.playNoise(0.03, 0.05);
    }

    // Turn switch: soft transition
    turnSwitch() {
        this.playTone(440, 0.08, 'sine', 0.08);
        this.playTone(554, 0.12, 'sine', 0.06, 0.06);
    }

    // Game win: triumphant fanfare
    win() {
        this.playTone(523, 0.15, 'sine', 0.2);       // C5
        this.playTone(659, 0.15, 'sine', 0.2, 0.15);  // E5
        this.playTone(784, 0.15, 'sine', 0.2, 0.3);   // G5
        this.playTone(1047, 0.4, 'sine', 0.25, 0.45);  // C6
        this.playTone(784, 0.12, 'sine', 0.12, 0.55);  // G5
        this.playTone(1047, 0.5, 'sine', 0.25, 0.65);  // C6
    }

    // New game: shuffling cards
    newGame() {
        for (let i = 0; i < 5; i++) {
            this.playNoise(0.04, 0.06, i * 0.05);
            this.playTone(200 + i * 60, 0.04, 'sine', 0.04, i * 0.05);
        }
    }

    // Pass turn
    pass() {
        this.playTone(500, 0.06, 'sine', 0.08);
        this.playTone(400, 0.1, 'sine', 0.06, 0.05);
    }
}


/* ═══════════════════════════════════════
   GAME IMAGES
   ═══════════════════════════════════════ */
const CHARACTER_IMAGES = [
    '/static/img/spy_card_1.png',
    '/static/img/spy_card_2.png',
    '/static/img/spy_card_3.png',
    '/static/img/spy_card_4.png',
    '/static/img/spy_card_5.png',
    '/static/img/spy_card_6.png',
];


/* ═══════════════════════════════════════
   MAIN GAME CLASS
   ═══════════════════════════════════════ */
class SemanticSaboteur {
    constructor() {
        this.state = null;
        this.spymasterView = false;
        this.charts = {};
        this.cardImageMap = {};
        this.previousClue = null;
        this.guessing = false;
        this.sound = new SoundEngine();
        this.init();
    }

    async init() {
        this.bindKeyboard();
        await this.newGame();
    }

    // ─── KEYBOARD SHORTCUTS ───
    bindKeyboard() {
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && !e.repeat) {
                e.preventDefault();
                const btn = document.getElementById('get-clue-btn');
                if (!btn.disabled) this.getClue();
            }
            if (e.code === 'Escape') {
                const analysis = document.getElementById('analysis-overlay');
                if (analysis.classList.contains('open')) {
                    this.closeAnalysis();
                } else {
                    const passBtn = document.getElementById('pass-btn');
                    if (!passBtn.disabled) this.passTurn();
                }
            }
            // M to toggle mute
            if (e.code === 'KeyM' && !e.repeat) {
                this.sound.enabled = !this.sound.enabled;
                this.toast(this.sound.enabled ? '🔊 Sound ON' : '🔇 Sound OFF', 'turn');
            }
        });
    }

    // ─── API ───
    async api(endpoint, method = 'POST', body = null) {
        const opts = { method, headers: { 'Content-Type': 'application/json' } };
        if (body) opts.body = JSON.stringify(body);
        const res = await fetch(endpoint, opts);
        if (!res.ok) return null;
        return res.json();
    }

    // ─── NEW GAME ───
    async newGame() {
        const difficulty = document.getElementById('difficulty-select').value;
        document.getElementById('loading-overlay').classList.add('active');
        this.sound.newGame();
        const data = await this.api('/api/new-game', 'POST', { difficulty });
        if (data) {
            this.state = data;
            this.previousClue = null;
            this.assignCardImages();
            this.renderAll();
            this.hideGameOver();
            this.clearConfetti();
        }
        document.getElementById('loading-overlay').classList.remove('active');
    }

    assignCardImages() {
        this.cardImageMap = {};
        const shuffled = [...CHARACTER_IMAGES].sort(() => Math.random() - 0.5);
        this.state.board.forEach((card, i) => {
            this.cardImageMap[card.word] = shuffled[i % shuffled.length];
        });
    }

    // ─── GET AI CLUE ───
    async getClue() {
        if (!this.state || this.state.game_over) return;
        this.sound.click();
        const btn = document.getElementById('get-clue-btn');
        btn.disabled = true;
        btn.innerHTML = '🧠 THINKING <span class="thinking-spinner"><span></span><span></span><span></span></span>';

        const data = await this.api('/api/generate-clue', 'POST');
        if (data) {
            this.state = data;
            this.renderAll();
            if (data.analysis) this.renderAnalysis(data.analysis);

            // Clue pop-out + sound
            if (data.current_clue && data.current_clue !== this.previousClue) {
                this.previousClue = data.current_clue;

                // Animate clue in action bar
                const clueEl = document.getElementById('clue-word');
                clueEl.classList.remove('animate-in');
                void clueEl.offsetWidth;
                clueEl.classList.add('animate-in');

                // Play clue reveal sound
                this.sound.clueReveal();

                // Show dramatic pop-out
                this.showCluePopout(data.current_clue, data.current_number);
            }
        }
        btn.disabled = false;
        btn.innerHTML = '🧠 GET CLUE <span class="kbd-hint">SPACE</span>';
    }

    // ─── CLUE POP-OUT ───
    showCluePopout(word, number) {
        const popout = document.getElementById('clue-popout');
        const wordEl = document.getElementById('clue-popout-word');
        const numEl = document.getElementById('clue-popout-number');

        wordEl.textContent = word.toUpperCase();
        numEl.textContent = number;

        popout.classList.remove('fade-out');
        popout.classList.add('active');

        // Hold for 1.5s, then fade out
        setTimeout(() => {
            popout.classList.add('fade-out');
            setTimeout(() => {
                popout.classList.remove('active', 'fade-out');
            }, 350);
        }, 1500);
    }

    // ─── GUESS ───
    async guess(word) {
        if (!this.state || this.state.phase !== 'operative' || this.state.game_over || this.guessing) return;
        this.guessing = true;
        this.sound.cardFlip();

        const cardEl = document.querySelector(`.card[data-word="${word}"]`);
        const data = await this.api('/api/guess', 'POST', { word });
        if (!data) { this.guessing = false; return; }

        this.state = data;
        const result = data.result;

        if (cardEl) {
            // 3D flip animation
            cardEl.classList.add('flipping');

            // At midpoint of flip (edge-on), reveal it
            setTimeout(() => {
                cardEl.classList.add('revealed');
                const art = cardEl.querySelector('.card-art');
                if (art) art.style.opacity = '1';
            }, 220);

            setTimeout(() => {
                cardEl.classList.remove('flipping');

                if (result.assassin_hit) {
                    cardEl.classList.add('shake');
                    this.sound.assassin();
                    this.toast('💀 ASSASSIN HIT!', 'assassin');
                    setTimeout(() => this.showGameOver(result.winner, true), 900);
                } else if (result.correct) {
                    this.sound.correct();
                    this.toast(`✓ ${word.toUpperCase()} — Correct!`, 'correct');
                    this.bumpScore(data.result.actual_team);
                    if (result.game_over) {
                        setTimeout(() => this.showGameOver(result.winner, false), 700);
                    }
                } else {
                    cardEl.classList.add('shake');
                    this.sound.wrong();
                    setTimeout(() => cardEl.classList.remove('shake'), 500);
                    const label = result.actual_team === 'neutral' ? 'Neutral' : (result.actual_team === 'assassin' ? 'Assassin' : result.actual_team.toUpperCase());
                    this.toast(`✗ ${word.toUpperCase()} — ${label}`, 'wrong');

                    if (result.game_over) {
                        setTimeout(() => this.showGameOver(result.winner, false), 700);
                    }
                }
            }, 550);
        }

        this.renderScores();
        this.renderClue();
        this.renderTurn();
        this.renderLog();
        this.updateControls();

        setTimeout(() => { this.guessing = false; }, 600);
    }

    // ─── PASS TURN ───
    async passTurn() {
        if (!this.state || this.state.game_over) return;
        this.sound.pass();
        const prevTurn = this.state.current_turn;
        const data = await this.api('/api/pass-turn', 'POST');
        if (data) {
            this.state = data;
            this.renderAll();
            if (data.current_turn !== prevTurn) {
                this.sound.turnSwitch();
                this.toast(`⏭️ ${data.current_turn.toUpperCase()} team's turn`, 'turn');
            }
        }
    }

    // ─── TOGGLES ───
    toggleSpymasterView() {
        this.sound.click();
        this.spymasterView = !this.spymasterView;
        const board = document.getElementById('game-board');
        const btn = document.getElementById('spy-view-btn');
        if (this.spymasterView) {
            board.classList.add('spymaster-view');
            btn.classList.add('active');
            btn.textContent = '👁️ SPY ON';
        } else {
            board.classList.remove('spymaster-view');
            btn.classList.remove('active');
            btn.textContent = '👁️ SPY VIEW';
        }
    }

    openAnalysis() {
        this.sound.click();
        document.getElementById('analysis-overlay').classList.add('open');
    }
    closeAnalysis() {
        document.getElementById('analysis-overlay').classList.remove('open');
    }

    // ═══════════════════════════
    // RENDERING
    // ═══════════════════════════

    renderAll() {
        this.renderBoard();
        this.renderScores();
        this.renderClue();
        this.renderTurn();
        this.renderLog();
        this.updateControls();
        this.updatePanelHighlight();
    }

    renderBoard() {
        const boardEl = document.getElementById('game-board');
        boardEl.innerHTML = '';
        if (this.spymasterView) boardEl.classList.add('spymaster-view');
        else boardEl.classList.remove('spymaster-view');

        boardEl.classList.toggle('operative-phase', this.state.phase === 'operative' && !this.state.game_over);

        this.state.board.forEach((card, i) => {
            const el = document.createElement('div');
            const mirror = i % 2 === 1 ? 'mirrored' : '';
            el.className = `card team-${card.team} ${card.revealed ? 'revealed' : ''} ${mirror}`;
            el.dataset.word = card.word;

            const imgUrl = this.cardImageMap[card.word] || CHARACTER_IMAGES[0];
            el.innerHTML = `
                <div class="card-art" style="background-image: url('${imgUrl}')"></div>
                <div class="card-label">${card.word.toUpperCase()}</div>
            `;

            if (!card.revealed) {
                el.addEventListener('click', () => this.guess(card.word));
            }
            boardEl.appendChild(el);
        });
    }

    renderScores() {
        const redFound = 9 - this.state.red_remaining;
        const blueFound = 8 - this.state.blue_remaining;
        document.getElementById('red-score').textContent = redFound;
        document.getElementById('blue-score').textContent = blueFound;
        document.getElementById('red-progress').style.width = `${(redFound / 9) * 100}%`;
        document.getElementById('blue-progress').style.width = `${(blueFound / 8) * 100}%`;
    }

    bumpScore(team) {
        const el = document.getElementById(team === 'red' ? 'red-score' : 'blue-score');
        el.classList.remove('bump');
        void el.offsetWidth;
        el.classList.add('bump');
        setTimeout(() => el.classList.remove('bump'), 500);
    }

    renderClue() {
        const wordEl = document.getElementById('clue-word');
        const numEl = document.getElementById('clue-num');
        const guessesEl = document.getElementById('guesses-left');

        if (this.state.current_clue) {
            wordEl.textContent = this.state.current_clue.toUpperCase();
            numEl.textContent = this.state.current_number;
            numEl.style.display = 'inline-flex';
            guessesEl.textContent = `${this.state.guesses_remaining} guesses left`;
        } else {
            wordEl.textContent = '—';
            numEl.style.display = 'none';
            guessesEl.textContent = 'Waiting for clue...';
        }
    }

    renderTurn() {
        const badge = document.getElementById('turn-badge');
        const text = document.getElementById('turn-text');
        const banner = document.getElementById('turn-banner');
        badge.classList.remove('red-turn', 'blue-turn');
        banner.classList.remove('red-turn-bar', 'blue-turn-bar');

        if (this.state.game_over) {
            text.textContent = 'GAME OVER';
            const winClass = this.state.winner === 'red' ? 'red-turn' : 'blue-turn';
            badge.classList.add(winClass);
        } else {
            const team = this.state.current_turn.toUpperCase();
            const phase = this.state.phase === 'spymaster' ? 'SPYMASTER' : 'OPERATIVE';
            text.textContent = `${team} — ${phase}`;
            badge.classList.add(`${this.state.current_turn}-turn`);
            banner.classList.add(`${this.state.current_turn}-turn-bar`);
        }
    }

    updatePanelHighlight() {
        const leftPanel = document.getElementById('left-panel');
        const rightPanel = document.getElementById('right-panel');
        leftPanel.classList.remove('active-panel');
        rightPanel.classList.remove('active-panel');

        if (!this.state.game_over) {
            if (this.state.current_turn === 'red') leftPanel.classList.add('active-panel');
            else rightPanel.classList.add('active-panel');
        }
    }

    renderLog() {
        const logEl = document.getElementById('game-log');
        logEl.innerHTML = '';

        if (!this.state.game_log.length) {
            logEl.innerHTML = '<div class="log-empty">Press <strong>SPACE</strong> to begin...</div>';
            return;
        }

        this.state.game_log.forEach(entry => {
            const div = document.createElement('div');
            div.className = `log-entry ${entry.team}-log`;
            let text = '';

            if (entry.type === 'clue') {
                text = `<strong>"${entry.clue}"</strong> for <strong>${entry.number}</strong>`;
            } else if (entry.type === 'guess') {
                const cls = entry.correct ? 'correct' : (entry.result === 'assassin' ? 'assassin-hit' : 'wrong');
                const icon = entry.correct ? '✓' : (entry.result === 'assassin' ? '💀' : '✗');
                text = `<strong>${entry.word.toUpperCase()}</strong> <span class="${cls}">${icon} ${entry.result.toUpperCase()}</span>`;
            } else if (entry.type === 'pass') {
                text = '<em>Passed turn</em>';
            }

            div.innerHTML = `<span class="log-dot ${entry.team}"></span><span class="log-text">${text}</span>`;
            logEl.appendChild(div);
        });
        logEl.scrollTop = logEl.scrollHeight;
    }

    updateControls() {
        const clueBtn = document.getElementById('get-clue-btn');
        const passBtn = document.getElementById('pass-btn');

        if (this.state.game_over) {
            clueBtn.disabled = true;
            passBtn.disabled = true;
        } else if (this.state.phase === 'spymaster') {
            clueBtn.disabled = false;
            passBtn.disabled = true;
        } else {
            clueBtn.disabled = true;
            passBtn.disabled = false;
        }
    }

    // ═══════════════════════════
    // TOAST NOTIFICATIONS
    // ═══════════════════════════

    toast(message, type = 'turn') {
        const container = document.getElementById('toast-container');
        const el = document.createElement('div');
        el.className = `toast toast-${type}`;
        el.innerHTML = message;
        container.appendChild(el);
        setTimeout(() => {
            if (el.parentNode) el.parentNode.removeChild(el);
        }, 2800);
    }

    // ═══════════════════════════
    // CONFETTI
    // ═══════════════════════════

    spawnConfetti(color1, color2) {
        const container = document.getElementById('confetti-container');
        const colors = [color1, color2, '#f4c430', '#fff', color1, color2];
        const count = 80;

        for (let i = 0; i < count; i++) {
            const piece = document.createElement('div');
            piece.className = 'confetti-piece';
            piece.style.left = `${Math.random() * 100}vw`;
            piece.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            piece.style.width = `${6 + Math.random() * 8}px`;
            piece.style.height = `${4 + Math.random() * 6}px`;
            piece.style.animationDuration = `${1.5 + Math.random() * 2}s`;
            piece.style.animationDelay = `${Math.random() * 0.6}s`;
            container.appendChild(piece);
        }
        setTimeout(() => this.clearConfetti(), 5000);
    }

    clearConfetti() {
        document.getElementById('confetti-container').innerHTML = '';
    }

    // ═══════════════════════════
    // AI ANALYSIS
    // ═══════════════════════════

    renderAnalysis(analysis) {
        document.getElementById('ai-explanation').textContent = analysis.explanation;
        this.renderSimilarityChart(analysis);
        this.renderCandidatesChart(analysis);
        this.loadVectorPlot();
    }

    renderSimilarityChart(analysis) {
        const ctx = document.getElementById('similarity-chart');
        if (this.charts.similarity) this.charts.similarity.destroy();

        const entries = Object.entries(analysis.board_similarities)
            .sort((a, b) => b[1].similarity - a[1].similarity);

        const teamColors = {
            red: 'rgba(197,71,61,0.8)', blue: 'rgba(74,123,167,0.8)',
            neutral: 'rgba(180,160,120,0.7)', assassin: 'rgba(255,71,87,0.9)',
        };

        this.charts.similarity = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: entries.map(e => e[0].toUpperCase()),
                datasets: [{
                    label: `Similarity to "${analysis.clue.toUpperCase()}"`,
                    data: entries.map(e => e[1].similarity),
                    backgroundColor: entries.map(e => teamColors[e[1].team] || '#888'),
                    borderRadius: 3, barThickness: 12,
                }],
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#8899aa', font: { size: 9 } } },
                    y: { grid: { display: false }, ticks: { color: '#ddd', font: { family: "'Outfit'", weight: '600', size: 9 } } },
                },
            },
        });
    }

    renderCandidatesChart(analysis) {
        const ctx = document.getElementById('candidates-chart');
        if (this.charts.candidates) this.charts.candidates.destroy();
        if (!analysis.top_candidates?.length) return;

        this.charts.candidates = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: analysis.top_candidates.map(c => c.word.toUpperCase()),
                datasets: [
                    { label: 'Reward', data: analysis.top_candidates.map(c => c.reward), backgroundColor: 'rgba(46,204,113,0.7)', borderRadius: 2 },
                    { label: 'Penalty', data: analysis.top_candidates.map(c => -c.penalty), backgroundColor: 'rgba(197,71,61,0.7)', borderRadius: 2 },
                    { label: 'Risk', data: analysis.top_candidates.map(c => -c.death_risk), backgroundColor: 'rgba(255,71,87,0.5)', borderRadius: 2 },
                ],
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#8899aa', font: { size: 10 }, usePointStyle: true } } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: '#ddd', font: { family: "'Outfit'", weight: '600', size: 10 } } },
                    y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#8899aa', font: { size: 9 } } },
                },
            },
        });
    }

    async loadVectorPlot() {
        const data = await this.api('/api/vector-plot', 'GET');
        if (!data?.points) return;

        const ctx = document.getElementById('vector-chart');
        if (this.charts.vector) this.charts.vector.destroy();

        const colors = { red: 'rgba(197,71,61,0.8)', blue: 'rgba(74,123,167,0.8)', neutral: 'rgba(180,160,120,0.6)', assassin: 'rgba(255,71,87,0.9)', clue: 'rgba(244,196,48,1)' };
        const sizes = { red: 7, blue: 7, neutral: 5, assassin: 10, clue: 14 };

        const datasets = Object.keys(colors).map(team => {
            const pts = data.points.filter(p => p.team === team);
            return {
                label: team.charAt(0).toUpperCase() + team.slice(1),
                data: pts.map(p => ({ x: p.x, y: p.y, label: p.word })),
                backgroundColor: colors[team],
                pointRadius: sizes[team], pointHoverRadius: sizes[team] + 3,
                pointStyle: team === 'clue' ? 'star' : 'circle',
            };
        });

        this.charts.vector = new Chart(ctx, {
            type: 'scatter', data: { datasets },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#8899aa', font: { size: 10 }, usePointStyle: true } },
                    tooltip: { callbacks: { label: ctx => `${ctx.raw.label.toUpperCase()} (${ctx.raw.x.toFixed(2)}, ${ctx.raw.y.toFixed(2)})` } },
                },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { color: '#667', font: { size: 8 } } },
                    y: { grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { color: '#667', font: { size: 8 } } },
                },
            },
        });
    }

    // ═══════════════════════════
    // GAME OVER
    // ═══════════════════════════

    showGameOver(winner, assassinHit) {
        const modal = document.getElementById('game-over-modal');
        const icon = document.getElementById('modal-icon');
        const title = document.getElementById('modal-title');
        const msg = document.getElementById('modal-message');

        const redFound = 9 - this.state.red_remaining;
        const blueFound = 8 - this.state.blue_remaining;
        document.getElementById('fs-red').textContent = redFound;
        document.getElementById('fs-blue').textContent = blueFound;

        if (assassinHit) {
            icon.textContent = '💀';
            title.textContent = 'ASSASSIN!';
            title.style.color = '#ff4757';
            msg.textContent = `${winner.toUpperCase()} team wins — the other team hit the assassin!`;
        } else {
            icon.textContent = '🏆';
            title.textContent = 'MISSION COMPLETE!';
            title.style.color = winner === 'red' ? '#d4574d' : '#5a8bb7';
            msg.textContent = `${winner.toUpperCase()} TEAM wins the game!`;

            const c1 = winner === 'red' ? '#c5473d' : '#4a7ba7';
            const c2 = winner === 'red' ? '#d4574d' : '#5a8bb7';
            this.spawnConfetti(c1, c2);
            this.sound.win();
        }

        this.revealAllCards();
        modal.classList.add('active');
    }

    revealAllCards() {
        document.querySelectorAll('.card:not(.revealed)').forEach(card => {
            card.classList.add('revealed');
            const art = card.querySelector('.card-art');
            if (art) art.style.opacity = '1';
        });
    }

    hideGameOver() {
        document.getElementById('game-over-modal').classList.remove('active');
    }
}

const game = new SemanticSaboteur();
