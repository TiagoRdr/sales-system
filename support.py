from flask import render_template
from app_conf import app

############ CADASTRO FORNECEDORES ##############
@app.route("/suporte")
def suporte():    
    return render_template("suporte.html")
