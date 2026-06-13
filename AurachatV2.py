import os
import random
from flask import Flask, render_template_string, request, jsonify, Response
import logging

app = Flask(__name__)
chat_history = []
salas_estado = {}

# Silencia logs padrão do Flask para manter o terminal limpo
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraChat</title>
    
    <meta name="google-site-verification" content="zQLtjHr1rPkPOerwm5y02Vabgk5uak_3kbT4iELGXSA" />
    
    <meta name="description" content="AuraChat é uma plataforma de conversas seguras, salas privadas em tempo real e chamadas de vídeo automáticas.">
    <meta name="keywords" content="AuraChat, chat privado, conversas seguras, video chamadas, chat online">
    
    <style>
        :root {
            --bg: #0b0c10; --card: #1a1b21; --text: #f1f1f1;
            --pink: #f34a74; --input-bg: #2a2c33; --green: #00a884;
            --sub-text: #888;
        }
        
        /* Temas Dinâmicos */
        body.tema-dark { background: var(--bg); color: var(--text); }
        
        body.tema-light {
            --bg: #f4f4f5; --card: #ffffff; --text: #18181b;
            --input-bg: #e4e4e7; --sub-text: #71717a;
        }
        body.tema-light .bubble.others { background: #e4e4e7; color: #18181b; }
        body.tema-light .bubble.mine { background: #d4d4d8; color: #18181b; }
        body.tema-light input { color: #18181b; }
        
        body.tema-cyberpunk {
            --bg: #2e0854; --card: #4a0e4e; --text: #00ffcc;
            --input-bg: #1a0033; --sub-text: #ff007f; --pink: #ff007f;
        }
        body.tema-cyberpunk .bubble.others { background: #1a0033; border: 1px solid #ff007f; }
        body.tema-cyberpunk .bubble.mine { background: #4a0e4e; border: 1px solid #00ffcc; }

        body { 
            font-family: sans-serif; margin: 0; display: flex; justify-content: center; 
            align-items: center; height: 100vh; overflow: hidden;
            background-image: radial-gradient(circle, rgba(128,128,128,0.1) 1px, transparent 1px); background-size: 30px 30px;
        }
        .screen { display: none; width: 100%; max-width: 400px; flex-direction: column; gap: 15px; padding: 20px; box-sizing: border-box; }
        .active { display: flex; }
        .card { background: var(--card); border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); padding: 30px; text-align: center; }
        input, select { background: var(--input-bg); color: white; border: none; padding: 14px; border-radius: 12px; width: 100%; box-sizing: border-box; outline: none; margin-bottom: 10px; font-family: sans-serif; }
        button { border-radius: 12px; border: none; font-weight: 600; cursor: pointer; transition: 0.2s; font-size: 14px; padding: 14px; }
        .btn-white { background: white; color: black; width: 100%; }
        
        #chat-screen { max-width: none; height: 100vh; padding: 0; width: 100%; background: rgba(0,0,0,0.15); }
        .chat-header { padding: 15px; font-size: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(128,128,128,0.1); background: var(--card); }
        #messages-flow { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
        
        /* Layout de Balão Modificado: Nick em cima pequeno, mensagem embaixo normal */
        .msg-container { display: flex; flex-direction: column; max-width: 75%; }
        .msg-container.mine { align-self: flex-end; }
        .msg-container.others { align-self: flex-start; }
        
        .msg-nick { font-size: 10px; font-weight: bold; margin-bottom: 2px; color: var(--pink); text-transform: uppercase; letter-spacing: 0.5px; }
        .msg-container.mine .msg-nick { text-align: right; color: var(--green); }

        .bubble { padding: 10px 14px; border-radius: 14px; font-size: 14px; word-break: break-all; }
        .mine .bubble { background: #4a4760; border-top-right-radius: 4px; }
        .others .bubble { background: #2a2c33; border-top-left-radius: 4px; }

        #call-ui { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #000; z-index: 1000; display: none; flex-direction: column; }
        .video-box { flex: 1; position: relative; display: flex; align-items: center; justify-content: center; }
        video { width: 100%; height: 100%; object-fit: cover; }
        #local-v { width: 100px; height: 130px; position: absolute; bottom: 20px; right: 20px; border-radius: 10px; border: 2px solid var(--pink); }
        .controls { height: 80px; background: rgba(0,0,0,0.9); display: flex; justify-content: center; align-items: center; }
        
        /* Painel Lateral de Configurações */
        #config-menu { position: fixed; top: 0; right: 0; bottom: 0; width: 280px; background: var(--card); padding: 20px; border-left: 1px solid rgba(128,128,128,0.2); display: none; z-index: 500; box-shadow: -5px 0 15px rgba(0,0,0,0.3); overflow-y: auto; }
        .adm-tag { color: var(--pink); border: 1px solid var(--pink); font-size: 9px; padding: 2px 5px; border-radius: 4px; margin-left: 5px; font-weight: bold; }
        .cfg-label { font-size: 10px; text-transform: uppercase; font-weight: bold; color: var(--sub-text); display: block; margin-top: 15px; margin-bottom: 5px; }
        .membro-row { display: flex; justify-content: space-between; align-items: center; font-size: 12px; padding: 6px 0; border-bottom: 1px solid #222; }
    </style>
</head>
<body class="tema-dark">

<div id="call-ui">
    <div class="video-box">
        <video id="remote-v" autoplay playsinline></video>
        <video id="local-v" autoplay muted playsinline></video>
    </div>
    <div class="controls">
        <button onclick="endCall()" style="background:var(--pink); color:white; width:60px; height:60px; border-radius:50%">✖</button>
    </div>
</div>

<div id="app" style="width: 100%;">
    <div id="login-screen" class="screen active">
        <div class="card">
            <h1>Welcome to AuraChat</h1>
            <input type="text" id="userInput" placeholder="Enter your name" onkeypress="if(event.key==='Enter') autenticar()">
            <button class="btn-white" onclick="autenticar()">Continue</button>
        </div>
    </div>

    <div id="menu-screen" class="screen">
        <div class="card" style="background:transparent; border:none">
            <h1>Aura<span style="color:var(--pink)">Chat</span></h1>
            <input type="text" id="groupInput" placeholder="Enter code..." onkeypress="if(event.key==='Enter') joinChat()">
            <button class="btn-white" onclick="joinChat()" style="margin-bottom:10px">Join Chat</button>
            <button class="btn-white" onclick="createChat()" style="background:transparent; color:white; border:1px solid white">🛡️ Start new private chat</button>
        </div>
    </div>

    <div id="chat-screen" class="screen">
        <div class="chat-header">
            <div style="width: 80px;" id="count-display">📶 0 online</div>
            <div>🔒 <span id="display-g"></span> <span id="adm-badge"></span></div>
            <div style="width: 80px; text-align: right; display:flex; gap:12px; justify-content:flex-end">
                <span style="cursor:pointer; font-size:14px;" onclick="startCall()">📞</span>
                <span style="cursor:pointer; font-size:14px;" onclick="toggleCfg()">⚙️</span>
            </div>
        </div>

        <div id="config-menu">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <h3 style="margin:0; font-size:16px;">Menu</h3>
                <span onclick="toggleCfg()" style="cursor:pointer; font-size:18px;">✕</span>
            </div>
            
            <span class="cfg-label">Change Name</span>
            <div style="display:flex; gap:5px;">
                <input type="text" id="newNameInput" style="margin:0; padding:10px;">
                <button onclick="alterarNome()" style="padding:10px; background:white; color:black;">Save</button>
            </div>

            <span class="cfg-label">Interface Theme</span>
            <select id="themeSelector" onchange="mudarTema(this.value)">
                <option value="tema-dark">Escuro Padrão</option>
                <option value="tema-light">Claro Minimalista</option>
                <option value="tema-cyberpunk">Cyberpunk Neon</option>
            </select>

            <div id="adm-panel" style="display:none; margin-top:20px; border-top: 1px solid rgba(128,128,128,0.2); padding-top: 10px;">
                <span class="cfg-label" style="color:var(--pink)">Group Management (ADM)</span>
                <div id="membros-lista-box" style="margin-top:10px;"></div>
            </div>

            <button onclick="location.href='/'" style="background:var(--pink); color:white; width:100%; margin-top:30px;">Exit Group</button>
        </div>

        <div id="messages-flow"></div>
        <div style="padding:10px; display:flex; gap:10px; background:#15161a; margin:10px; border-radius:30px">
            <input type="text" id="msgInput" placeholder="Type your reply..." style="margin:0; background:transparent" onkeypress="if(event.key==='Enter') send()">
            <button onclick="send()" style="background:white; color:black; width:40px; height:40px; border-radius:50%; padding:0">➔</button>
        </div>
    </div>
</div>

<script>
    let u="", g="", last=0, stream=null;
    
    const urlParams = window.location.pathname.split('/');
    const roomFromUrl = urlParams.length === 3 && urlParams[1] === 'chat' ? urlParams[2] : null;

    function autenticar() { 
        u = document.getElementById('userInput').value.trim(); 
        if(!u) {
            alert("Por favor, digite seu nome primeiro!");
            return;
        }
        
        if (roomFromUrl) {
            g = roomFromUrl;
            start();
        } else {
            show('menu-screen');
        }
    }
    
    function joinChat() { 
        let code = document.getElementById('groupInput').value.trim(); 
        if(code) {
            g = code;
            start();
        }
    }
    
    function createChat() { 
        g = Math.random().toString(36).substr(2,6); 
        start();
    }

    function start() {
        show('chat-screen');
        document.getElementById('display-g').innerText = g;
        document.getElementById('newNameInput').value = u;
        
        window.history.pushState({}, '', '/chat/' + g);

        fetch('/join_room', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user: u, group: g})
        });
        setInterval(sync, 1000);
    }

    function show(id) {
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        document.getElementById(id).classList.add('active');
    }

    async function send(type="text") {
        const i = document.getElementById('msgInput');
        const val = (type === "call") ? "📲 Chamada de vídeo iniciada" : i.value;
        if(!val && type !== "call") return;
        await fetch('/receive', { 
            method: 'POST', 
            headers: {'Content-Type': 'application/json'}, 
            body: JSON.stringify({user:u, group:g, msg:val, type:type, ts:Date.now()}) 
        });
        i.value='';
    }

    async function alterarNome() {
        let novo = document.getElementById('newNameInput').value.trim();
        if(novo && novo !== u) {
            await fetch('/change_name', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({group: g, old_user: u, new_user: novo})
            });
            u = novo;
            alert("Nome updated!");
        }
    }

    function mudarTema(tema) {
        document.body.className = tema;
    }

    async function expulsar(alvo) {
        await fetch('/kick', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({group: g, user: alvo})
        });
    }

    async function bloquear(alvo) {
        await fetch('/ban', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({group: g, user: alvo})
        });
    }

    async function startCall() {
        send("call");
        document.getElementById('call-ui').style.display='flex';
        stream = await navigator.mediaDevices.getUserMedia({video:true, audio:true});
        document.getElementById('local-v').srcObject = stream;
        document.getElementById('remote-v').srcObject = stream;
    }

    function endCall() {
        if(stream) stream.getTracks().forEach(t => t.stop());
        document.getElementById('call-ui').style.display='none';
    }

    function toggleCfg() {
        const m = document.getElementById('config-menu');
        m.style.display = (m.style.display === 'block') ? 'none' : 'block';
    }

    async function sync() {
        const metaRes = await fetch(`/room_info?group=${g}&user=${u}`);
        const meta = await metaRes.json();
        
        if (meta.kicked_or_banned) {
            alert("Você foi removido ou bloqueado deste grupo.");
            location.href = '/';
            return;
        }

        document.getElementById('count-display').innerText = `📶 ${meta.qtd} online`;

        if(meta.adm === u) {
            document.getElementById('adm-badge').innerHTML = '<span class="adm-tag">ADM</span>';
            document.getElementById('adm-panel').style.display = 'block';
            
            const listContainer = document.getElementById('membros-lista-box');
            listContainer.innerHTML = '';
            meta.membros.forEach(m => {
                if(m !== u) {
                    const row = document.createElement('div');
                    row.className = 'membro-row';
                    row.innerHTML = `
                        <span>${m}</span>
                        <div>
                            <span onclick="expulsar('${m}')" style="color:orange; cursor:pointer; margin-right:8px;">Excluir</span>
                            <span onclick="bloquear('${m}')" style="color:var(--pink); cursor:pointer;">Bloquear</span>
                        </div>
                    `;
                    listContainer.appendChild(row);
                }
            });
        } else {
            document.getElementById('adm-badge').innerHTML = '';
            document.getElementById('adm-panel').style.display = 'none';
        }

        const r = await fetch('/messages');
        const data = await r.json();
        const filtered = data.filter(m => m.group === g);

        if(filtered.length > last) {
            const flow = document.getElementById('messages-flow');
            for(let i=last; i<filtered.length; i++) {
                const m = filtered[i];
                const container = document.createElement('div');
                
                if(m.type === "call") {
                    container.className = "msg-container others";
                    container.innerHTML = `
                        <span class="msg-nick">${m.user}</span>
                        <div class="bubble" style="background:var(--green)">
                            iniciou vídeo.<br>
                            <button onclick="startCall()" style="background:white; color:black; margin-top:5px; padding:3px 10px; font-size:10px; border-radius:6px;">ENTRAR</button>
                        </div>`;
                } else {
                    const isMine = m.user === u;
                    container.className = `msg-container ${isMine ? 'mine' : 'others'}`;
                    container.innerHTML = `
                        <span class="msg-nick">${isMine ? 'you' : m.user}</span>
                        <div class="bubble">
                            ${m.msg}
                        </div>
                    `;
                }
                flow.appendChild(container);
            }
            last = filtered.length;
            flow.scrollTop = flow.scrollHeight;
        }
    }
</script>
</body>
</html>
"""

@app.route('/')
@app.route('/chat/<room_code>')
def home(room_code=None):
    return render_template_string(HTML_TEMPLATE)

@app.route('/robots.txt')
def robots():
    """Garante que os robôs do Google leiam o arquivo perfeitamente como texto puro"""
    content = "User-agent: *\nAllow: /\n"
    return Response(content, mimetype='text/plain')

@app.route('/receive', methods=['POST'])
def receive():
    chat_history.append(request.json)
    return jsonify({"status": "ok"})

@app.route('/messages')
def messages(): 
    return jsonify(chat_history)

@app.route('/join_room', methods=['POST'])
def join_room_route():
    data = request.json
    g = data.get('group')
    u = data.get('user')
    if g and u:
        if g not in salas_estado:
            salas_estado[g] = {'adm': u, 'membros': set(), 'banidos': set()}
        if u not in salas_estado[g]['banidos']:
            salas_estado[g]['membros'].add(u)
    return jsonify({"status": "ok"})

@app.route('/room_info')
def room_info():
    g = request.args.get('group')
    u = request.args.get('user')
    if g in salas_estado:
        if u not in salas_estado[g]['membros'] or u in salas_estado[g]['banidos']:
            return jsonify({"kicked_or_banned": True})
            
        return jsonify({
            "kicked_or_banned": False,
            "qtd": len(salas_estado[g]['membros']),
            "adm": salas_estado[g]['adm'],
            "membros": list(salas_estado[g]['membros'])
        })
    return jsonify({"kicked_or_banned": False, "qtd": 1, "adm": u, "membros": [u]})

@app.route('/change_name', methods=['POST'])
def change_name():
    data = request.json
    g = data.get('group')
    old = data.get('old_user')
    new = data.get('new_user')
    if g in salas_estado:
        if old in salas_estado[g]['membros']:
            salas_estado[g]['membros'].remove(old)
            salas_estado[g]['membros'].add(new)
        if salas_estado[g]['adm'] == old:
            salas_estado[g]['adm'] = new
        for msg in chat_history:
            if msg['group'] == g and msg['user'] == old:
                msg['user'] = new
    return jsonify({"status": "ok"})

@app.route('/kick', methods=['POST'])
def kick_user():
    data = request.json
    g = data.get('group')
    target = data.get('user')
    if g in salas_estado and target in salas_estado[g]['membros']:
        salas_estado[g]['membros'].remove(target)
    return jsonify({"status": "ok"})

@app.route('/ban', methods=['POST'])
def ban_user():
    data = request.json
    g = data.get('group')
    target = data.get('user')
    if g in salas_estado:
        if target in salas_estado[g]['membros']:
            salas_estado[g]['membros'].remove(target)
        salas_estado[g]['banidos'].add(target)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
