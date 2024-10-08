from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime, date
import os
from database import DatabaseConnection
from app_conf import app

############ VARIAVEIS GLOBAIS ##############
data_atual = date.today().strftime("%Y-%m-%d")
produtos = []
list_sale_infos = []

def format_value(value):
    return str(format(value, '.2f')).replace(".", ",")

def format_value_visual(value):
    return str(format(value, '.2f')).replace(".", ",")


@app.route('/nova_venda', methods=["GET", "POST"])
def nova_venda():  
    db_connection = DatabaseConnection()
    db_connection.connect() 
    novavenda = NewSale(db_connection)

    total_prods = novavenda.total_produtos()
    lista_produtos = novavenda.consulta_produtos()
    nvenda = novavenda.consulta_nvenda()
    clientes = novavenda.consulta_clientes()
    return render_template("new_sale.html", 
                        data_atual=data_atual, 
                        produtos=produtos, 
                        total_prods=total_prods, 
                        lista_produtos=lista_produtos, 
                        nvenda=nvenda, 
                        clientes=clientes)


class NewSale:
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

    def consulta_nvenda(self):
        query_nvenda = f"""select                           
                                    (max(id) + 1) as proximo_id 
                                    from vendas v         
                                """
        
        result_nvenda = self.db_connection.execute_query(query_nvenda)
        return result_nvenda
    

    def consulta_clientes(self):
        query_clientes = f"""select                           
                                        nome
                                        from clientes         
                                    """
        result_clientes = self.db_connection.execute_query(query_clientes)
        return result_clientes

    def total_produtos(self):
        total_prods = 0
        try:
            for i in range(len(produtos)):
                total_prods += round((int(produtos[i][2]) * float(str(produtos[i][3]).replace(",","."))),2)
        except Exception as e:
            print(e)
            total_prods = 0

        return format_value(total_prods)


    @app.route('/buscar_cliente/<nome>', methods=['GET'])
    def buscar_cliente(nome):

        db_connection = DatabaseConnection()
        db_connection.connect() 

        query_find_client = f"""select 
                    id,
                    cpf_cnpj, 
                    telefone 
                    from clientes c
                    where nome = '{nome}'
                """
            
        
        result_clientes = db_connection.execute_query(query_find_client)

        if len(result_clientes) > 0:        
            return jsonify(success=True, idcliente=result_clientes[0][0], cpfcnpj=result_clientes[0][1], telefone=result_clientes[0][2])
        else:       
            return jsonify(success=True, idcliente='0', cpfcnpj='', telefone='')


    @app.route('/buscar_valor_unitario/<nome>', methods=['GET'])
    def buscar_valor_unitario(nome):
        db_connection = DatabaseConnection()
        db_connection.connect() 

        query_unit_value = f"""select
                                id,
                                REPLACE(FORMAT(valor_unitario  , 2), '.', ',') AS campo_formatado   
                                from produtos
                                where nome = '{nome}'
                        """
        
        result_unit_value = db_connection.execute_query(query_unit_value)

        if len(result_unit_value) > 0:   
            return jsonify(success=True, id_produto=result_unit_value[0][0], valor_unitario=result_unit_value[0][1])
        else:
            return jsonify(success=True, id_produto='0', valor_unitario='')


    def total_vendas(self, taxaentrega, desconto):
        total_prod = self.total_produtos()
        total_venda = 0  
        try:
            total_venda = round(float(str(total_prod).replace(",",".")) + (float(str(taxaentrega).replace(",",".")) - float(str(desconto).replace(",","."))),2)
        except Exception as e:
            print(e)
            total_venda = 0
        return format(total_venda, '.2f')


    @app.route('/add_product', methods=['POST'])
    def add_product():    
        product_id = request.form.get('idproduto')
        product_name = request.form.get('produto')
        product_qtd = request.form.get('quantidade')
        product_valor_unit = request.form.get('valorunitario')
        total_unitario = str(format(float(request.form.get('total_unitario')), '.2f')).replace(".",",")
        
        if product_name and product_qtd and product_valor_unit:
            produtos.append([product_id, product_name, product_qtd, product_valor_unit, total_unitario])
        print(produtos)
        return redirect(url_for('nova_venda'))


    @app.route('/remove/<int:index>', methods=['POST'])
    def remove_product(index):
        if 0 <= index < len(produtos):
            produtos.pop(index)
        return redirect(url_for('nova_venda'))

    @app.route('/clear_products', methods=["POST"])
    def clear_products():    
        produtos.clear() # Limpa a lista de produtos
        return render_template('list-products.html', produtos=produtos)


    @app.route('/list-products')
    def list_products():    
        return render_template('list-products.html', produtos=produtos)


