import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aurachat_v2_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- HTML EMBUTIDO ---

HTML_REGISTER = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>AuraChat V2 - Cadastro</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #1e1e1e; padding: 30px; border-radius: 10px; width: 300px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        input { width: 90%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #333; background: #2b2b2b; color: #fff; }
        button { width: 98%; padding: 10px; background: #2e7d32; color: #fff; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background: #1b5e20; }
        a { color: #81c784; text-decoration: none; }
        .flash { color: #ff5252; margin-bottom: 10px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Criar Conta</h2>
        {% with messages = get_flashed_messages() %}
          {% if messages %}<p class="flash">{{ messages[0] }}</p>{% endif %}
        {% endwith %}
        <form method="POST">
            <input type="text" name="username" placeholder="Usuário" required><br>
            <input type="password" name="password" placeholder="Senha" required><br>
            <button type="submit">Cadastrar</button>
        </form>
        <p>Já possui conta? <a href="/login">Fazer Login</a></p>
    </div>
</body>
</html>
'''

HTML_LOGIN = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>AuraChat V2 - Login</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #1e1e1e; padding: 30px; border-radius: 10px; width: 300px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        input { width: 90%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #333; background: #2b2b2b; color: #fff; }
        button { width: 98%; padding: 10px; background: #1976d2; color: #fff; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background: #1565c0; }
        a { color: #64b5f6; text-decoration: none; }
        .flash { color: #ff5252; margin-bottom: 10px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="box">
        <h2>AuraChat V2</h2>
        {% with messages = get_flashed_messages() %}
          {% if messages %}<p class="flash">{{ messages[0] }}</p>{% endif %}
        {% endwith %}
        <form method="POST">
            <input type="text" name="username" placeholder="Usuário" required><br>
            <input type="password" name="password" placeholder="Senha" required><br>
            <button type="submit">Entrar</button>
        </form>
        <p>Não tem conta? <a href="/register">Cadastre-se</a></p>
    </div>
</body>
</html>
'''

HTML_ROOM = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>AuraChat V2 - Sala de Áudio</title>
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #fff; text-align: center; padding: 40px; }
        .container { max-width: 450px; margin: 0 auto; background: #1e1e1e; padding: 25px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
        .btn-muta { padding: 12px 24px; background: #d32f2f; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 15px; }
        .btn-muta.muted { background: #388e3c; }
        .btn-logout { display: inline-block; margin-top: 25px; color: #888; text-decoration: none; font-size: 14px; }
        ul { list-style: none; padding: 0; margin-top: 20px; }
        li { background: #2a2a2a; padding: 12px; margin: 8px 0; border-radius: 6px; text-align: left; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🎙️ Sala de Áudio V2</h2>
        <p>Conectado como: <strong>{{ username }}</strong></p>
        
        <button id="mute-btn" class="btn-muta" onclick="toggleMute()">Mutar Microfone</button>
        
        <h3>Participantes Online</h3>
        <ul id="user-list">
            <li>🟢 Você ({{ username }})</li>
        </ul>

        <a href="/logout" class="btn-logout">Sair</a>
    </div>

    <div id="audio-containers"></div>

    <script>
        const socket = io();
        const peers = {};
        let localStream;
        let isMuted = false;

        const config = {
            iceServers: [{ urls: 'stun:stun.l.google.com:19020' }]
        };

        navigator.mediaDevices.getUserMedia({ audio: true, video: false })
            .then(stream => {
                localStream = stream;
                socket.emit('join');
            })
            .catch(err => alert("Acesso ao microfone é necessário para participar da chamada."));

        socket.on('user-connected', data => {
            createPeerConnection(data.sid, true);
            addUserToList(data.sid, data.username);
        });

        socket.on('signal', async data => {
            if (!peers[data.from]) {
                createPeerConnection(data.from, false);
            }
            const pc = peers[data.from];
            
            if (data.signal.sdp) {
                await pc.setRemoteDescription(new RTCSessionDescription(data.signal.sdp));
                if (data.signal.sdp.type === 'offer') {
                    const answer = await pc.createAnswer();
                    await pc.setLocalDescription(answer);
                    socket.emit('signal', { to: data.from, signal: { sdp: pc.localDescription } });
                }
            } else if (data.signal.candidate) {
                await pc.addIceCandidate(new RTCIceCandidate(data.signal.candidate));
            }
        });

        socket.on('user-disconnected', sid => {
            if (peers[sid]) {
                peers[sid].close();
                delete peers[sid];
            }
            const el = document.getElementById(`user-${sid}`);
            if (el) el.remove();
            const audioEl = document.getElementById(`audio-${sid}`);
            if (audioEl) audioEl.remove();
        });

        function createPeerConnection(sid, isInitiator) {
            const pc = new RTCPeerConnection(config);
            peers[sid] = pc;

            localStream.getTracks().forEach(track => pc.addTrack(track, localStream));

            pc.onicecandidate = event => {
                if (event.candidate) {
                    socket.emit('signal', { to: sid, signal: { candidate: event.candidate } });
                }
            };

            pc.ontrack = event => {
                let audioEl = document.getElementById(`audio-${sid}`);
                if (!audioEl) {
                    audioEl = document.createElement('audio');
                    audioEl.id = `audio-${sid}`;
                    audioEl.autoplay = true;
                    document.getElementById('audio-containers').appendChild(audioEl);
                }
                audioEl.srcObject = event.streams[0];
            };

            if (isInitiator) {
                pc.createOffer().then(offer => {
                    return pc.setLocalDescription(offer);
                }).then(() => {
                    socket.emit('signal', { to: sid, signal: { sdp: pc.localDescription } });
                });
            }
        }

        function addUserToList(sid, username) {
            const list = document.getElementById('user-list');
            const li = document.createElement('li');
            li.id = `user-${sid}`;
            li.innerText = `🟢 ${username}`;
            list.appendChild(li);
        }

        function toggleMute() {
            if (localStream) {
                isMuted = !isMuted;
                localStream.getAudioTracks()[0].enabled = !isMuted;
                const btn = document.getElementById('mute-btn');
                btn.innerText = isMuted ? "Desmutar Microfone" : "Mutar Microfone";
                btn.classList.toggle('muted', isMuted);
            }
        }
    </script>
</body>
</html>
'''

# --- ROTAS ---

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('room'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if not username or not password:
            flash('Preencha todos os campos.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            conn.close()
            flash('Cadastro realizado com sucesso!')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Nome de usuário já cadastrado.')
            return redirect(url_for('register'))

    return render_template_string(HTML_REGISTER)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            return redirect(url_for('room'))
        else:
            flash('Usuário ou senha inválidos.')

    return render_template_string(HTML_LOGIN)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/room')
def room():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template_string(HTML_ROOM, username=session['username'])

# --- SINALIZAÇÃO WEBRTC ---

ROOM_ID = "sala_principal"

@socketio.on('join')
def handle_join():
    username = session.get('username')
    if username:
        join_room(ROOM_ID)
        emit('user-connected', {'sid': request.sid, 'username': username}, to=ROOM_ID, include_self=False)

@socketio.on('signal')
def handle_signal(data):
    target_sid = data.get('to')
    emit('signal', {
        'from': request.sid,
        'signal': data.get('signal')
    }, to=target_sid)

@socketio.on('disconnect')
def handle_disconnect():
    leave_room(ROOM_ID)
    emit('user-disconnected', request.sid, to=ROOM_ID)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
