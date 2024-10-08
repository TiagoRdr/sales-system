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
    preco_unitario = float(str(request.form.get("inputprecounitario").replace(",", ".")))
    data_compra = request.form.get("inputdatacompra")
    data_pagamento = request.form.get("inputdatapagamento")
    valor_total_compra = float(str(request.form.get("inputtotalcompra").replace(",", ".")))
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
        query_update_produto = f"""
            UPDATE produtos set qtd_estoque = qtd_estoque + {quantidade_comprada} where id = {codigo_produto}
        """
        result_update_produto = db_connection.execute_query(query_update_produto, False)
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


@app.route("/consulta-compras-main")
def consulta_compras_main():
    db_connection = DatabaseConnection()
    db_connection.connect()
    lista_produtos = consulta_produtos()
    compras_mes = consulta_compras_mes()
    produto = ''
    datainicial = date.today().strftime("%Y-%m-%d")
    datafinal = date.today().strftime("%Y-%m-%d")
    return render_template("consulta-compras.html", compras_mes=compras_mes, datainicial=datainicial, datafinal=datafinal, produto=produto, lista_produtos=lista_produtos)



def consulta_compras_mes():
    db_connection = DatabaseConnection()
    db_connection.connect() 

    query = f"""select
                c.id,
                DATE_FORMAT(c.data_compra, '%d/%m/%Y') AS data_formatada,
                c.metodo_pagamento,
                f.nome,
                p.nome,
                REPLACE(FORMAT(c.valor_total_compra  , 2), '.', ','),
                c.status_compra
                from compras c 
                left join fornecedores f on c.id_fornecedor = f.id
                left join produtos p on p.id = c.id_produto
                ORDER BY c.id desc
                    """
    
    result_compras_mes = db_connection.execute_query(query)
    return result_compras_mes


@app.route("/consulta-compras-filtros" ,methods=["POST","GET"])
def consulta_compras_filtros():
    db_connection = DatabaseConnection()
    db_connection.connect()
    datainicial = request.form.get("datainicio") 
    datafinal = request.form.get("datafim")  
    produto = request.form.get("filtro_produto")

    if produto:
        query = f"""
                select
                    c.id,
                    DATE_FORMAT(c.data_compra, '%d/%m/%Y') AS data_formatada,
                    c.metodo_pagamento,
                    f.nome,
                    p.nome,
                    REPLACE(FORMAT(c.valor_total_compra  , 2), '.', ','),
                    c.status_compra
                    from compras c 
                    left join fornecedores f on c.id_fornecedor = f.id
                    left join produtos p on p.id = c.id_produto
                    where
                    c.data_compra between '{datainicial}' and '{datafinal}'
                    and p.nome = '{produto}'
                    group by c.id
                    ORDER BY c.id desc
                """
    else:
        query = f"""
            select
                c.id,
                DATE_FORMAT(c.data_compra, '%d/%m/%Y') AS data_formatada,
                c.metodo_pagamento,
                f.nome,
                p.nome,
                REPLACE(FORMAT(c.valor_total_compra  , 2), '.', ','),
                c.status_compra
                from compras c 
                left join fornecedores f on c.id_fornecedor = f.id
                left join produtos p on p.id = c.id_produto
                where
                c.data_compra between '{datainicial}' and '{datafinal}'
                group by c.id
                ORDER BY c.id desc
            """

    result_compras_filtros = db_connection.execute_query(query)
    
    lista_produtos = consulta_produtos()
    return render_template("consulta-compras.html", 
                            compras_mes=result_compras_filtros, 
                            lista_produtos=lista_produtos, 
                            produto=produto, 
                            datainicial=datainicial, 
                            datafinal=datafinal)


def consulta_produtos():
    db_connection = DatabaseConnection()
    db_connection.connect()
    query_produtos = f"""select                           
                            p.nome                           
                            from produtos p                            
                            ORDER BY p.id desc
                    """

    result_produtos = db_connection.execute_query(query_produtos)
    return result_produtos



@app.route("/visualizar-compra-main", methods=["POST", "GET"])
def visualizar_compra_main():
    try:
        codigo_compra = request.form.get("codigo")
        info_compra = consulta_compras_visualizar(codigo_compra)
        fornecedores, produtos = busca_fornecedores_produtos()

        return render_template("visualizar-compra.html", info_compra=info_compra, fornecedores=fornecedores, produtos=produtos)
    
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    

def consulta_compras_visualizar(codigo_compra):
    db_connection = DatabaseConnection()
    db_connection.connect()
    query_compras = f"""select 
                    c.id,
                    p.nome,
                    quantidade_comprada,
                    REPLACE(FORMAT(c.preco_unitario  , 2), '.', ','),
                    data_compra,
                    f.nome,
                    REPLACE(FORMAT(c.valor_total_compra  , 2), '.', ','),
                    numero_nota_fiscal,
                    metodo_pagamento,
                    c.observacoes,
                    data_pagamento,
                    c.status_compra,
                    c.id_produto
                    from compras c
                    left join fornecedores f on c.id_fornecedor = f.id
                    left join produtos p on p.id = c.id_produto
                    where c.id = {codigo_compra}
                    """

    result_compras = db_connection.execute_query(query_compras)
    return result_compras[0]


@app.route('/cancelaCompra/<int:idcompra>/<int:idproduto>/<int:quantidade>', methods=["POST"])
def cancelar_compra(idcompra, idproduto, quantidade):
    db_connection = DatabaseConnection()
    db_connection.connect() 
    status_venda = '❌ Cancelada'

    query_cancelar = f"UPDATE compras set status_compra = '{status_venda}' WHERE id={idcompra}"
    result_cancelar_venda = db_connection.execute_query(query_cancelar, False)

    query_update_produto = f"""
            UPDATE produtos set qtd_estoque = qtd_estoque - {quantidade} where id = {idproduto}
        """
    result_update_produto = db_connection.execute_query(query_update_produto, False)
    
    return redirect(url_for('consulta_compras_main'))