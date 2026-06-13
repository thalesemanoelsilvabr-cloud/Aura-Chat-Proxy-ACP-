from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# ==========================================
# 💾 BANCO DE DADOS EM MEMÓRIA (ESTADOS)
# ==========================================
chat_history = []         # Armazena o histórico completo de mensagens (Infinitas)
usuarios_online = {}      # Estrutura: {"nome_do_grupo": ["Usuario1", "Usuario2"]}
usuarios_banidos = set()  # Guarda a lista negra de usuários banidos globalmente

# ==========================================
# 🛡️ CONFIGURAÇÕES DO SISTEMA ANTIDDOS AUTOBAN
# ==========================================
historico_trafego = {}    # Estrutura: {"nome_do_grupo_usuario": [timestamps]}
LIMITE_MENSAGENS = 10     # Gatilho de segurança
JANELA_SEGUNDOS = 3       # Tempo de análise do fluxo
COOLDOWN_ALERTA = 10      # Evita duplicação do aviso emergencial
ultimos_alertas = {}      # Registro por grupo

@app.route('/')
def index():
    return "AuraChat Core + Auto-Ban AntiDDoS rodando!"

@app.route('/receive', methods=['POST'])
def receive():
    dados = request.json
    if not dados:
        return jsonify({"status": "error", "message": "Dados inválidos."}), 400

    grupo = dados.get('group')
    usuario = dados.get('user')
    tipo = dados.get('type')
    mensagem = dados.get('msg')
    agora = time.time()

    if not grupo or not usuario:
        return jsonify({"status": "error", "message": "Dados obrigatórios ausentes."}), 400

    # ------------------------------------------------------------------
    # 🔒 SEGURANÇA CAMADA 1: FIREWALL ATIVO (BLOQUEIO COMPLETO)
    # ------------------------------------------------------------------
    if usuario in usuarios_banidos:
        return jsonify({
            "status": "error", 
            "message": "🔒 Código Banido: Seu acesso foi revogado por violação de segurança (DDoS Detectado)."
        }), 403

    if grupo not in usuarios_online:
        usuarios_online[grupo] = []

    # ------------------------------------------------------------------
    # 🔒 SEGURANÇA CAMADA 2: BANIMENTO MANUAL VIA SCRIPT
    # ------------------------------------------------------------------
    if tipo == "ban_command" and mensagem == "banido":
        usuarios_banidos.add(usuario)
        if usuario in usuarios_online[grupo]:
            usuarios_online[grupo].remove(usuario)
        print(f"🛑 [BAN MANUAL] O usuário [{usuario}] foi banido do servidor.")
        return jsonify({"status": "banned", "usuarios_online": usuarios_online[grupo]})

    # ------------------------------------------------------------------
    # 🔒 SEGURANÇA CAMADA 3: ANÁLISE HEURÍSTICA E AUTOBAN DE BOTS/DDOS
    # ------------------------------------------------------------------
    if usuario not in ["SISTEMA", "🔒 AURA_ALERTAS", "🔒 SEGURANÇA", "Sistema"]:
        chave_usuario = f"{grupo}_{usuario}"
        
        if chave_usuario not in historico_trafego:
            historico_trafego[chave_usuario] = []
            
        historico_trafego[chave_usuario].append(agora)
        historico_trafego[chave_usuario] = [ts for ts in historico_trafego[chave_usuario] if agora - ts <= JANELA_SEGUNDOS]

        # Se estourar a taxa limite na janela de tempo -> BAN NO ATO
        if len(historico_trafego[chave_usuario]) > LIMITE_MENSAGENS:
            usuarios_banidos.add(usuario)
            
            if usuario in usuarios_online[grupo]:
                usuarios_online[grupo].remove(usuario)
                
            print(f"🚨 [AUTOBAN] Atividade hostil detectada! [{usuario}] foi banido.")

            # Injeção do Alerta de Invasão Exato no Histórico do Grupo
            ultimo_alerta_tempo = ultimos_alertas.get(grupo, 0)
            if agora - ultimo_alerta_tempo > COOLDOWN_ALERTA:
                mensagem_alerta = (
                    "Olá, aqui é da AuraChat Alertas. Porfavor saiam imediatamente desse grupo "
                    "e volt depois de 5 segundos, etsa acontecendo um ataque ddos, e para a sua "
                    "segurança saia, mas tentaremos tirar ele da rede"
                )
                chat_history.append({
                    "user": "🔒 AURA_ALERTAS",
                    "group": grupo,
                    "msg": mensagem_alerta,
                    "type": "system_alert",
                    "ts": int(agora * 1000)
                })
                ultimos_alertas[grupo] = agora

            return jsonify({
                "status": "error", 
                "message": "🔒 Código Banido por atividade maliciosa de DDoS."
            }), 403

    # ------------------------------------------------------------------
    # ⚙️ FLUXO APLICATIVO ORIGINAL (SEM ALTERAÇÕES)
    # ------------------------------------------------------------------
    if tipo == "status":
        if mensagem == "offline":
            if usuario in usuarios_online[grupo]:
                usuarios_online[grupo].remove(usuario)
            chat_history.append({
                "user": "Sistema",
                "group": grupo,
                "msg": f"🛑 {usuario} saiu do chat.",
                "type": "system",
                "ts": int(agora * 1000)
            })
        return jsonify({"status": "ok", "usuarios_online": usuarios_online[grupo]})

    entidades_sistema = ["SISTEMA", "🔒 AURA_ALERTAS", "🔒 SEGURANÇA", "Sistema"]
    if usuario not in usuarios_online[grupo] and usuario not in entidades_sistema:
        usuarios_online[grupo].append(usuario)

    chat_history.append(dados)
    return jsonify({"status": "ok", "usuarios_online": usuarios_online[grupo]})


@app.route('/history/<nome_grupo>', methods=['GET'])
def get_history(nome_grupo):
    mensagens_grupo = [msg for msg in chat_history if msg.get('group') == nome_grupo]
    online = usuarios_online.get(nome_grupo, [])
    return jsonify({
        "messages": mensagens_grupo,
        "usuarios_online": online
    })

handler = app 

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
