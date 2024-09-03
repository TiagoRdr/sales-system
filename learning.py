from flask import Flask, render_template, request

app = Flask(__name__)

app.config['FLASK_ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TESTING'] = True



marcas = []
clientes = {}
@app.route('/', methods=["GET", "POST"])
def main():
    #Lista
    frutas = ['Morango', 'Larajna', "Pera", 'XI']

    #Dict
    jogos = {1: "LOL", 2: "CS", 3: "Valorant"}

    #Envio de dados LISTA    
    if request.method == "POST":
        if request.form.get("marcas"):
            marcas.append(request.form.get("marcas"))
    
    #Envio de dados Dict    
    if request.method == "POST":
        if request.form.get("codigo") and request.form.get("nome"):
            clientes[request.form.get("codigo")] = request.form.get("nome")
    
    return render_template("index.html", frutas=frutas, jogos=jogos, marcas=marcas, clientes=clientes)


@app.route("/consulta")
def consulta():
    return render_template("consulta.html")


app.run(debug=True)