from flask import request, redirect, url_for, render_template
from app_conf import app
import time
import os
from datetime import date
from datetime import datetime
from database import DatabaseConnection

data_atual = date.today().strftime("%Y-%m-%d")

############ CADASTRO COMPRAS ##############
@app.route("/compras")
def compras():    
    return render_template("compras.html")


@app.route("/nova-compra")
def nova_compra():    
    fornecedores, produtos = busca_fornecedores_produtos()
    return render_template("nova-compra.html", fornecedores=fornecedores, produtos=produtos, data_atual=data_atual)


@app.route("/salvar-compra", methods=["POST"])
def salvar_compra():
    db_connection = DatabaseConnection()
    db_connection.connect()
    
    nome_fornecedor = request.form.get("inputfornecedor")
    nome_produto = request.form.get("inputnomeproduto")

    quantidade_comprada = request.form.get("inputqtd")
    preco_unitario = request.form.get("inputprecounitario")
    data_compra = request.form.get("inputdatacompra")
    data_pagamento = request.form.get("inputdatapagamento")
    valor_total_compra = request.form.get("inputtotalcompra")
    numero_nota_fiscal = request.form.get("inputnotafiscal")
    metodo_pagamento = request.form.get("inputmetodopagamento")
    observacoes = request.form.get("inputobservacoes")

    query_id_fornecedor = f"""
    select id from fornecedores f where nome = '{nome_fornecedor}'
        """
    result_get_id_fornecedor = db_connection.execute_query(query_id_fornecedor)

    query_id_produto = f"""
    select id from produtos p where nome = '{nome_produto}'
        """
    result_get_id_produto = db_connection.execute_query(query_id_produto)



    if len(result_get_id_fornecedor) > 0:
        codigo_fornecedor = result_get_id_fornecedor[0][0]
    else:
        query_salvar_fornecedor = """
            INSERT INTO fornecedores (nome) VALUES (%s)
        """
        result_salvar_fornecedor = db_connection.execute_query(query_salvar_fornecedor, False, (nome_fornecedor,))
        codigo_fornecedor = result_salvar_fornecedor.lastrowid

    if len(result_get_id_produto) > 0:
        codigo_produto = result_get_id_produto[0][0]
    else:
        caminho_imagem = os.path.join(os.getcwd(), 'static', 'no-photo.png')
        with open(caminho_imagem, 'rb') as file:        
            imagem_binaria = file.read()

        query_salvar_produto = """
            INSERT INTO produtos (nome, id_fornecedor, qtd_estoque, valor_unitario, foto, data_validade) VALUES (%s, %s, %s, %s, %s, %s)
        """
        result_salvar_produto = db_connection.execute_query(query_salvar_produto, False, (nome_produto, codigo_fornecedor, quantidade_comprada, preco_unitario, imagem_binaria, datetime.strptime('2029-12-31', '%Y-%m-%d')))
        codigo_produto = result_salvar_produto.lastrowid


    query_insert_compras = """
            INSERT INTO `tr-sale-system`.compras
            (id_produto, quantidade_comprada, preco_unitario, data_compra, id_fornecedor, valor_total_compra, numero_nota_fiscal, metodo_pagamento, observacoes, data_pagamento)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
        """
    result_salvar_compras = db_connection.execute_query(query_insert_compras, False, (codigo_produto, quantidade_comprada, preco_unitario, data_compra, codigo_fornecedor, valor_total_compra, numero_nota_fiscal, metodo_pagamento, observacoes, data_pagamento))
    
    time.sleep(2)
    return redirect(url_for('nova_compra'))



def busca_fornecedores_produtos():
    list_forn = []
    list_produtos = []
    db_connection = DatabaseConnection()
    db_connection.connect()
    query_forn = f"""select                            
                            nome       
                            from fornecedores f
                            where nome is not null  
                            order by id desc
                    """
    result_forn = db_connection.execute_query(query_forn)
    query_produto = f"""select                           
                            p.nome                           
                            from produtos p                            
                            ORDER BY p.id desc
                    """
    result_produtos = db_connection.execute_query(query_produto)

    for i in range(len(result_forn)):
        list_forn.append(str(result_forn[i]).split("'")[1])

    for i in range(len(result_produtos)):
        list_produtos.append(str(result_produtos[i]).split("'")[1])

    return list_forn, list_produtos