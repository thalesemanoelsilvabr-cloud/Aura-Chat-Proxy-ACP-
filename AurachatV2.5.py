import os
import random
import logging
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)
chat_history = []
salas_estado = {}

# Silencia logs do Flask para manter o terminal limpo
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraChat v2.5 (Silent)</title>
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
        body.tema-light input, body.tema-light select { color: #18181b; }
        
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
        
        .msg-container { display: flex; flex-direction: column; max-width: 75%; }
        .msg-container.mine { align-self: flex-end; }
        .msg-container.others { align-self: flex-start; }
        
        .msg-nick { font-size: 10px; font-weight: bold; margin-bottom: 2px; color: var(--pink); text-transform: uppercase; letter-spacing: 0.5px; }
        .msg-container.mine .msg-nick { text-align: right; color: var(--green); }

        .bubble { padding: 10px 14px; border-radius: 14px; font-size: 14px; word-break: break-word; }
        .bubble img { max-width: 100%; border-radius: 8px; margin-top: 5px; }
        .mine .bubble { background: #4a4760; border-top-right-radius: 4px; }
        .others .bubble { background: #2a2c33; border-top-left-radius: 4px; }

        /* Media / Overlay UIs */
        #call-ui, #game-ui { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #000; z-index: 1000; display: none; flex-direction: column; }
        .video-box { flex: 1; position: relative; display: flex; align-items: center; justify-content: center; }
        video { width: 100%; height: 100%; object-fit: cover; }
        #local-v { width: 100px; height: 130px; position: absolute; bottom: 20px; right: 20px; border-radius: 10px; border: 2px solid var(--pink); }
        .controls { height: 80px; background: rgba(0,0,0,0.9); display: flex; gap: 15px; justify-content: center; align-items: center; }
        
        #config-menu { position: fixed; top: 0; right: 0; bottom: 0; width: 280px; background: var(--card); padding: 20px; border-left: 1px solid rgba(128,128,128,0.2); display: none; z-index: 500; box-shadow: -5px 0 15px rgba(0,0,0,0.3); overflow-y: auto; }
        .adm-tag { color: var(--pink); border: 1px solid var(--pink); font-size: 9px; padding: 2px 5px; border-radius: 4px; margin-left: 5px; font-weight: bold; }
        .cfg-label { font-size: 10px; text-transform: uppercase; font-weight: bold; color: var(--sub-text); display: block; margin-top: 15px; margin-bottom: 5px; }
        .membro-row { display: flex; justify-content: space-between; align-items: center; font-size: 12px; padding: 6px 0; border-bottom: 1px solid #222; }

        /* Popups / Emojis / Games */
        #emoji-picker { display: none; position: absolute; bottom: 70px; left: 10px; background: var(--card); border: 1px solid #444; border-radius: 12px; padding: 10px; gap: 8px; flex-wrap: wrap; width: 200px; z-index: 100; }
        #emoji-picker span { font-size: 20px; cursor: pointer; }
        #game-canvas { background: #111; flex: 1; width: 100%; height: 100%; }
        .game-overlay-chat { position: absolute; bottom: 10px; left: 10px; width: 280px; background: rgba(0,0,0,0.7); padding: 10px; border-radius: 8px; display: flex; flex-direction: column; gap: 5px; }
        .game-overlay-chat #game-msgs { height: 80px; overflow-y: auto; font-size: 11px; color: #fff; }
    </style>
</head>
<body class="tema-dark">

<div id="call-ui">
    <div class="video-box">
        <video id="remote-v" autoplay playsinline></video>
        <video id="local-v" autoplay muted playsinline></video>
    </div>
    <div class="controls">
        <button id="mic-btn" onclick="toggleMute()" style="background:#4a4760; color:white; width:50px; height:50px; border-radius:50%">🎤</button>
        <button onclick="endCall()" style="background:var(--pink); color:white; width:60px; height:60px; border-radius:50%">✖</button>
    </div>
</div>

<div id="game-ui">
    <div style="height: 40px; background: var(--card); display: flex; justify-content: space-between; align-items: center; padding: 0 15px;">
        <span id="game-title" style="font-weight: bold; font-size: 14px;">Game Zone</span>
        <div>
            <button onclick="startCall('voice')" style="padding: 5px 10px; font-size: 11px; background: var(--green); color: white;">🎙️ Voz</button>
            <button onclick="closeGame()" style="padding: 5px 10px; font-size: 11px; background: var(--pink); color: white;">Sair</button>
        </div>
    </div>
    <div style="flex:1; position:relative;" id="game-container">
        <!-- Canvas do Jogo da Maçã / Iframe para Eaglecraft / G+ -->
    </div>
    <div class="game-overlay-chat" id="game-chat-box" style="display:none;">
        <div id="game-msgs"></div>
        <input type="text" id="gameMsgInput" placeholder="Chat do jogo..." style="margin:0; padding:5px; font-size:11px;" onkeypress="if(event.key==='Enter') sendGameChat()">
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
            <div style="width: 100px; text-align: right; display:flex; gap:10px; justify-content:flex-end; align-items:center;">
                <span style="cursor:pointer; font-size:14px;" onclick="openGamesMenu()" title="Jogos">🎮</span>
                <span style="cursor:pointer; font-size:14px;" onclick="startCall('voice')" title="Voice Chat">🎙️</span>
                <span style="cursor:pointer; font-size:14px;" onclick="startCall('video')" title="Video Call">📹</span>
                <span style="cursor:pointer; font-size:14px;" onclick="toggleCfg()" title="Configurações">⚙️</span>
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

        <!-- Emoji Picker -->
        <div id="emoji-picker">
            <span onclick="addEmoji('😀')">😀</span>
            <span onclick="addEmoji('😂')">😂</span>
            <span onclick="addEmoji('🔥')">🔥</span>
            <span onclick="addEmoji('❤️')">❤️</span>
            <span onclick="addEmoji('👍')">👍</span>
            <span onclick="addEmoji('🎮')">🎮</span>
            <span onclick="addEmoji('🚀')">🚀</span>
            <span onclick="addEmoji('💩')">💩</span>
        </div>

        <div id="messages-flow"></div>

        <div style="padding:10px; display:flex; gap:8px; background:#15161a; margin:10px; border-radius:30px; align-items:center;">
            <span onclick="toggleEmoji()" style="cursor:pointer; font-size:18px; margin-left:8px;">😊</span>
            <label for="imgInput" style="cursor:pointer; font-size:18px;">📷</label>
            <input type="file" id="imgInput" accept="image/*" style="display:none" onchange="uploadFoto(this)">
            
            <input type="text" id="msgInput" placeholder="Type your reply..." style="margin:0; background:transparent" onkeypress="if(event.key==='Enter') send()">
            <button onclick="send()" style="background:white; color:black; width:40px; height:40px; border-radius:50%; padding:0; flex-shrink:0;">➔</button>
        </div>
    </div>
</div>

<script>
    let u="", g="", last=0, stream=null;
    let audioCtx = null;

    const urlParams = window.location.pathname.split('/');
    const roomFromUrl = urlParams.length === 3 && urlParams[1] === 'chat' ? urlParams[2] : null;

    // Toca som sintético de notificação (sem dependência externa)
    function playNotificationSound() {
        try {
            if(!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
            osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.15); // A5
            gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.15);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.15);
        } catch(e){}
    }

    function autenticar() { 
        u = document.getElementById('userInput').value.trim(); 
        if(!u) { alert("Por favor, digite seu nome primeiro!"); return; }
        if (roomFromUrl) { g = roomFromUrl; start(); } else { show('menu-screen'); }
    }
    
    function joinChat() { 
        let code = document.getElementById('groupInput').value.trim(); 
        if(code) { g = code; start(); }
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

    async function send(type="text", customMsg=null) {
        const i = document.getElementById('msgInput');
        let val = customMsg || i.value;
        if(type === "call") val = "📲 Chamada de vídeo iniciada";
        if(type === "voice_call") val = "🎙️ Chamada de voz iniciada";
        if(!val && type === "text") return;

        await fetch('/receive', { 
            method: 'POST', 
            headers: {'Content-Type': 'application/json'}, 
            body: JSON.stringify({user:u, group:g, msg:val, type:type, ts:Date.now()}) 
        });
        if(!customMsg) i.value='';
        document.getElementById('emoji-picker').style.display = 'none';
    }

    function toggleEmoji() {
        const p = document.getElementById('emoji-picker');
        p.style.display = (p.style.display === 'flex') ? 'none' : 'flex';
    }

    function addEmoji(emoji) {
        document.getElementById('msgInput').value += emoji;
    }

    function uploadFoto(input) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                send("image", e.target.result);
            }
            reader.readAsDataURL(input.files[0]);
        }
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
            alert("Nome atualizado!");
        }
    }

    function mudarTema(tema) { document.body.className = tema; }

    async function promoverADM(alvo) {
        await fetch('/add_adm', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({group: g, user: alvo})
        });
    }

    async function rebaixarADM(alvo) {
        await fetch('/remove_adm', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({group: g, user: alvo})
        });
    }

    async function expulsar(alvo) {
        await fetch('/kick', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({group: g, user: alvo})
        });
    }

    async function bloquear(alvo) {
        await fetch('/ban', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({group: g, user: alvo})
        });
    }

    /* WEBRTC / CALLS */
    async function startCall(mode='video') {
        send(mode === 'video' ? "call" : "voice_call");
        document.getElementById('call-ui').style.display='flex';
        const constraints = { audio: true, video: mode === 'video' };
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        document.getElementById('local-v').srcObject = stream;
        document.getElementById('remote-v').srcObject = stream;
    }

    function toggleMute() {
        if(stream) {
            const audioTrack = stream.getAudioTracks()[0];
            if(audioTrack) {
                audioTrack.enabled = !audioTrack.enabled;
                document.getElementById('mic-btn').innerText = audioTrack.enabled ? "🎤" : "🔇";
            }
        }
    }

    function endCall() {
        if(stream) stream.getTracks().forEach(t => t.stop());
        document.getElementById('call-ui').style.display='none';
    }

    function toggleCfg() {
        const m = document.getElementById('config-menu');
        m.style.display = (m.style.display === 'block') ? 'none' : 'block';
    }

    /* SITEMA DE JOGOS INTEGRADO */
    function openGamesMenu() {
        const choice = prompt("Escolha o jogo:\\n1. Fuga da Maçã (Multiplayer)\\n2. Jogo da Velha\\n3. Eaglecraft (Minecraft JS)\\n4. Google+ Nostalgia");
        if(choice === '1') startFugaMaca();
        else if(choice === '2') startJogoDaVelha();
        else if(choice === '3') loadExternalGame('https://eaglercraft.com/mc/1.8.8/', 'Eaglecraft');
        else if(choice === '4') loadExternalGame('https://plus.google.com', 'Google+ Archive');
    }

    function closeGame() {
        document.getElementById('game-ui').style.display = 'none';
        document.getElementById('game-container').innerHTML = '';
        document.getElementById('game-chat-box').style.display = 'none';
    }

    function loadExternalGame(url, title) {
        document.getElementById('game-title').innerText = title;
        document.getElementById('game-container').innerHTML = `<iframe src="${url}" style="width:100%; height:100%; border:none;"></iframe>`;
        document.getElementById('game-ui').style.display = 'flex';
        document.getElementById('game-chat-box').style.display = 'none';
    }

    /* Jogo 1: Fuga da Maçã Multiplayer */
    let macaPos = {x: 50, y: 50}, playerPos = {x: 200, y: 200};
    function startFugaMaca() {
        document.getElementById('game-title').innerText = "Fuga da Maçã (Multiplayer)";
        document.getElementById('game-container').innerHTML = `<canvas id="game-canvas"></canvas>`;
        document.getElementById('game-ui').style.display = 'flex';
        document.getElementById('game-chat-box').style.display = 'flex';
        
        send("text", `🎮 Convite: Entrei na Fuga da Maçã! Clique no menu de jogos para jogar comigo.`);
        
        const canvas = document.getElementById('game-canvas');
        canvas.width = window.innerWidth; canvas.height = window.innerHeight - 40;
        const ctx = canvas.getContext('2d');

        window.onkeydown = (e) => {
            if(e.key === 'ArrowUp') playerPos.y -= 10;
            if(e.key === 'ArrowDown') playerPos.y += 10;
            if(e.key === 'ArrowLeft') playerPos.x -= 10;
            if(e.key === 'ArrowRight') playerPos.x += 10;
        };

        function loop() {
            if(document.getElementById('game-ui').style.display === 'none') return;
            ctx.clearRect(0,0,canvas.width, canvas.height);
            
            // Desenha a Maçã
            ctx.fillStyle = "red";
            ctx.beginPath(); ctx.arc(macaPos.x, macaPos.y, 15, 0, Math.PI*2); ctx.fill();

            // Desenha Jogador
            ctx.fillStyle = "#00ffcc";
            ctx.fillRect(playerPos.x, playerPos.y, 20, 20);
            ctx.fillStyle = "white"; ctx.fillText(u, playerPos.x - 5, playerPos.y - 5);

            requestAnimationFrame(loop);
        }
        loop();
    }

    /* Jogo 2: Jogo da Velha */
    function startJogoDaVelha() {
        document.getElementById('game-title').innerText = "Jogo da Velha";
        document.getElementById('game-container').innerHTML = `
            <div style="display:grid; grid-template-columns: repeat(3, 80px); gap: 5px; justify-content:center; align-content:center; height:100%;">
                ${[0,1,2,3,4,5,6,7,8].map(i => `<button id="t-${i}" onclick="playVelha(${i})" style="height:80px; font-size:24px; background:#222; color:white;">-</button>`).join('')}
            </div>
        `;
        document.getElementById('game-ui').style.display = 'flex';
        document.getElementById('game-chat-box').style.display = 'none';
    }

    let velhaTurn = 'X';
    function playVelha(i) {
        const btn = document.getElementById(`t-${i}`);
        if(btn.innerText === '-') {
            btn.innerText = velhaTurn;
            velhaTurn = velhaTurn === 'X' ? 'O' : 'X';
        }
    }

    function sendGameChat() {
        const input = document.getElementById('gameMsgInput');
        if(input.value) {
            send("text", `[No Jogo] ${input.value}`);
            input.value = '';
        }
    }

    /* Sincronização Geral */
    async function sync() {
        const metaRes = await fetch(`/room_info?group=${g}&user=${u}`);
        const meta = await metaRes.json();
        
        if (meta.kicked_or_banned) {
            alert("Você foi removido ou bloqueado deste grupo.");
            location.href = '/';
            return;
        }

        document.getElementById('count-display').innerText = `📶 ${meta.qtd} online`;

        const isAdm = meta.adms && meta.adms.includes(u);
        if(isAdm) {
            document.getElementById('adm-badge').innerHTML = '<span class="adm-tag">ADM</span>';
            document.getElementById('adm-panel').style.display = 'block';
            
            const listContainer = document.getElementById('membros-lista-box');
            listContainer.innerHTML = '';
            meta.membros.forEach(m => {
                if(m !== u) {
                    const eAdmin = meta.adms.includes(m);
                    const row = document.createElement('div');
                    row.className = 'membro-row';
                    row.innerHTML = `
                        <span>${m} ${eAdmin ? '<b style="color:var(--pink)">(ADM)</b>' : ''}</span>
                        <div>
                            ${eAdmin ? 
                                `<span onclick="rebaixarADM('${m}')" style="color:yellow; cursor:pointer; margin-right:5px;">-ADM</span>` : 
                                `<span onclick="promoverADM('${m}')" style="color:green; cursor:pointer; margin-right:5px;">+ADM</span>`
                            }
                            <span onclick="expulsar('${m}')" style="color:orange; cursor:pointer; margin-right:5px;">Excluir</span>
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
            const gMsgs = document.getElementById('game-msgs');

            for(let i=last; i<filtered.length; i++) {
                const m = filtered[i];
                if(i > 0 && m.user !== u) playNotificationSound();

                const container = document.createElement('div');
                const isMine = m.user === u;
                container.className = `msg-container ${isMine ? 'mine' : 'others'}`;

                if(m.type === "call" || m.type === "voice_call") {
                    container.className = "msg-container others";
                    container.innerHTML = `
                        <span class="msg-nick">${m.user}</span>
                        <div class="bubble" style="background:var(--green)">
                            ${m.type === "call" ? "iniciou vídeo." : "iniciou chamada de voz."}<br>
                            <button onclick="startCall('${m.type === "call" ? "video" : "voice"}')" style="background:white; color:black; margin-top:5px; padding:3px 10px; font-size:10px; border-radius:6px;">ENTRAR</button>
                        </div>`;
                } else if(m.type === "image") {
                    container.innerHTML = `
                        <span class="msg-nick">${isMine ? 'you' : m.user}</span>
                        <div class="bubble"><img src="${m.msg}" /></div>`;
                } else if(m.type === "system_alert") {
                    container.className = "msg-container others"; container.style.width = "100%";
                    container.innerHTML = `
                        <span class="msg-nick" style="color:red">🔒 ALERTA DE SISTEMA</span>
                        <div class="bubble" style="background:#5c061a; border: 1px solid red; color: #ff9999;">${m.msg}</div>`;
                } else {
                    container.innerHTML = `
                        <span class="msg-nick">${isMine ? 'you' : m.user}</span>
                        <div class="bubble">${m.msg}</div>`;
                }
                flow.appendChild(container);

                // Sincroniza chat secundário do jogo
                if(gMsgs) {
                    const gLine = document.createElement('div');
                    gLine.innerText = `${m.user}: ${m.msg}`;
                    gMsgs.appendChild(gLine);
                    gMsgs.scrollTop = gMsgs.scrollHeight;
                }
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

@app.route('/receive', methods=['POST'])
def receive():
    dados = request.json
    if not dados:
        return jsonify({"status": "error", "message": "Dados inválidos."}), 400

    grupo = dados.get('group')
    usuario = dados.get('user')
    tipo = dados.get('type')
    mensagem = dados.get('msg')

    if not grupo or not usuario:
        return jsonify({"status": "error", "message": "Dados obrigatórios ausentes."}), 400

    if grupo in salas_estado and usuario in salas_estado[grupo].get('banidos', set()):
        return jsonify({"status": "error", "message": "🔒 Código Banido por violação de segurança."}), 403

    if tipo == "ban_command" and mensagem == "banido":
        if grupo in salas_estado:
            if usuario in salas_estado[grupo]['membros']:
                salas_estado[grupo]['membros'].remove(usuario)
            salas_estado[grupo]['banidos'].add(usuario)
        return jsonify({"status": "error", "message": "🔒 Código Banido por atividade não autorizada."}), 403

    chat_history.append(dados)
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
            salas_estado[g] = {'adms': {u}, 'membros': set(), 'banidos': set()}
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
            "adms": list(salas_estado[g]['adms']),
            "membros": list(salas_estado[g]['membros'])
        })
    return jsonify({"kicked_or_banned": False, "qtd": 1, "adms": [u], "membros": [u]})

@app.route('/add_adm', methods=['POST'])
def add_adm():
    data = request.json
    g, target = data.get('group'), data.get('user')
    if g in salas_estado and target in salas_estado[g]['membros']:
        salas_estado[g]['adms'].add(target)
    return jsonify({"status": "ok"})

@app.route('/remove_adm', methods=['POST'])
def remove_adm():
    data = request.json
    g, target = data.get('group'), data.get('user')
    if g in salas_estado and target in salas_estado[g]['adms']:
        salas_estado[g]['adms'].remove(target)
    return jsonify({"status": "ok"})

@app.route('/change_name', methods=['POST'])
def change_name():
    data = request.json
    g, old, new = data.get('group'), data.get('old_user'), data.get('new_user')
    if g in salas_estado:
        if old in salas_estado[g]['membros']:
            salas_estado[g]['membros'].remove(old)
            salas_estado[g]['membros'].add(new)
        if old in salas_estado[g]['adms']:
            salas_estado[g]['adms'].remove(old)
            salas_estado[g]['adms'].add(new)
        for msg in chat_history:
            if msg['group'] == g and msg['user'] == old:
                msg['user'] = new
    return jsonify({"status": "ok"})

@app.route('/kick', methods=['POST'])
def kick_user():
    data = request.json
    g, target = data.get('group'), data.get('user')
    if g in salas_estado and target in salas_estado[g]['membros']:
        salas_estado[g]['membros'].remove(target)
    return jsonify({"status": "ok"})

@app.route('/ban', methods=['POST'])
def ban_user():
    data = request.json
    g, target = data.get('group'), data.get('user')
    if g in salas_estado:
        if target in salas_estado[g]['membros']:
            salas_estado[g]['membros'].remove(target)
        salas_estado[g]['banidos'].add(target)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
