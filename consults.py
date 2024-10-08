from flask import render_template, request, redirect, url_for
from datetime import date
from app_conf import app
from database import DatabaseConnection


############ TELA PRINCIPAL DA CONSULTA ##############
@app.route("/consulta")
def consulta_main():
    return render_template("consulta.html")


@app.route("/consulta-vendas")
def consulta_vendas():
    db_connection = DatabaseConnection()
    consultavendas = ConsultaVendas(db_connection)
    lista_produtos = consultavendas.consulta_produtos()
    vendas_mes = consultavendas.consulta_vendas_mes()
    produto = ''
    datainicial = date.today().strftime("%Y-%m-%d")
    datafinal = date.today().strftime("%Y-%m-%d")
    return render_template("consulta-vendas.html", vendas_mes=vendas_mes, datainicial=datainicial, datafinal=datafinal, produto=produto, lista_produtos=lista_produtos)

@app.route("/consulta-vendas-filtros" ,methods=["POST","GET"])
def consulta_vendas_filtros():
    db_connection = DatabaseConnection()
    db_connection.connect()
    datainicial = request.form.get("datainicio") 
    datafinal = request.form.get("datafim")  
    produto = request.form.get("filtro_produto")

    if produto:
        query = f"""
                select
                    v.id,
                    DATE_FORMAT(v.data_venda, '%d/%m/%Y') AS data_formatada,
                    v.forma_pagamento,
                    c2.nome,
                    REPLACE(FORMAT(v.total_venda , 2), '.', ',') AS campo_formatado,
                    status_venda
                    from vendas v 
                    left join clientes c2 on v.id_cliente  = c2.id
                    left join vendas_produtos vp on vp.id_venda = v.id
                    where
                    data_venda between '{datainicial}' and '{datafinal}'
                    and vp.nome_produto = '{produto}'
                    group by v.id
                    ORDER BY v.id desc
                """
    else:
        query = f"""
            select
                v.id,
                DATE_FORMAT(v.data_venda, '%d/%m/%Y') AS data_formatada,
                v.forma_pagamento,
                c2.nome,
                REPLACE(FORMAT(v.total_venda , 2), '.', ',') AS campo_formatado,
                status_venda
                from vendas v 
                left join clientes c2 on v.id_cliente  = c2.id
                left join vendas_produtos vp on vp.id_venda = v.id
                where
                data_venda between '{datainicial}' and '{datafinal}'                
                group by v.id
                ORDER BY v.id desc
            """

    result_vendas_filtros = db_connection.execute_query(query)
    
    consultavendas = ConsultaVendas(db_connection)
    lista_produtos = consultavendas.consulta_produtos()
    return render_template("consulta-vendas.html", 
                            vendas_mes=result_vendas_filtros, 
                            lista_produtos=lista_produtos, 
                            produto=produto, 
                            datainicial=datainicial, 
                            datafinal=datafinal)


########################## VISUALIZAR VENDA ####################################
@app.route("/visualizar-venda-main", methods=["POST", "GET"])
def visualizar_venda_main():
    try:
        dbconnection = DatabaseConnection()
        consultavendas = ConsultaVendas(dbconnection)
        codigo_venda = request.form.get("codigo")        
        info_venda, info_produtos = consultavendas.get_venda_info(codigo_venda)
        return render_template("visualizar-venda.html", info_venda=info_venda, info_produtos=info_produtos)
    
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro

@app.route('/cancelaVenda/<int:idvenda>/<string:motivo>', methods=["POST"])
def cancelar_venda(idvenda, motivo):
    db_connection = DatabaseConnection()
    db_connection.connect() 
    status_venda = '❌ Cancelada'

    query_cancelar = "UPDATE `tr-sale-system`.vendas set status_venda = %s, motivo_cancelamento = %s WHERE id= %s"
    result_cancelar_venda = db_connection.execute_query(query_cancelar, False, params=(status_venda, motivo, idvenda,))

    query_produtos = """SELECT 
                            id_produto,
                            quantidade
                            FROM `tr-sale-system`.vendas_produtos
                            where id_venda = %s
                        """
    result_produtos = db_connection.execute_query(query_produtos, params=(idvenda,))

    for produto in result_produtos:
        print(produto[1],'aaa', produto[0])
        query_update_produto = f"""
            UPDATE produtos set qtd_estoque = qtd_estoque - {int(produto[1])} where id = {int(produto[0])}
        """
        result_update_produto = db_connection.execute_query(query_update_produto, False)

    return redirect(url_for('consulta_vendas'))

