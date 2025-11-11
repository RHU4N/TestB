from flask import Flask, render_template, request, redirect, url_for, jsonify
import os

# Carrega .env automaticamente se python-dotenv estiver instalado
try:
    # Import dynamicamente para evitar erro em ambientes onde python-dotenv não está instalado
    import importlib
    dotenv = importlib.import_module('dotenv')
    dotenv.load_dotenv()
except Exception:
    # python-dotenv não está disponível; assume variáveis de ambiente do sistema
    pass

try:
    import requests
except Exception:
    requests = None

app = Flask(__name__)

# Simulação de um banco de dados
# Adicione a chave 'foto' com o caminho da imagem de cada veículo
veiculos = {
    'compactos': [
        {'id': 1, 'nome': 'Fiat Mobi', 'opcionais': ['Ar condicionado', 'Vidros elétricos'], 'valor': 80.00, 'foto': 'mobi.jpg'},
        {'id': 2, 'nome': 'Renault Kwid', 'opcionais': ['Ar condicionado'], 'valor': 75.00, 'foto': 'kwid.jpg'},
    ],
    'suvs': [
        {'id': 3, 'nome': 'Jeep Renegade', 'opcionais': ['Ar condicionado', 'Multimídia', 'Direção elétrica'], 'valor': 150.00, 'foto': 'renegade.jpg'},
        {'id': 4, 'nome': 'Nissan Kicks', 'opcionais': ['Ar condicionado', 'Direção elétrica'], 'valor': 140.00, 'foto': 'kicks.jpg'},
    ],
    'esportivos': [
        {'id': 5, 'nome': 'Ford Mustang', 'opcionais': ['Motor V8', 'Câmbio automático', 'Bancos de couro'], 'valor': 350.00, 'foto': 'mustang.jpg'},
    ]
}

# (O resto do seu código Flask permanece o mesmo)
@app.route('/')
def index():
    # ...
    # Se você quiser fotos nas categorias, adicione-as aqui também.
    # Exemplo: categorias = {'compactos': {'foto': 'categoria_compactos.jpg'}, 'suvs': {'foto': 'categoria_suvs.jpg'}}
    # e depois ajuste o template index.html para usar isso.
    # Por enquanto, vamos manter a simplicidade e focar nas fotos dos veículos.
    categorias = veiculos.keys()
    return render_template('index.html', categorias=categorias)

@app.route('/categoria/<categoria_nome>')
def ver_categoria(categoria_nome):
    if categoria_nome in veiculos:
        lista_veiculos = veiculos[categoria_nome]
        return render_template('categoria.html', categoria=categoria_nome, veiculos=lista_veiculos)
    else:
        return "Categoria não encontrada", 404

@app.route('/checkout/<int:veiculo_id>')
def checkout(veiculo_id):
    veiculo_selecionado = None
    for categoria in veiculos.values():
        for veiculo in categoria:
            if veiculo['id'] == veiculo_id:
                veiculo_selecionado = veiculo
                break
        if veiculo_selecionado:
            break

    if veiculo_selecionado:
        return render_template('checkout.html', veiculo=veiculo_selecionado)
    else:
        return "Veículo não encontrado", 404


