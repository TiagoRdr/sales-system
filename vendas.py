from flask import Flask, render_template, request, redirect, url_for
import datetime

app = Flask(__name__)

app.config['FLASK_ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TESTING'] = True

data_atual = datetime.date.today().strftime("%Y-%m-%d")
produtos = []

@app.route('/', methods=["GET", "POST"])
def main():  
    
    return render_template("index.html", data_atual=data_atual, produtos=produtos)


@app.route('/add_product', methods=['POST'])
def add_product():
    
    product_name = request.form.get('produto')
    product_qtd = request.form.get('quantidade')
    product_valor_unit = request.form.get('valorunitario')   
    #print(product_name, product_qtd, product_valor_unit)
    
    if product_name and product_qtd and product_valor_unit:
        produtos.append([product_name, product_qtd, product_valor_unit])
    print(produtos)
    return redirect(url_for('main'))


@app.route('/remove/<int:index>', methods=['POST'])
def remove_product(index):
    if 0 <= index < len(produtos):
        produtos.pop(index)
    print(produtos)
    return redirect(url_for('main'))

@app.route('/list-products')
def list_products():    
    return render_template('list-products.html', produtos=produtos)


@app.route("/consulta")
def consulta():
    return render_template("consulta.html")


app.run(debug=True)