@app.route('/preview-resume-sale', methods=['POST', 'GET'])
def preview_resume_sale():
    try:
        db_connection = DatabaseConnection()
        newsale = NewSale(db_connection)
        total_produtos = newsale.total_produtos()

        product_taxa = request.form.get('valortaxa')
        product_desconto = request.form.get('valordesconto')

        try:            
            product_desconto = format(float(str(request.form.get('valordesconto').replace(",","."))), '.2f')
        except:            
            product_desconto = 0

        try:
            product_taxa = format(float(str(request.form.get('valortaxa').replace(",","."))), '.2f')
        except:
            product_taxa = 0

        data_venda = request.form.get("data_venda") 
        nvenda = request.form.get("nvenda")        
        nome_cliente = request.form.get("nome_cliente")
        forma_pagamento = request.form.get("forma_pagamento")
        endereco_entrega = request.form.get("endereco_entrega")

        id_cliente = request.form.get("id_cliente")
        cpf_cnpj = request.form.get("cpf_cnpj")
        telefone = request.form.get("telefone")
        observacoes = request.form.get("observacoes")
        data_entrega = request.form.get("data_entrega")
        
        total_venda = newsale.total_vendas(product_taxa, product_desconto)

        return jsonify({
            'nvenda': nvenda,
            'data_venda': data_venda,
            'nome_cliente': nome_cliente,
            'forma_pagamento': forma_pagamento,
            'endereco_entrega': endereco_entrega,
            'total_prods': total_produtos,
            'product_taxa': str(product_taxa).replace(".",","),
            'product_desconto': str(product_desconto).replace(".",","),
            'total_venda': str(total_venda).replace(".",","),
            'id_cliente': id_cliente,
            'cpf_cnpj': cpf_cnpj,
            'telefone': telefone,
            'observacoes': observacoes,
            'data_entrega': data_entrega
        })

    except Exception as e:
        print("Erro no processamento:", str(e))
        return jsonify({"error": "Server error"}), 500


@app.route('/show-resume-sale', methods=['POST', 'GET'])
def show_resume_sale():
    try:
        if request.method == 'POST':
            nvenda = request.form.get('nvenda')
            data_venda = request.form.get('data_venda')
            nome_cliente = request.form.get('nome_cliente')
            forma_pagamento = request.form.get('forma_pagamento')
            endereco_entrega = request.form.get('endereco_entrega')
            total_prods = request.form.get('total_prods')
            taxaentrega = request.form.get('product_taxa')
            desconto = request.form.get('product_desconto')
            total_venda = request.form.get('total_venda')
            id_cliente = request.form.get('id_cliente')
            cpf_cnpj = request.form.get('cpf_cnpj')
            telefone = request.form.get('telefone')
            observacoes = request.form.get('observacoes')
            data_entrega = request.form.get('data_entrega')
            list_sale_infos.clear()
            list_sale_infos.append([nvenda, datetime.strptime(data_venda, '%Y-%m-%d').strftime("%d/%m/%Y"), nome_cliente, forma_pagamento, endereco_entrega, total_prods, taxaentrega, desconto, total_venda, id_cliente, cpf_cnpj, telefone, observacoes, data_entrega])

            return redirect('/show-resume-sale')

        elif request.method == 'GET':
            return render_template('/resume_sale_teste.html', 
                nvenda=list_sale_infos[0][0], 
                data_venda=list_sale_infos[0][1], 
                nome_cliente=list_sale_infos[0][2], 
                forma_pagamento=list_sale_infos[0][3],
                endereco_entrega=list_sale_infos[0][4], 
                total_prods=list_sale_infos[0][5],
                taxaentrega=list_sale_infos[0][6],
                desconto=list_sale_infos[0][7],
                total_venda=list_sale_infos[0][8],
                id_cliente = list_sale_infos[0][9],
                cpf_cnpj = list_sale_infos[0][10],
                telefone = list_sale_infos[0][11],
                observacoes = list_sale_infos[0][12],
                data_entrega = list_sale_infos[0][13],
                produtos=produtos)
        
    except Exception as e:
        print("Erro no processamento:", str(e))
        return jsonify({"error": "Server error"}), 500