@app.route('/ai/recommend', methods=['POST'])
def ai_recommend():
    """Recomenda veículos com base nas preferências do usuário.

    Fluxo:
    - Recebe JSON: { budget: number|null, category: str|'any', features: [str] }
    - Filtra candidatos por categoria se fornecida
    - Pontua por estar dentro do orçamento e por casar com opcionais
    - Retorna top 3 recomendações. Se a variável de ambiente GEMINI_API_KEY
      estiver definida, tenta chamar a API Generative (Gemini) para gerar uma
      justificativa curta e incluí-la no retorno.
    """
    payload = request.get_json() or {}
    budget = payload.get('budget')
    category_pref = payload.get('category', 'any')
    features = payload.get('features', []) or []

    # Debug flag: se AI_DEBUG=1 no ambiente, incluímos informações de depuração
    ai_debug = os.environ.get('AI_DEBUG') == '1'
    if ai_debug:
        app.logger.debug(f"AI payload: {payload}")

    # Construir candidatos (já filtrando por categoria)
    candidates = []
    for cat_name, items in veiculos.items():
        if category_pref != 'any' and category_pref != cat_name:
            continue
        for v in items:
            c = v.copy()
            c['categoria'] = cat_name
            candidates.append(c)

    if ai_debug:
        app.logger.debug(f"category_pref={category_pref}, candidates_count={len(candidates)}")

    # Aplicar filtro estrito baseado no orçamento (se fornecido)
    strict_candidates = candidates
    try:
        if budget is not None:
            strict_candidates = [c for c in candidates if float(c.get('valor', 0)) <= float(budget)]
    except Exception:
        # se conversão falhar, mantenha candidates
        strict_candidates = candidates

    # Se houver features explicitamente fornecidas, exigir que cada veículo contenha
    # todos os recursos solicitados (modo estrito). Se isso eliminar todos os candidatos,
    # vamos permitir fallback para o conjunto original.
    if features:
        def has_all_features(c):
            opcionais = [o.lower() for o in c.get('opcionais', [])]
            return all(f.lower() in " ".join(opcionais) for f in features)

        strict_with_features = [c for c in strict_candidates if has_all_features(c)]
        if strict_with_features:
            strict_candidates = strict_with_features

    recs = []
    for c in candidates:
        score = 0
        try:
            valor = float(c.get('valor', 0))
        except Exception:
            valor = 0
        if budget:
            if valor <= float(budget):
                score += 20
                score += max(0, int((float(budget) - valor) / 10))
            else:
                score -= int((valor - float(budget)) / 10)

        opcionais = [o.lower() for o in c.get('opcionais', [])]
        match_count = 0
        for f in features:
            if f.lower() in " ".join(opcionais):
                match_count += 1
        score += match_count * 10

        recs.append({
            'id': c.get('id'),
            'nome': c.get('nome'),
            'categoria': c.get('categoria'),
            'valor': c.get('valor'),
            'score': score,
            'opcionais': c.get('opcionais', []),
        })

    recs = sorted(recs, key=lambda x: x['score'], reverse=True)

    # Se existirem candidatos estritos (budget/features), filtramos os resultados para eles.
    used_strict = False
    if strict_candidates:
        strict_ids = {c['id'] for c in strict_candidates}
        filtered = [r for r in recs if r['id'] in strict_ids]
        if filtered:
            recs = filtered
            used_strict = True

    # Se não houver correspondência estrita, mantemos o heurístico original e
    # informamos no retorno que nenhum veículo atendeu estritamente aos filtros.
    strict_notice = None
    if not used_strict and (budget is not None or features):
        strict_notice = 'Nenhum veículo correspondeu estritamente aos filtros; mostrando melhores alternativas.'

    if ai_debug:
        app.logger.debug(f"recs (top): {recs[:5]}")

    # Se houver chave GEMINI_API_KEY, tentar gerar explicação via Generative API
    gemini_key = os.environ.get('GEMINI_API_KEY')
    if gemini_key and len(recs) > 0 and requests is not None:
        try:
            # Monta prompt com os top 5 candidatos (não incluir valores para evitar que o modelo
            # retorne somas/totais de categoria)
            top_text = "\n".join([f"- {r['nome']} ({r['categoria']}) - opcionais: {', '.join(r['opcionais'])}" for r in recs[:5]])
            prompt = (
                f"Você é um assistente que recomenda veículos para aluguel. O usuário tem orçamento R$ {budget} e deseja: {', '.join(features)}. "
                "Escolha os 3 melhores veículos da lista abaixo e explique brevemente (1-2 frases cada). "
                "ATENÇÃO: não faça somas ou mostre o valor total por categoria — apenas comente cada veículo individualmente.\n"
                + top_text
            )

            # Chamada HTTP para a API Generative (Gemini) - usando endpoint REST com API key
            # Observação: o projeto do usuário precisa ativar a API e a key deve ser válida.
            # Suporta GEMINI_MODEL (recomendado) ou Model (compatibilidade com .env existente)
            model = os.environ.get('GEMINI_MODEL') or os.environ.get('Model') or 'text-bison-001'
            url = f"https://generativelanguage.googleapis.com/v1beta2/models/{model}:generateText?key={gemini_key}"
            body = {
                "prompt": {"text": prompt},
                "temperature": 0.6,
                "maxOutputTokens": 300
            }
            resp = requests.post(url, json=body, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            explanation = None
            # Extrair texto de retorno conforme esquema da API
            if 'candidates' in result and len(result['candidates']) > 0:
                explanation = result['candidates'][0].get('content')
            elif 'output' in result and 'text' in result['output']:
                explanation = result['output']['text']

            resp_payload = {'method': 'gemini', 'recommendations': recs[:3], 'explanation': explanation}
            if strict_notice:
                resp_payload['strict_notice'] = strict_notice
            return jsonify(resp_payload)
        except Exception as e:
            # em caso de erro na chamada externa, cair no heurístico
            resp_payload = {'method': 'heuristic', 'recommendations': recs[:3], 'error': str(e)}
            if strict_notice:
                resp_payload['strict_notice'] = strict_notice
            return jsonify(resp_payload)

    # Se não houver requests disponível ou GEMINI_KEY ausente, retornar heurístico
    if gemini_key and requests is None:
        # informar que a chave existe mas a biblioteca requests não está instalada
        resp_payload = {'method': 'heuristic', 'recommendations': recs[:3], 'warning': 'GEMINI_API_KEY set but `requests` not installed'}
        if strict_notice:
            resp_payload['strict_notice'] = strict_notice
        return jsonify(resp_payload)

    resp_payload = {'method': 'heuristic', 'recommendations': recs[:3]}
    if strict_notice:
        resp_payload['strict_notice'] = strict_notice
    return jsonify(resp_payload)

if __name__ == '__main__':
    app.run(debug=True)