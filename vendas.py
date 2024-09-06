from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import datetime

app = Flask(__name__)

app.config['FLASK_ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TESTING'] = True

data_atual = datetime.date.today().strftime("%Y-%m-%d")
produtos = []

@app.route('/', methods=["GET", "POST"])
def main():  
    # Se estiver fora da função
    total_prods = total_produtos()    
    return render_template("index.html", data_atual=data_atual, produtos=produtos, total_prods=total_prods)

def total_produtos():
    total_prods = 0
    try:
        for i in range(len(produtos)):
            total_prods += round((int(produtos[i][1]) * float(str(produtos[i][2]).replace(",","."))),2)
    except Exception as e:
        print(e)
        total_prods = 0

    return total_prods

def total_vendas(taxaentrega, desconto):
    total_venda = 0
    total_prod = total_produtos()    
    try:
        total_venda = round(float(total_prod) + (float(str(taxaentrega).replace(",",".")) - float(str(desconto).replace(",","."))),2)
    except Exception as e:
        print(e)
        total_venda = 0
    return total_venda


@app.route('/add_product', methods=['POST'])
def add_product():    
    product_name = request.form.get('produto')
    product_qtd = request.form.get('quantidade')
    product_valor_unit = request.form.get('valorunitario')
    print(product_name, product_qtd, product_valor_unit)
    
    if product_name and product_qtd and product_valor_unit:
        produtos.append([product_name, product_qtd, product_valor_unit])

    return redirect(url_for('main'))


@app.route('/remove/<int:index>', methods=['POST'])
def remove_product(index):
    if 0 <= index < len(produtos):
        produtos.pop(index)
    print(produtos) 
    return redirect(url_for('main'))



@app.route('/clear_products', methods=["POST"])
def clear_products():    
    produtos.clear() # Limpa a lista de produtos
    total_prods = total_produtos()
    return render_template('total-products.html', total_prods=total_prods)



@app.route('/list-products')
def list_products():    
    return render_template('list-products.html', produtos=produtos)


@app.route('/resume-sale', methods=['POST', 'GET'])
def resume_sale():
    try:
        total_prods = total_produtos()
        product_taxa = request.form.get('valortaxa') 
        product_desconto = request.form.get('valordesconto')

        if not product_taxa or not product_desconto:
            return jsonify({"error": "Missing values"}), 400  # Retorna erro 400 se valores ausentes

        total_venda = total_vendas(product_taxa, product_desconto)
        return render_template('/resume-sale.html', total_prods=total_prods, total_venda=total_venda, taxaentrega=product_taxa, desconto=product_desconto)

    
    except Exception as e:
        print("Erro no processamento:", str(e))
        return jsonify({"error": "Server error"}), 500


@app.route("/consulta")
def consulta():
    return render_template("consulta.html")


app.run(debug=True)