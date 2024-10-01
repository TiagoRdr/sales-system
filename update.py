from flask import request, redirect, url_for, render_template
import time
import os
from app_conf import app
from database import DatabaseConnection
from cadastros import CadastroProdutos

@app.route("/atualizar-produtos-main", methods=["POST", "GET"])
def atualizar_produtos_main():
    try:
        db_connection = DatabaseConnection()
        atualizaprodutos = AtualizaProdutos(db_connection)
        cadastroprodutos = CadastroProdutos(db_connection)   
        codigo_produto = request.form.get("codigo")
        info_produto = atualizaprodutos.get_product_info(codigo_produto)
        fornecedores, marcas = cadastroprodutos.busca_fornecedores_marcas()

        return render_template("atualiza-produtos.html", info_produto=info_produto, fornecedores=fornecedores, marcas=marcas)
    
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    
@app.route('/imagem/<int:id>')
def get_image(id):
    db_connection = DatabaseConnection()
    query_imagem = "SELECT foto FROM produtos WHERE id =%s"
    result_imagem = db_connection.execute_query(query_imagem, params=(id,))
    if result_imagem is None:
        return "Imagem não encontrada.", 404  # Retorna uma mensagem se não encontrar a imagem

    imagem = result_imagem[0][0]
    
    return imagem, 200, {'Content-Type': 'image/jpeg'}

@app.route("/atualizar-produtos", methods=["POST", "GET"])
def atualizar_produto():
    db_connection = DatabaseConnection()
    db_connection.connect()

    id_produto = request.form.get("idproduto")
    nome_produto = request.form.get("input_nome_produto")
    marca_produto = request.form.get("input_marca")
    fornecedor_produto = request.form.get("input_fornecedor")
    data_validade_produto = request.form.get("input_data_validade")
    qtd_estoque_produto = request.form.get("input_quantidade")
    valor_unitario_produto = float(str(request.form.get("input_valor_unitario")).replace(",","."))
    peso_produto = request.form.get("input_peso")
    custo_produto = float(str(request.form.get("input_custo_aquisicao")).replace(",",".")) if request.form.get("input_custo_aquisicao") else 0
    foto_produto = request.files.get('imagem_produto')

    query_atualizar_produto = """select                            
                            id                          
                            from fornecedores f 
                            where nome = %s
                            order by id desc"""
    
    result_consulta_fornecedor = db_connection.execute_query(query_atualizar_produto, params=(fornecedor_produto,))

    if len(result_consulta_fornecedor) > 0:
        codigo_fornecedor = result_consulta_fornecedor[0][0]
    else:
        codigo_fornecedor = 0

    if foto_produto:
        imagem_binaria = foto_produto.read()
        query_update_produto = """UPDATE `tr-sale-system`.produtos
        SET nome = %s, id_fornecedor = %s, qtd_estoque = %s, valor_unitario = %s, marca = %s, data_validade = %s, peso = %s, custo_aquisicao = %s, foto = %s
        WHERE id = %s;"""
        result_update_produto = db_connection.execute_query(query_update_produto, False, params=(nome_produto, codigo_fornecedor, qtd_estoque_produto, valor_unitario_produto, marca_produto, data_validade_produto, peso_produto, custo_produto, imagem_binaria, id_produto))
    else:
        query_update_produto = """
                UPDATE `tr-sale-system`.produtos
                SET nome = %s, id_fornecedor = %s, qtd_estoque = %s, valor_unitario = %s, marca = %s, data_validade = %s, peso = %s, custo_aquisicao = %s
                WHERE id = %s;
                """
        result_update_produto = db_connection.execute_query(query_update_produto, False, params=(nome_produto, codigo_fornecedor, qtd_estoque_produto, valor_unitario_produto, marca_produto, data_validade_produto, peso_produto, custo_produto, id_produto))

    time.sleep(2)
    return redirect(url_for('consulta_produtos'))



@app.route('/removeProduct/<int:idproduto>', methods=["POST"])
def remover_produto(idproduto):
    db_connection = DatabaseConnection()
    db_connection.connect()
    query_remove = "DELETE FROM `tr-sale-system`.produtos WHERE id= %s"
    result_imagem = db_connection.execute_query(query_remove, False, (idproduto,))
    result_imagem.close()
    return redirect(url_for('consulta_produtos'))

class AtualizaProdutos:
    def __init__(self, db_connection) -> None:
        self.db_connection = db_connection


    def get_product_info(self, codigo_produto):
        query_product_info = f"""select
                                p.id,
                                p.nome,
                                coalesce(f.nome, '') as fornecedor,
                                p.qtd_estoque,
                                REPLACE(FORMAT(p.valor_unitario  , 2), '.', ',') AS valorunitario,
                                coalesce(p.marca,''),
                                p.data_validade,
                                coalesce(p.peso, ''),
                                coalesce(REPLACE(FORMAT(p.custo_aquisicao , 2), '.', ','),'') AS custoaquisicao,
                                p.foto 
                                from produtos p
                                left join fornecedores f on f.id = p.id_fornecedor
                                where p.id = {codigo_produto}
                        """
        result_product_info = self.db_connection.execute_query(query_product_info)
        
        return result_product_info[0]


