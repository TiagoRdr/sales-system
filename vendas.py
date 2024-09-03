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
    
    
    if request.method == "POST":
        produtos.append([request.form.get("inputproduto"), request.form.get("inputquantidade"), request.form.get("inputvalorunitario")])
        return redirect(url_for("main"))
    return render_template("index.html", data_atual=data, produtos=produtos)


@app.route("/consulta")
def consulta():
    return render_template("consulta.html")


app.run(debug=True)