from flask import Flask, render_template, request, redirect, url_for
import datetime

app = Flask(__name__)

app.config['FLASK_ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TESTING'] = True

produtos = []

clientes = {}
@app.route('/', methods=["GET", "POST"])
def main():  
    data = datetime.date.today().strftime("%Y-%m-%d")
    
    if 'add-prod' in request.form:      
        if request.method == "POST":
            produtos.append([request.form.get("inputproduto"), request.form.get("inputquantidade"), request.form.get("inputvalorunitario")])
            #return redirect(url_for("main"))
    else:
        pass
    print(produtos)
    return render_template("index.html", data_atual=data, produtos=produtos)

@app.route('/remove/<int:product_id>', methods=['POST'])
def remove_product(product_id):
    # Remove o produto pela posição na lista
    if 0 <= product_id < len(produtos):
        del produtos[product_id]
    return redirect(url_for('main'))

@app.route("/consulta")
def consulta():
    return render_template("consulta.html")


app.run(debug=True)