from flask import Flask, render_template, request, redirect, url_for

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

if __name__ == '__main__':
    app.run(debug=True)