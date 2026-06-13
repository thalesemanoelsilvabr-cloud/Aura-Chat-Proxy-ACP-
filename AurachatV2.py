from flask import Flask, request, jsonify, render_template
import time

app = Flask(__name__)

# --- BANCO DE DADOS EM MEMÓRIA ---
chat_history = []       # Armazena todas as mensagens do chat
usuarios_online = {}    # Estrutura: {"nome_do_grupo": ["Usuario1", "Usuario2"]}

# --- CONFIGURAÇÕES DO MONITOR DE TRÁFEGO (DEFESA) ---
historico_trafego = {}  # Estrutura: {"nome_do_grupo": [timestamp1, timestamp2, ...]}
LIMITE_MENSAGENS = 10   # Máximo de mensagens permitidas na janela de tempo
JANELA_SEGUNDOS = 3     # Tempo em segundos da janela de análise
COOLDOWN_ALERTA = 10    # Tempo de espera (em segundos) para não duplicar o alerta
ultimos_alertas = {}    # Estrutura: {"nome_do_grupo": timestamp_do_ultimo_alerta}


@app.route('/')
def index():
    return "AuraChat Backend rodando com sucesso!"


@app.route('/receive', methods=['POST'])
def receive():
    dados = request.json
    if not dados:
        return jsonify({"status": "error", "message": "Dados inválidos"}), 400

    grupo = dados.get('group')
    usuario = dados.get('user')
    tipo = dados.get('type')
    mensagem = dados.get('msg')
    agora = time.time()

    if not grupo or not usuario:
        return jsonify({"status": "error", "message": "Grupo ou usuário ausente"}), 400

    # 1. INICIALIZA AS ESTRUTURAS DO GRUPO SE NÃO EXISTIREM
    if grupo not in usuarios_online:
        usuarios_online[grupo] = []
    if grupo not in historico_trafego:
        historico_trafego[grupo] = []

    # 2. MONITORAMENTO DE REQUISIÇÕES (SISTEMA DE ALERTA DE INUNDAÇÃO)
    # Registra o timestamp do envio atual
    historico_trafego[grupo].append(agora)

    # Remove registros antigos que estão fora da janela de 3 segundos
    historico_trafego[grupo] = [ts for ts in historico_trafego[grupo] if agora - ts <= JANELA_SEGUNDOS]

    # Verifica se a quantidade de mensagens estourou o limite de segurança
    if len(historico_trafego[grupo]) > LIMITE_MENSAGENS:
        ultimo_alerta_tempo = ultimos_alertas.get(grupo, 0)
        
        # Só dispara o alerta se passou o tempo de cooldown (evita inundar o chat com o próprio aviso)
        if agora - ultimo_alerta_tempo > COOLDOWN_ALERTA:
            mensagem_alerta = (
                "Olá, aqui é da AuraChat Alertas. Porfavor saiam imediatamente desse grupo "
                "e volt depois de 5 segundos, etsa acontecendo um ataque ddos, e para a sua "
                "segurança saia, mas tentaremos tirar ele da rede"
            )

            payload_alerta = {
                "user": "🔒 AURA_ALERTAS",
                "group": grupo,
                "msg": mensagem_alerta,
                "type": "system_alert",
                "ts": int(agora * 1000)
            }
            
            chat_history.append(payload_alerta)
            ultimos_alertas[grupo] = agora
            print(f"⚠️ Alerta de segurança acionado no grupo: [{grupo}]")

    # 3. PROCESSAMENTO DOS TIPOS DE MENSAGEM
    if tipo == "status":
        if mensagem == "offline":
            # Remove o usuário da lista de online se ele estiver nela
            if usuario in usuarios_online[grupo]:
                usuarios_online[grupo].remove(usuario)
            
            # Notifica o grupo sobre a saída
            chat_history.append({
                "user": "Sistema",
                "group": grupo,
                "msg": f"🛑 {usuario} saiu do chat.",
                "type": "system",
                "ts": int(agora * 1000)
            })
        return jsonify({"status": "ok", "usuarios_online": usuarios_online[grupo]})

    # Gerenciamento padrão para mensagens de texto comuns
    # Adiciona o usuário na lista de online se ele acabou de mandar mensagem e não constava lá
    if usuario not in usuarios_online[grupo] and usuario != "SISTEMA":
        usuarios_online[grupo].append(usuario)

    # Salva a mensagem recebida no histórico global
    chat_history.append(dados)
    return jsonify({"status": "ok", "usuarios_online": usuarios_online[grupo]})


@app.route('/history/<nome_grupo>', methods=['GET'])
def get_history(nome_grupo):
    """Rota para o JavaScript buscar as mensagens e os usuários online atualizados"""
    mensagens_grupo = [msg for msg in chat_history if msg.get('group') == nome_grupo]
    online = usuarios_online.get(nome_grupo, [])
    
    return jsonify({
        "messages": mensagens_grupo,
        "usuarios_online": online
    })


# Configuração necessária para rodar localmente ou expor para a Vercel/Render
handler = app 

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