class ConsultaVendas:
    def __init__(self, db_connection) -> None:
        self.db_connection = db_connection

    def consulta_produtos(self):
        query_produtos = f"""select                           
                                p.nome                           
                                from produtos p                            
                                ORDER BY p.id desc
                        """

        result_produtos = self.db_connection.execute_query(query_produtos)
        return result_produtos
    

    def consulta_vendas_mes(self):
        db_connection = DatabaseConnection()
        db_connection.connect() 

        query = f"""select
                                v.id,
                                DATE_FORMAT(v.data_venda, '%d/%m/%Y') AS data_formatada,
                                v.forma_pagamento,
                                c2.nome,
                                REPLACE(FORMAT(v.total_venda , 2), '.', ',') AS campo_formatado,
                                status_venda
                                from vendas v 
                                left join clientes c2 on v.id_cliente  = c2.id                            
                                ORDER BY v.id desc
                        """
        
        result_vendas_mes = self.db_connection.execute_query(query)

        return result_vendas_mes

    def get_venda_info(self, codigo_venda):
        db_connection = DatabaseConnection()
        db_connection.connect() 
        query_vendas = """SELECT 
                    v.id,
                    DATE_FORMAT(v.data_venda, '%d/%m/%Y'),
                    DATE_FORMAT(v.data_entrega, '%d/%m/%Y'),
                    v.forma_pagamento, 
                    REPLACE(FORMAT(v.taxa_entrega , 2), '.', ','), 
                    v.endereco_entrega, 
                    c.nome, 
                    REPLACE(FORMAT(v.desconto , 2), '.', ','), 
                    v.observacoes,
                    REPLACE(FORMAT(v.total_venda  , 2), '.', ','),
                    v.status_venda                                    
                    FROM `tr-sale-system`.vendas v
                    left join clientes c on c.id = v.id_cliente 
                    where v.id = %s;
                        """
        
        query_produtos = """SELECT 
                            nome_produto, 
                            quantidade, 
                            REPLACE(FORMAT(valor_unitario  , 2), '.', ',') AS campo_formatado,
                            REPLACE(FORMAT(quantidade * valor_unitario , 2), '.', ',') AS campo_formatado2,
                            (select REPLACE(FORMAT(sum(quantidade * valor_unitario) , 2), '.', ',') from vendas_produtos vp2 where id_venda = %s) as subtotal_produtos 
                            FROM `tr-sale-system`.vendas_produtos
                            where id_venda = %s
                        """

        result_vendas = db_connection.execute_query(query_vendas, params=(codigo_venda, ))
        result_produtos = db_connection.execute_query(query_produtos, params=(codigo_venda, codigo_venda,))

        return result_vendas[0], result_produtos

























############ CONSULTA PRODUTOS ##############

@app.route("/consulta-produtos")
def consulta_produtos():
    db_connection = DatabaseConnection()
    consultaprodutos = ConsultaProdutos(db_connection)
    produtos_cadastrados = consultaprodutos.consulta_produtos_geral()
    return render_template("consulta-produtos.html", produtos_cadastrados=produtos_cadastrados)

class ConsultaProdutos:
    def __init__(self, db_connection) -> None:
        self.db_connection = db_connection

    def consulta_produtos_geral(self):
        query = f"""select
                                p.id,
                                p.nome,
                                coalesce(f.nome, ''),
                                p.qtd_estoque, 
                                REPLACE(FORMAT(p.valor_unitario  , 2), '.', ',') AS campo_formatado                            
                                from produtos p
                                left join fornecedores f on p.id_fornecedor = f.id 
                                ORDER BY p.id desc
                        """
        
        result_produtos_geral = self.db_connection.execute_query(query)
        return result_produtos_geral
    


############ CONSULTA CLIENTES ##############
@app.route("/consulta-clientes")
def consulta_clientes():
    db_connection = DatabaseConnection()
    consultaclientes = ConsultaClientes(db_connection)
    clientes_cadastrados = consultaclientes.consulta_clientes_geral()
    return render_template("consulta-clientes.html", clientes_cadastrados=clientes_cadastrados)

class ConsultaClientes:
    def __init__(self, db_connection) -> None:
        self.db_connection = db_connection

    def consulta_clientes_geral(self):
        query = f"""select
                                id,
                                nome,
                                coalesce(endereco, ''),
                                coalesce(email, ''),
                                telefone,
                                cpf_cnpj
                                from clientes c 
                                order by id desc
                        """
        result_clientes_geral = self.db_connection.execute_query(query)
        return result_clientes_geral
    




############ CONSULTA FORNECEDORES ##############
@app.route("/consulta-fornecedores")
def consulta_fornecedores():
    db_connection = DatabaseConnection()
    consultafornecedores = ConsultaFornecedores(db_connection)
    fornecedores_cadastrados = consultafornecedores.consulta_fornecedores_geral()
    return render_template("consulta-fornecedores.html", fornecedores_cadastrados=fornecedores_cadastrados)


class ConsultaFornecedores:
    def __init__(self, db_connection) -> None:
        self.db_connection = db_connection

    def consulta_fornecedores_geral(self):
        query = f"""select
                                id,
                                nome,
                                coalesce(cpf_cnpj, ''),
                                coalesce(telefone, ''),
                                coalesce(email, ''),
                                coalesce(endereco, '') 
                                from fornecedores f 
                                order by id desc
                        """
        result_fornecedores_geral = self.db_connection.execute_query(query)
        return result_fornecedores_geral