from flask import request, redirect, url_for, render_template
import time
import os
from app_conf import app
from database import DatabaseConnection


############ TELA PRINCIPAL DE CADASTROS ##############
@app.route("/cadastro")
def cadastro_main():
    return render_template("cadastro.html")


@app.route("/cadastro-produtos")
def cadastro_produtos():  
    db_connection = DatabaseConnection()
    cadastroprodutos = CadastroProdutos(db_connection)  
    fornecedores, marcas = cadastroprodutos.busca_fornecedores_marcas()
    return render_template("cadastro-produtos.html", fornecedores=fornecedores, marcas=marcas)


class CadastroProdutos:
    def __init__(self, db_connection) -> None:
        self.db_connection = db_connection

    def busca_fornecedores_marcas(self):

        list_forn = []
        list_marcas = []
        query_forn = f"""select                            
                                nome       
                                from fornecedores f
                                where nome is not null  
                                order by id desc
                        """
        result_forn = self.db_connection.execute_query(query_forn)
        query_marca = f"""select 
                                distinct(marca)
                                from produtos p  
                                where marca is not null 
                        """
        result_marcas = self.db_connection.execute_query(query_marca)

        for i in range(len(result_forn)):
            list_forn.append(str(result_forn[i]).split("'")[1])

        for i in range(len(result_marcas)):
            list_marcas.append(str(result_marcas[i]).split("'")[1])

        return list_forn, list_marcas
    
@app.route("/salvar-produto", methods=["POST", "GET"])
def salvar_produtos():
    db_connection = DatabaseConnection()
    db_connection.connect()

    nome_produto = request.form.get("input_nome_produto")
    marca_produto = request.form.get("input_marca")
    fornecedor_produto = request.form.get("input_fornecedor")
    data_validade_produto = request.form.get("input_data_validade")
    qtd_estoque_produto = request.form.get("input_quantidade")
    valor_unitario_produto = float(str(request.form.get("input_valor_unitario")).replace(",","."))
    peso_produto = request.form.get("input_peso")
    custo_produto = float(str(request.form.get("input_custo_aquisicao")).replace(",","."))
    foto_produto = request.files.get('imagem_produto')

    if foto_produto:
        imagem_binaria = foto_produto.read()
    else:
        caminho_imagem = os.path.join(os.getcwd(), 'static', 'no-photo.png')
        with open(caminho_imagem, 'rb') as file:        
            imagem_binaria = file.read()

    query = """select                            
                            id                          
                            from fornecedores f 
                            where nome = %s
                            order by id desc"""
    
    result_cursor_codigo_fornecedor = db_connection.execute_query(query, params=(fornecedor_produto,))

    print(result_cursor_codigo_fornecedor)

    if len(result_cursor_codigo_fornecedor) > 0:
        codigo_fornecedor = result_cursor_codigo_fornecedor[0][0]
    else:
        codigo_fornecedor = 0

    query_insert = """
            INSERT INTO produtos (nome, id_fornecedor, qtd_estoque, valor_unitario, marca, data_validade, peso, custo_aquisicao, foto) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

    salvar_produtos = db_connection.execute_query(query_insert, False, (nome_produto, codigo_fornecedor, qtd_estoque_produto, valor_unitario_produto, marca_produto, data_validade_produto, peso_produto, custo_produto, imagem_binaria))
    salvar_produtos.close()
    
    time.sleep(2)
    return redirect(url_for('cadastro_produtos'))




############ CADASTRO CLIENTES ##############
@app.route("/cadastro-clientes")
def cadastro_clientes():    
    return render_template("cadastro-clientes.html")

class CadastrosClientes:
    def __init__(self, db_connection) -> None:
        self.db_connection = db_connection

@app.route("/salvar-clientes", methods=["POST", "GET"])
def salvar_clientes():
    db_connection = DatabaseConnection()
    db_connection.connect()

    nome_cliente = request.form.get("input_nome_cliente")
    cpfncpj_cliente = request.form.get("input_cpfcnpj_cliente")
    email_cliente = request.form.get("input_email_cliente")
    telefone_cliente = request.form.get("input_telefone_cliente")
    endereco_cliente = request.form.get("input_endereco_cliente")
    observacoes_cliente = request.form.get("input_observacoes_cliente")

    query_insert = """
            INSERT INTO clientes (nome, cpf_cnpj, email, telefone, endereco, observacoes) VALUES (%s, %s, %s, %s, %s, %s)
        """

    result_salvar_clientes = db_connection.execute_query(query_insert, False, (nome_cliente, cpfncpj_cliente, email_cliente, telefone_cliente, endereco_cliente, observacoes_cliente))
    result_salvar_clientes.close()
    time.sleep(2)
    return redirect(url_for('cadastro_clientes'))



############ CADASTRO FORNECEDORES ##############
@app.route("/cadastro-fornecedores")
def cadastro_fornecedores():    
    return render_template("cadastro-fornecedores.html")

class CadastroFornecedores:
    def __init__(self, db_connection) -> None:
        self.db_connection = db_connection

@app.route("/salvar-fornecedores", methods=["POST", "GET"])
def salvar_fornecedores():

    db_connection = DatabaseConnection()
    db_connection.connect()


    nome_fornecedor = request.form.get("input_nome_fornecedor")
    cpfncpj_fornecedor = request.form.get("input_cpfcnpj_fornecedor")
    email_fornecedor = request.form.get("input_email_fornecedor")
    telefone_fornecedor = request.form.get("input_telefone_fornecedor")
    endereco_fornecedor = request.form.get("input_endereco_fornecedor")
    observacoes_fornecedor = request.form.get("input_observacoes_fornecedor")

    query_insert = """
            INSERT INTO fornecedores (nome, cpf_cnpj, email, telefone, endereco, observacoes) VALUES (%s, %s, %s, %s, %s, %s)
        """

    result_salvar_fornecedores = db_connection.execute_query(query_insert, False, (nome_fornecedor, cpfncpj_fornecedor, email_fornecedor, telefone_fornecedor, endereco_fornecedor, observacoes_fornecedor))
    result_salvar_fornecedores.close()
    time.sleep(2)
    return redirect(url_for('cadastro_fornecedores'))