@app.route("/salvar-venda", methods=["POST", "GET"])
def salvar_venda():
    
    db_connection = DatabaseConnection()
    db_connection.connect()
    newsale = NewSale(db_connection)

    data_venda = datetime.strptime(request.form.get("data_venda"), '%d/%m/%Y').strftime('%Y-%m-%d')
    data_entrega = request.form.get("data_entrega")
    metodo_pagamento = request.form.get("metodo_pagamento")
    endereco_entrega = request.form.get("endereco_entrega")
    taxa_entrega = format(float(str(request.form.get("taxa_entrega")).replace(",",".")), '.2f')
    desconto = format(float(str(request.form.get("desconto")).replace(",",".")), '.2f')
    observacoes = request.form.get("observacoes")
    idcliente = request.form.get("idcliente")
    nome = request.form.get("nome")
    cpfcnpj = request.form.get("cpfcnpj")
    telefone = request.form.get("telefone")
    total_venda = newsale.total_vendas(taxa_entrega, desconto)
    status_venda = '✅ Finalizada'
    

    if idcliente == '0':
        query = """
            INSERT INTO clientes (nome, cpf_cnpj, telefone) VALUES (%s, %s, %s)
        """
        save_client = db_connection.execute_query(query, False, (nome, cpfcnpj, telefone))


        ultimo_id_cliente = save_client.lastrowid
    else:
        ultimo_id_cliente = idcliente

    query_save_venda = """
            INSERT INTO `tr-sale-system`.vendas
            (data_venda, data_entrega, forma_pagamento, taxa_entrega, endereco_entrega, id_cliente, desconto, observacoes, total_venda, status_venda)
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
    
    save_venda = db_connection.execute_query(query_save_venda, 
                                            False, 
                                            (data_venda, 
                                            data_entrega, 
                                            metodo_pagamento, 
                                            taxa_entrega, 
                                            endereco_entrega, 
                                            ultimo_id_cliente, 
                                            desconto, 
                                            observacoes, 
                                            total_venda, 
                                            status_venda))

    ultimo_id_venda = save_venda.lastrowid

    for produto in produtos:
        id_produto = 0
        if produto[0] == '0':
            caminho_imagem = os.path.join(os.getcwd(), 'static', 'no-photo.png')
            with open(caminho_imagem, 'rb') as file:        
                imagem_binaria = file.read()
            query_save_produtos = """INSERT INTO `tr-sale-system`.produtos
                (nome, id_fornecedor, qtd_estoque, valor_unitario, foto, data_validade)
                VALUES(%s, %s, %s, %s, %s , %s);"""
            save_produtos = db_connection.execute_query(query_save_produtos, 
                                                        False, 
                                                        (produto[1], 
                                                        0, 
                                                        1000, 
                                                        float(str(produto[3]).replace(",",".")),
                                                        imagem_binaria, 
                                                        datetime.strptime('2029-12-31', '%Y-%m-%d')))
            id_produto = save_produtos.lastrowid
        else:
            id_produto = produto[0]
        


        query_save_venda_produtos = """
                INSERT INTO `tr-sale-system`.vendas_produtos
                (id_produto, nome_produto, quantidade, valor_unitario, id_venda)
                VALUES(%s, %s, %s, %s, %s);
            """
        save_venda_produtos = db_connection.execute_query(query_save_venda_produtos, 
                                                            False, 
                                                            (id_produto, 
                                                            produto[1], 
                                                            produto[2], 
                                                            float(str(produto[3]).replace(",",".")), 
                                                            ultimo_id_venda))
        


        query_update_estoque_produto = f"""
                UPDATE `tr-sale-system`.produtos
                SET qtd_estoque= qtd_estoque - {produto[2]}
                WHERE id={id_produto};                
            """
        
        save_update_estoque_produto = db_connection.execute_query(query_update_estoque_produto, 
                                                                    False)
    db_connection.close()
    return redirect(url_for('nova_venda'))