@app.route("/atualizar-cliente-main", methods=["POST", "GET"])
def atualizar_clientes_main():
    try:
        db_connection = DatabaseConnection()
        atualizaclientes = AtualizaClientes(db_connection)
        codigo_cliente = request.form.get("codigo")
        info_cliente = atualizaclientes.get_cliente_info(codigo_cliente)
        return render_template("atualiza-cliente.html", info_cliente=info_cliente)
    
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro

@app.route("/atualizar-cliente", methods=["POST", "GET"])
def atualizar_cliente():
    db_connection = DatabaseConnection()
    db_connection.connect()

    id_cliente = request.form.get("codigo")
    nome_cliente = request.form.get("input_nome_cliente")
    cpf_cnpj = request.form.get("input_cpfcnpj_cliente")
    email = request.form.get("input_email_cliente")
    telefone = request.form.get("input_telefone_cliente")
    endereco = request.form.get("input_endereco_cliente")
    observacoes = request.form.get("input_observacoes_cliente")

    query_atualiza_cliente = """UPDATE `tr-sale-system`.clientes
    SET nome=%s, cpf_cnpj=%s, email=%s, telefone=%s, endereco=%s, observacoes=%s
    WHERE id=%s;
        """
    # Execute a query com os valores como parâmetros
    result_atualizar_cliente = db_connection.execute_query(query_atualiza_cliente, False, (nome_cliente, cpf_cnpj, email, telefone, endereco, observacoes, id_cliente))
    result_atualizar_cliente.close()
    time.sleep(2)
    return redirect(url_for('consulta_clientes'))


@app.route('/removeCliente/<int:idcliente>', methods=["POST"])
def remover_cliente(idcliente):
    db_connection = DatabaseConnection()
    db_connection.connect()

    query_remover_cliente = "DELETE FROM `tr-sale-system`.clientes WHERE id= %s"
    result_cliente_info = db_connection.execute_query(query_remover_cliente, False, (idcliente,))

    result_cliente_info.close()
    return redirect(url_for('consulta_clientes'))



class AtualizaClientes:
    def __init__(self, db_connection) -> None:
        self.db_connection = db_connection

    def get_cliente_info(self, codigo_cliente):
        query_cliente_info = """SELECT id, 
                            coalesce(nome,''), 
                            coalesce(email,''), 
                            coalesce(telefone,''), 
                            coalesce(cpf_cnpj,''), 
                            coalesce(observacoes,''), 
                            coalesce(endereco, '')
                            FROM `tr-sale-system`.clientes
                            where id = %s
                        """
        result_cliente_info = self.db_connection.execute_query(query_cliente_info, params=(codigo_cliente,))
        #result_cliente_info.close()
        return result_cliente_info[0]







@app.route("/atualizar-fornecedor-main", methods=["POST", "GET"])
def atualizar_fornecedor_main():
    try:
        codigo_fornecedor = request.form.get("codigo")
        db_connection = DatabaseConnection()
        atualizafornecedores = AtualizaFornecedores(db_connection)
        info_fornecedor = atualizafornecedores.get_fornecedor_info(codigo_fornecedor)
        return render_template("atualiza-fornecedor.html", info_fornecedor=info_fornecedor)
    
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    
@app.route("/atualizar-fornecedor", methods=["POST", "GET"])
def atualizar_fornecedor():
    db_connection = DatabaseConnection()
    db_connection.connect()

    id_fornecedor = request.form.get("codigo")
    nome_fornecedor = request.form.get("input_nome_fornecedor")
    cpf_cnpj = request.form.get("input_cpfcnpj_fornecedor")
    email = request.form.get("input_email_fornecedor")
    telefone = request.form.get("input_telefone_fornecedor")
    endereco = request.form.get("input_endereco_fornecedor")
    observacoes = request.form.get("input_observacoes_fornecedor")

    query_atualizar_fornecedor = """UPDATE `tr-sale-system`.fornecedores
                SET nome=%s, cpf_cnpj=%s, email=%s, telefone=%s, endereco=%s, observacoes=%s
                WHERE id=%s;
        """
    # Execute a query com os valores como parâmetros
    result_fornecedor_info = db_connection.execute_query(query_atualizar_fornecedor, False, (nome_fornecedor, cpf_cnpj, email, telefone, endereco, observacoes, id_fornecedor))
    time.sleep(2)
    return redirect(url_for('consulta_fornecedores'))


@app.route('/removeFornecedor/<int:idfornecedor>', methods=["POST"])
def remover_fornecedor(idfornecedor):
    db_connection = DatabaseConnection()
    db_connection.connect()
    query_remover_fornecedor = "DELETE FROM `tr-sale-system`.fornecedores WHERE id= %s"
    result_fornecedor_info = db_connection.execute_query(query_remover_fornecedor, False, (idfornecedor,))

    return redirect(url_for('consulta_fornecedores'))


class AtualizaFornecedores:
    def __init__(self, db_connection) -> None:
        self.db_connection = db_connection

    def get_fornecedor_info(self, codigo_fornecedor):
        query_fornecedor_info = """SELECT id, 
                            coalesce(nome,''), 
                            coalesce(cpf_cnpj,''), 
                            coalesce(email,''), 
                            coalesce(telefone,''), 
                            coalesce(endereco,''), 
                            coalesce(observacoes,'')
                            FROM `tr-sale-system`.fornecedores
                            where id = %s
                        """
        result_fornecedor_info = self.db_connection.execute_query(query_fornecedor_info, params=(codigo_fornecedor,))
        return result_fornecedor_info[0]