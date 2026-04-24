from flask import Flask, render_template_string, request, jsonify
import logging
import random

app = Flask(__name__)
chat_history = []

# Silencia logs do Flask para deixar o terminal do Debian limpo
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AuraChat | Aura Inc.</title>
    <style>
        :root {
            --bg: #0b0c10;
            --card: #1a1b21;
            --text: #f1f1f1;
            --pink: #f34a74;
            --input-bg: #2a2c33;
            --btn-gray: #33353b;
        }
        body { 
            background: var(--bg); color: var(--text); font-family: sans-serif;
            margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; overflow: hidden;
            background-image: radial-gradient(circle, #222 1px, transparent 1px); background-size: 30px 30px;
        }
        .screen { display: none; width: 100%; max-width: 400px; flex-direction: column; gap: 15px; padding: 20px; box-sizing: border-box; }
        .active { display: flex; }
        .card { background: var(--card); border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); padding: 30px; text-align: center; }
        input { background: var(--input-bg); color: white; border: none; padding: 16px; border-radius: 12px; width: 100%; box-sizing: border-box; outline: none; }
        button { border-radius: 12px; border: none; font-weight: 600; cursor: pointer; transition: 0.2s; font-size: 14px; padding: 14px; }
        .btn-white { background: white; color: black; width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .btn-gray { background: #7a7a7a; color: white; width: 100%; opacity: 0.5; }
        .btn-join { background: var(--btn-gray); color: white; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(255,255,255,0.1); }
        #chat-screen { max-width: none; height: 100vh; padding: 0; background: #000; }
        .chat-header { padding: 15px; font-size: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #111; }
        #messages-flow { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
        .bubble { padding: 12px 16px; border-radius: 20px; font-size: 14px; max-width: 75%; line-height: 1.4; }
        .mine { background: #4a4760; align-self: flex-end; border-bottom-right-radius: 4px; }
        .others { background: #2a2c33; align-self: flex-start; border-bottom-left-radius: 4px; }
        .bubble b { display: block; font-size: 10px; opacity: 0.5; margin-bottom: 4px; }
        .chat-footer { padding: 10px; display: flex; align-items: center; gap: 12px; background: #15161a; margin: 15px; border-radius: 35px; }
        .send-circle { background: white; color: black; width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center; justify-content: center; padding: 0; }
        .share-btn { background: rgba(255,255,255,0.1); padding: 5px 12px; border-radius: 20px; color: white; font-size: 10px; cursor: pointer; }
    </style>
</head>
<body>
<div id="app" style="width: 100%;">
    <div id="login-screen" class="screen active">
        <div class="card">
            <h1>Welcome to AuraChat</h1>
            <input type="text" id="userInput" placeholder="Enter your name">
            <button class="btn-gray" id="btnContinue" onclick="toMenu()" disabled style="margin-top: 15px;">Continue</button>
        </div>
    </div>
    <div id="menu-screen" class="screen">
        <div class="card" style="background: transparent; border: none;">
            <h1>Nook<span style="color:var(--pink)">Chat</span></h1>
            <div style="display:flex; background:var(--input-bg); border-radius:14px; padding:4px; margin: 15px 0;">
                <input type="text" id="groupInput" placeholder="Enter code..." style="background:transparent;">
                <button class="btn-join" onclick="joinChat()">➔</button>
            </div>
            <button class="btn-white" onclick="createChat()">🛡️ Start new private chat</button>
        </div>
    </div>
    <div id="chat-screen" class="screen">
        <div class="chat-header">
            <!-- Importe o CSS do Bootstrap Icons no <head> -->
<link rel="stylesheet" href="https://jsdelivr.net">

<!-- O ícone dentro da div -->
<div style="width: 80px; font-size: 60px; color: black;">
    <i class="bi bi-wifi"></i>
</div>
            <div>🔒 <span id="display-g"></span> 👤 <span id="count">1</span></div>
            <div style="width: 80px; text-align: right;"><span class="share-btn" onclick="shareLink()">🔗 Compartilhar</span></div>
        </div>
        <div id="messages-flow"></div>
        <div class="chat-footer">
            <span style="cursor:pointer" onclick="addE('😊')">😊</span>
            <input type="text" id="msgInput" placeholder="Type your reply...">
            <button class="send-circle" onclick="send()">➔</button>
        </div>
    </div>
</div>
<script>
    let u = "", g = "", last = 0;
    document.getElementById('userInput').oninput = (e) => {
        const b = document.getElementById('btnContinue');
        b.disabled = !e.target.value;
        b.className = e.target.value ? "btn-white" : "btn-gray";
    };
    function toMenu() { u = document.getElementById('userInput').value; show('menu-screen'); }
    function joinChat() { g = document.getElementById('groupInput').value; if(g) start(); }
    function createChat() {
        const c = 'abcdefghijklmnopqrstuvwxyz0123456789'; g = '-';
        for(let i=0; i<5; i++) g += c.charAt(Math.floor(Math.random() * c.length));
        start();
    }
    function start() {
        show('chat-screen');
        document.getElementById('display-g').innerText = g;
        document.getElementById('messages-flow').innerHTML = '';
        setInterval(sync, 1000);
    }
    function show(id) {
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        document.getElementById(id).classList.add('active');
    }
    function addE(e) { document.getElementById('msgInput').value += e; }
    function shareLink() {
        const link = window.location.origin;
        const texto = "Venha para o chat do " + u + "!\\nCódigo: " + g + "\\nLink: " + link;
        navigator.clipboard.writeText(texto).then(() => { alert("Convite copiado! 🚀"); });
    }
    async function send() {
        const i = document.getElementById('msgInput');
        if(!i.value) return;
        await fetch('/receive', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({user: u, group: g, msg: i.value}) });
        i.value = '';
    }
    document.getElementById('msgInput').addEventListener('keypress', (e) => { if(e.key === 'Enter') send(); });
    async function sync() {
        const r = await fetch('/messages');
        const data = await r.json();
        const filtered = data.filter(m => m.group === g);
        document.getElementById('count').innerText = new Set(filtered.map(m => m.user)).size || 1;
        if(filtered.length > last) {
            const flow = document.getElementById('messages-flow');
            for(let i = last; i < filtered.length; i++) {
                const m = filtered[i];
                const div = document.createElement('div');
                div.className = `bubble ${m.user === u ? 'mine' : 'others'}`;
                div.innerHTML = `<b>${m.user === u ? 'you' : m.user}</b>${m.msg}`;
                flow.appendChild(div);
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
def home(): return render_template_string(HTML_TEMPLATE)

@app.route('/receive', methods=['POST'])
def receive():
    data = request.json
    chat_history.append(data)
    print(f"[{data['group']}] {data['user']}: {data['msg']}")
    return jsonify({"status": "ok"})

@app.route('/messages')
def messages(): return jsonify(chat_history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
