from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from datetime import datetime, date
import mysql.connector
import calendar
import time
import os
import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go


import reports

app = Flask(__name__)

app.config['FLASK_ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TESTING'] = True


############ VARIAVEIS GLOBAIS ##############
data_atual = date.today().strftime("%Y-%m-%d")
produtos = []


############ TELA INICIAL ##############
@app.route('/', methods=["GET", "POST"])
def main():      
    valores_mensal = get_values_main()
    total_mensal = str(format(valores_mensal[0], '.2f')).replace(".",",")
    total_clientes = valores_mensal[1]
    ticket_medio = str(format(valores_mensal[2], '.2f')).replace(".",",")
    variacao_mensal = str(format(valores_mensal[3], '.2f')).replace(".",",")
    return render_template("index.html", total_mensal=total_mensal, total_clientes=total_clientes, ticket_medio=ticket_medio, variacao_mensal=variacao_mensal)

def get_values_main():
    ultimo_dia_mes = calendar.monthrange(date.today().year, date.today().month)[1]

    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    mycursor = mydb.cursor()
    mycursor.execute(f"""select
                        sum(total_venda),
                        count( distinct(id_cliente)),
                        avg(total_venda),
                        coalesce((select sum(total_venda) from vendas where month(data_venda) = '{date.today().month}'),0) - coalesce((select sum(total_venda) from vendas where month(data_venda) = '{date.today().month -1}'),0) as variacao
                        from vendas v 
                        where data_venda between '{date.today().year}-{date.today().month}-01' and '{date.today().year}-{date.today().month}-{ultimo_dia_mes}'
                    """)
    myresult = mycursor.fetchall()

    return myresult[0]


############ NOVA VENDA ##############


@app.route('/nova_venda', methods=["GET", "POST"])
def nova_venda():  
    # Se estiver fora da função
    total_prods = total_produtos()
    lista_produtos, nvenda, clientes = consulta_produtos_nvenda_clientes()    
    return render_template("new_sale.html", data_atual=data_atual, produtos=produtos, total_prods=total_prods, lista_produtos=lista_produtos, nvenda=nvenda, clientes=clientes)


def consulta_produtos_nvenda_clientes():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    mycursor_produtos = mydb.cursor()
    mycursor_produtos.execute(f"""select                           
                            p.nome                           
                            from produtos p                            
                            ORDER BY p.id desc
                    """)
    myresult_produtos = mycursor_produtos.fetchall()

    mycursor_nvenda = mydb.cursor()
    mycursor_nvenda.execute(f"""select                           
                                    (max(id) + 1) as proximo_id 
                                    from vendas v         
                                """)
    myresult_nvenda = mycursor_nvenda.fetchall()

    mycursor_clientes = mydb.cursor()
    mycursor_clientes.execute(f"""select                           
                                    nome
                                    from clientes         
                                """)
    myresult_clientes = mycursor_clientes.fetchall()

    return myresult_produtos, myresult_nvenda, myresult_clientes


@app.route('/buscar_cliente/<nome>', methods=['GET'])
def buscar_cliente(nome):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )
    query = f"""select 
                id,
                cpf_cnpj, 
                telefone 
                from clientes c
                where nome = '{nome}'
            """
        
    
    mycursor_clientes = mydb.cursor()
    mycursor_clientes.execute(query)
    myresult = mycursor_clientes.fetchall()

    if len(myresult) > 0:        
        return jsonify(success=True, idcliente=myresult[0][0], cpfcnpj=myresult[0][1], telefone=myresult[0][2])
    else:       
        return jsonify(success=True, idcliente='0', cpfcnpj='', telefone='')


@app.route('/buscar_valor_unitario/<nome>', methods=['GET'])
def buscar_valor_unitario(nome):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    mycursor_clientes = mydb.cursor()
    mycursor_clientes.execute(f"""select
                            id,
                            REPLACE(FORMAT(valor_unitario  , 2), '.', ',') AS campo_formatado   
                            from produtos
                            where nome = '{nome}'
                    """)
    myresult = mycursor_clientes.fetchall()
    
    if len(myresult) > 0:   
        return jsonify(success=True, id_produto=myresult[0][0], valor_unitario=myresult[0][1])
    else:
        return jsonify(success=True, id_produto='0', valor_unitario='')

def total_produtos():
    total_prods = 0
    try:
        for i in range(len(produtos)):
            total_prods += round((int(produtos[i][2]) * float(str(produtos[i][3]).replace(",","."))),2)
    except Exception as e:
        print(e)
        total_prods = 0

    return format(total_prods, '.2f')

def total_vendas(taxaentrega, desconto):
    total_venda = 0
    total_prod = total_produtos()    
    try:
        total_venda = round(float(total_prod) + (float(str(taxaentrega).replace(",",".")) - float(str(desconto).replace(",","."))),2)
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
    print(product_name, product_qtd, product_valor_unit)
    
    if product_name and product_qtd and product_valor_unit:
        produtos.append([product_id, product_name, product_qtd, product_valor_unit, total_unitario])
    print(produtos)
    return redirect(url_for('nova_venda'))


@app.route('/remove/<int:index>', methods=['POST'])
def remove_product(index):
    if 0 <= index < len(produtos):
        produtos.pop(index)
    print(produtos) 
    return redirect(url_for('nova_venda'))



@app.route('/clear_products', methods=["POST"])
def clear_products():    
    produtos.clear() # Limpa a lista de produtos
    return render_template('list-products.html', produtos=produtos)


@app.route('/list-products')
def list_products():    
    return render_template('list-products.html', produtos=produtos)



@app.route('/resume-sale', methods=['POST', 'GET'])
def resume_sale():
    try:
        lista_produtos, nvenda, clientes = consulta_produtos_nvenda_clientes()
        
        total_prods = total_produtos()

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
        nome_cliente = request.form.get("nome_cliente")
        forma_pagamento = request.form.get("forma_pagamento")
        endereco_entrega = request.form.get("endereco_entrega")

        id_cliente = request.form.get("id_cliente")
        cpf_cnpj = request.form.get("cpf_cnpj")
        telefone = request.form.get("telefone")
        observacoes = request.form.get("observacoes")
        data_entrega = request.form.get("data_entrega")
        
        total_venda = total_vendas(product_taxa, product_desconto)
        return jsonify({
            'nvenda': nvenda[0][0],
            'data_venda': data_venda,
            'nome_cliente': nome_cliente,
            'forma_pagamento': forma_pagamento,
            'endereco_entrega': endereco_entrega,
            'total_prods': str(total_prods).replace(".",","),
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


list_test = []
@app.route('/nova-pagina', methods=['POST', 'GET'])
def nova_pagina():
    try:
        if request.method == 'POST':
            # Receber e processar os dados enviados via POST
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
            list_test.clear()
            list_test.append([nvenda, datetime.strptime(data_venda, '%Y-%m-%d').strftime("%d/%m/%Y"), nome_cliente, forma_pagamento, endereco_entrega, total_prods, taxaentrega, desconto, total_venda, id_cliente, cpf_cnpj, telefone, observacoes, data_entrega])

            return redirect('/nova-pagina')

        elif request.method == 'GET':
            # Receber e exibir dados na página com GET
            # Para demonstrar, você pode passar dados armazenados em sessão ou variáveis globais
            print(list_test[0])
            # Renderiza a nova página após o redirecionamento
            print(produtos)
            return render_template('/resume_sale_teste.html', 
                nvenda=list_test[0][0], 
                data_venda=list_test[0][1], 
                nome_cliente=list_test[0][2], 
                forma_pagamento=list_test[0][3],
                endereco_entrega=list_test[0][4], 
                total_prods=list_test[0][5],
                taxaentrega=list_test[0][6],
                desconto=list_test[0][7],
                total_venda=list_test[0][8],
                id_cliente = list_test[0][9],
                cpf_cnpj = list_test[0][10],
                telefone = list_test[0][11],
                observacoes = list_test[0][12],
                data_entrega = list_test[0][13],
                produtos=produtos)
        
    except Exception as e:
        print("Erro no processamento:", str(e))
        return jsonify({"error": "Server error"}), 500


@app.route("/salvar-venda", methods=["POST", "GET"])
def salvar_venda():
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
    total_venda = total_vendas(taxa_entrega, desconto)
    status_venda = '✅ Finalizada'
    
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    if idcliente == '0':
        cursor_salvar_cliente = mydb.cursor()
        cursor_salvar_cliente.execute("""
            INSERT INTO clientes (nome, cpf_cnpj, telefone) VALUES (%s, %s, %s)
        """, (nome, cpfcnpj, telefone))

        ultimo_id_cliente = cursor_salvar_cliente.lastrowid
    else:
        ultimo_id_cliente = idcliente

    cursor_salvar_venda = mydb.cursor()
    cursor_salvar_venda.execute("""
            INSERT INTO `tr-sale-system`.vendas
            (data_venda, data_entrega, forma_pagamento, taxa_entrega, endereco_entrega, id_cliente, desconto, observacoes, total_venda, status_venda)
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (data_venda, data_entrega, metodo_pagamento, taxa_entrega, endereco_entrega, ultimo_id_cliente, desconto, observacoes, total_venda, status_venda))

    mydb.commit()
    ultimo_id_venda = cursor_salvar_venda.lastrowid
    cursor_salvar_venda.close()

    for produto in produtos:
        cursor_salvar_venda_produtos = mydb.cursor()
        cursor_atualiza_estoque_produto = mydb.cursor()
        cursor_cadastrar_produto = mydb.cursor()
        id_produto = 0
        if produto[0] == '0':
            caminho_imagem = os.path.join(os.getcwd(), 'static', 'no-photo.png')
            with open(caminho_imagem, 'rb') as file:        
                imagem_binaria = file.read()
            query = """INSERT INTO `tr-sale-system`.produtos
                (nome, id_fornecedor, qtd_estoque, valor_unitario, foto, data_validade)
                VALUES(%s, %s, %s, %s, %s , %s);"""
            cursor_cadastrar_produto.execute(query, (produto[1], 0, 1000, float(str(produto[3]).replace(",",".")), imagem_binaria, datetime.strptime('2025-12-31', '%Y-%m-%d')))
            id_produto = cursor_cadastrar_produto.lastrowid
        else:
            id_produto = produto[0]

        cursor_salvar_venda_produtos.execute("""
                INSERT INTO `tr-sale-system`.vendas_produtos
                (id_produto, nome_produto, quantidade, valor_unitario, id_venda)
                VALUES(%s, %s, %s, %s, %s);
            """, (id_produto, produto[1], produto[2], float(str(produto[3]).replace(",",".")), ultimo_id_venda))
        
        cursor_atualiza_estoque_produto.execute(f"""
                UPDATE `tr-sale-system`.produtos
                SET qtd_estoque= qtd_estoque - {produto[2]}
                WHERE id={id_produto};                
            """)
        mydb.commit()

    cursor_cadastrar_produto.close()
    cursor_atualiza_estoque_produto.close()
    cursor_salvar_venda_produtos.close()
    return redirect(url_for('nova_venda'))

############ TELA PRINCIPAL DA CONSULTA ##############

@app.route("/consulta")
def consulta_main():
    return render_template("consulta.html")

############ CONSULTA VENDAS ##############
@app.route("/consulta-vendas")
def consulta_vendas():
    vendas_mes = consulta_vendas_mes()
    return render_template("consulta-vendas.html", vendas_mes=vendas_mes, data_atual=data_atual)


def consulta_vendas_mes():
    ultimo_dia_mes = calendar.monthrange(date.today().year, date.today().month)[1]

    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    mycursor = mydb.cursor()
    mycursor.execute(f"""select
                            v.id,
                            DATE_FORMAT(v.data_venda, '%d/%m/%Y') AS data_formatada,
                            v.forma_pagamento,
                            c2.nome,
                            REPLACE(FORMAT(v.total_venda , 2), '.', ',') AS campo_formatado,
                            status_venda
                            from vendas v 
                            left join clientes c2 on v.id_cliente  = c2.id                            
                            ORDER BY v.id desc
                    """)

    myresult = mycursor.fetchall()
    return myresult


############ CONSULTA PRODUTOS ##############

@app.route("/consulta-produtos")
def consulta_produtos():
    produtos_cadastrados = consulta_produtos_geral()
    return render_template("consulta-produtos.html", produtos_cadastrados=produtos_cadastrados)


def consulta_produtos_geral():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    mycursor = mydb.cursor()
    mycursor.execute(f"""select
                            p.id,
                            p.nome,
                            coalesce(f.nome, ''),
                            p.qtd_estoque, 
                            REPLACE(FORMAT(p.valor_unitario  , 2), '.', ',') AS campo_formatado                            
                            from produtos p
                            left join fornecedores f on p.id_fornecedor = f.id 
                            ORDER BY p.id desc
                    """)
    myresult = mycursor.fetchall()
    return myresult


############ CONSULTA CLIENTES ##############

@app.route("/consulta-clientes")
def consulta_clientes():
    clientes_cadastrados = consulta_clientes_geral()
    return render_template("consulta-clientes.html", clientes_cadastrados=clientes_cadastrados)


def consulta_clientes_geral():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    mycursor = mydb.cursor()
    mycursor.execute(f"""select
                            id,
                            nome,
                            endereco,
                            email,
                            telefone,
                            cpf_cnpj
                            from clientes c 
                            order by id desc
                    """)
    myresult = mycursor.fetchall()
    return myresult

@app.route("/consulta-fornecedores")
def consulta_fornecedores():
    fornecedores_cadastrados = consulta_fornecedores_geral()
    return render_template("consulta-fornecedores.html", fornecedores_cadastrados=fornecedores_cadastrados)


############ CONSULTA FORNECEDORES ##############


def consulta_fornecedores_geral():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    mycursor = mydb.cursor()
    mycursor.execute(f"""select
                            id,
                            nome,
                            cpf_cnpj,
                            telefone,
                            email,
                            endereco 
                            from fornecedores f 
                            order by id desc
                    """)
    myresult = mycursor.fetchall()
    return myresult

############ TELA PRINCIPAL DE CADASTROS ##############


@app.route("/cadastro")
def cadastro_main():
    return render_template("cadastro.html")


############ CONSULTA PRODUTOS ##############


@app.route("/cadastro-produtos")
def cadastro_produtos():    
    fornecedores,  marcas = busca_fornecedores_marcas()
    return render_template("cadastro-produtos.html", fornecedores=fornecedores, marcas=marcas)

def busca_fornecedores_marcas():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )
    list_forn = []
    list_marcas = []
    cursor_fornecedores = mydb.cursor()
    cursor_marcas = mydb.cursor()
    cursor_fornecedores.execute(f"""select                            
                            nome       
                            from fornecedores f
                            where nome is not null  
                            order by id desc
                    """)
    myresult = cursor_fornecedores.fetchall()

    cursor_marcas.execute(f"""select 
                            distinct(marca)
                            from produtos p  
                            where marca is not null 
                            
                    """)
    myresult2 = cursor_marcas.fetchall()

    for i in range(len(myresult)):
        list_forn.append(str(myresult[i]).split("'")[1])

    for i in range(len(myresult2)):
        list_marcas.append(str(myresult2[i]).split("'")[1])

    return list_forn, list_marcas

@app.route("/salvar-produto", methods=["POST", "GET"])
def salvar_produtos():
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

    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    cursor_codigo_fornecedor = mydb.cursor()
    query = f"""select                            
                            id                          
                            from fornecedores f 
                            where nome = '{fornecedor_produto}'
                            order by id desc"""
    
    cursor_codigo_fornecedor.execute(query)
    result_cursor_codigo_fornecedor = cursor_codigo_fornecedor.fetchall()

    if len(result_cursor_codigo_fornecedor) > 0:
        codigo_fornecedor = result_cursor_codigo_fornecedor[0][0]
    else:
        codigo_fornecedor = 0

    cursor = mydb.cursor()
    cursor.execute("""
            INSERT INTO produtos (nome, id_fornecedor, qtd_estoque, valor_unitario, marca, data_validade, peso, custo_aquisicao, foto) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (nome_produto, codigo_fornecedor, qtd_estoque_produto, valor_unitario_produto, marca_produto, data_validade_produto, peso_produto, custo_produto, imagem_binaria))

    mydb.commit()
    cursor.close()
    time.sleep(2)
    return redirect(url_for('cadastro_produtos'))



############ CONSULTA FORNECEDORES ##############


@app.route("/cadastro-fornecedores")
def cadastro_fornecedores():    
    return render_template("cadastro-fornecedores.html")


@app.route("/salvar-fornecedores", methods=["POST", "GET"])
def salvar_fornecedores():
    nome_fornecedor = request.form.get("input_nome_fornecedor")
    cpfncpj_fornecedor = request.form.get("input_cpfcnpj_fornecedor")
    email_fornecedor = request.form.get("input_email_fornecedor")
    telefone_fornecedor = request.form.get("input_telefone_fornecedor")
    endereco_fornecedor = request.form.get("input_endereco_fornecedor")
    observacoes_fornecedor = request.form.get("input_observacoes_fornecedor")

    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    cursor = mydb.cursor()
    cursor.execute("""
            INSERT INTO fornecedores (nome, cpf_cnpj, email, telefone, endereco, observacoes) VALUES (%s, %s, %s, %s, %s, %s)
        """, (nome_fornecedor, cpfncpj_fornecedor, email_fornecedor, telefone_fornecedor, endereco_fornecedor, observacoes_fornecedor))

    mydb.commit()
    cursor.close()
    time.sleep(2)
    return redirect(url_for('cadastro_fornecedores'))


############ CONSULTA CLIENTES ##############


@app.route("/cadastro-clientes")
def cadastro_clientes():    
    return render_template("cadastro-clientes.html")


@app.route("/salvar-clientes", methods=["POST", "GET"])
def salvar_clientes():
    nome_cliente = request.form.get("input_nome_cliente")
    cpfncpj_cliente = request.form.get("input_cpfcnpj_cliente")
    email_cliente = request.form.get("input_email_cliente")
    telefone_cliente = request.form.get("input_telefone_cliente")
    endereco_cliente = request.form.get("input_endereco_cliente")
    observacoes_cliente = request.form.get("input_observacoes_cliente")

    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    cursor = mydb.cursor()
    cursor.execute("""
            INSERT INTO clientes (nome, cpf_cnpj, email, telefone, endereco, observacoes) VALUES (%s, %s, %s, %s, %s, %s)
        """, (nome_cliente, cpfncpj_cliente, email_cliente, telefone_cliente, endereco_cliente, observacoes_cliente))

    mydb.commit()
    cursor.close()
    time.sleep(2)
    return redirect(url_for('cadastro_clientes'))



@app.route("/atualizar-produtos-main", methods=["POST", "GET"])
def atualizar_produtos_main():
    try:
        codigo_produto = request.form.get("codigo")
        info_produto = get_product_info(codigo_produto)
        fornecedores, marcas = busca_fornecedores_marcas()

        return render_template("atualiza-produtos.html", info_produto=info_produto, fornecedores=fornecedores, marcas=marcas)
    
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    

@app.route('/imagem/<int:id>')
def get_image(id):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )
    cursor = mydb.cursor()
    cursor.execute("SELECT foto FROM produtos WHERE id = %s", (id,))
    imagem = cursor.fetchone()
    
    if imagem is None:
        return "Imagem não encontrada.", 404  # Retorna uma mensagem se não encontrar a imagem

    imagem = imagem[0]
    cursor.close()
    return imagem, 200, {'Content-Type': 'image/jpeg'}


@app.route('/removeProduct/<int:idproduto>', methods=["POST"])
def remover_produto(idproduto):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )
    print(idproduto)
    cursor = mydb.cursor()
    query = "DELETE FROM `tr-sale-system`.produtos WHERE id= %s"
    cursor.execute(query, (idproduto,))

    mydb.commit()

    cursor.close()
    return redirect(url_for('consulta_produtos'))


def get_product_info(codigo_produto):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    mycursor = mydb.cursor()
    mycursor.execute(f"""select
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
                    """)
    myresult = mycursor.fetchall()
    return myresult[0]

@app.route("/atualizar-produtos", methods=["POST", "GET"])
def atualizar_produto():
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

    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    cursor_codigo_fornecedor = mydb.cursor()
    query = f"""select                            
                            id                          
                            from fornecedores f 
                            where nome = '{fornecedor_produto}'
                            order by id desc"""
    
    cursor_codigo_fornecedor.execute(query)
    result_cursor_codigo_fornecedor = cursor_codigo_fornecedor.fetchall()

    if len(result_cursor_codigo_fornecedor) > 0:
        codigo_fornecedor = result_cursor_codigo_fornecedor[0][0]
    else:
        codigo_fornecedor = 0

    cursor = mydb.cursor()

    if foto_produto:
        imagem_binaria = foto_produto.read()
        query = """UPDATE `tr-sale-system`.produtos
        SET nome = %s, id_fornecedor = %s, qtd_estoque = %s, valor_unitario = %s, marca = %s, data_validade = %s, peso = %s, custo_aquisicao = %s, foto = %s
        WHERE id = %s;"""

    # Execute a query com os valores como parâmetros
        cursor.execute(query, (nome_produto, codigo_fornecedor, qtd_estoque_produto, valor_unitario_produto, marca_produto, data_validade_produto, peso_produto, custo_produto, imagem_binaria, id_produto))
    else:
        query = """
                UPDATE `tr-sale-system`.produtos
                SET nome = %s, id_fornecedor = %s, qtd_estoque = %s, valor_unitario = %s, marca = %s, data_validade = %s, peso = %s, custo_aquisicao = %s
                WHERE id = %s;
                    """
        cursor.execute(query, (nome_produto, codigo_fornecedor, qtd_estoque_produto, valor_unitario_produto, marca_produto, data_validade_produto, peso_produto, custo_produto, id_produto))


    mydb.commit()
    cursor.close()
    time.sleep(2)
    return redirect(url_for('consulta_produtos'))


@app.route("/atualizar-cliente-main", methods=["POST", "GET"])
def atualizar_clientes_main():
    try:
        codigo_cliente = request.form.get("codigo")
        info_cliente = get_cliente_info(codigo_cliente)
        return render_template("atualiza-cliente.html", info_cliente=info_cliente)
    
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    


def get_cliente_info(codigo_cliente):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    mycursor = mydb.cursor()
    query = f"""SELECT id, 
                        coalesce(nome,''), 
                        coalesce(email,''), 
                        coalesce(telefone,''), 
                        coalesce(cpf_cnpj,''), 
                        coalesce(observacoes,''), 
                        coalesce(endereco, '')
                        FROM `tr-sale-system`.clientes
                        where id = {codigo_cliente}
                    """
    mycursor.execute(query)
    myresult = mycursor.fetchall()
    return myresult[0]

@app.route("/atualizar-cliente", methods=["POST", "GET"])
def atualizar_cliente():
    id_cliente = request.form.get("codigo")
    nome_cliente = request.form.get("input_nome_cliente")
    cpf_cnpj = request.form.get("input_cpfcnpj_cliente")
    email = request.form.get("input_email_cliente")
    telefone = request.form.get("input_telefone_cliente")
    endereco = request.form.get("input_endereco_cliente")
    observacoes = request.form.get("input_observacoes_cliente")

    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    cursor = mydb.cursor()
    query = """UPDATE `tr-sale-system`.clientes
    SET nome=%s, cpf_cnpj=%s, email=%s, telefone=%s, endereco=%s, observacoes=%s
    WHERE id=%s;
        """
    print(id_cliente, endereco)
    # Execute a query com os valores como parâmetros
    cursor.execute(query, (nome_cliente, cpf_cnpj, email, telefone, endereco, observacoes, id_cliente))
    mydb.commit()
    time.sleep(2)
    return redirect(url_for('consulta_clientes'))


@app.route('/removeCliente/<int:idcliente>', methods=["POST"])
def remover_cliente(idcliente):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )
    cursor = mydb.cursor()
    query = "DELETE FROM `tr-sale-system`.clientes WHERE id= %s"
    cursor.execute(query, (idcliente,))

    mydb.commit()

    cursor.close()
    return redirect(url_for('consulta_clientes'))

##############################################################################


@app.route("/atualizar-fornecedor-main", methods=["POST", "GET"])
def atualizar_fornecedor_main():
    try:
        codigo_fornecedor = request.form.get("codigo")
        
        info_fornecedor = get_fornecedor_info(codigo_fornecedor)
        print(info_fornecedor)
        return render_template("atualiza-fornecedor.html", info_fornecedor=info_fornecedor)
    
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    


def get_fornecedor_info(codigo_fornecedor):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    mycursor = mydb.cursor()
    query = f"""SELECT id, 
                        coalesce(nome,''), 
                        coalesce(cpf_cnpj,''), 
                        coalesce(email,''), 
                        coalesce(telefone,''), 
                        coalesce(endereco,''), 
                        coalesce(observacoes,'')
                        FROM `tr-sale-system`.fornecedores
                        where id = {codigo_fornecedor}
                    """
    mycursor.execute(query)
    myresult = mycursor.fetchall()
    print(myresult[0])
    return myresult[0]

@app.route("/atualizar-fornecedor", methods=["POST", "GET"])
def atualizar_fornecedor():
    id_fornecedor = request.form.get("codigo")
    nome_fornecedor = request.form.get("input_nome_fornecedor")
    cpf_cnpj = request.form.get("input_cpfcnpj_fornecedor")
    email = request.form.get("input_email_fornecedor")
    telefone = request.form.get("input_telefone_fornecedor")
    endereco = request.form.get("input_endereco_fornecedor")
    observacoes = request.form.get("input_observacoes_fornecedor")

    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    cursor = mydb.cursor()
    query = """UPDATE `tr-sale-system`.fornecedores
                SET nome=%s, cpf_cnpj=%s, email=%s, telefone=%s, endereco=%s, observacoes=%s
                WHERE id=%s;
        """
    # Execute a query com os valores como parâmetros
    cursor.execute(query, (nome_fornecedor, cpf_cnpj, email, telefone, endereco, observacoes, id_fornecedor))
    mydb.commit()
    time.sleep(2)
    return redirect(url_for('consulta_fornecedores'))


@app.route('/removeFornecedor/<int:idfornecedor>', methods=["POST"])
def remover_fornecedor(idfornecedor):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )
    cursor = mydb.cursor()
    query = "DELETE FROM `tr-sale-system`.fornecedores WHERE id= %s"
    cursor.execute(query, (idfornecedor,))

    mydb.commit()

    cursor.close()
    return redirect(url_for('consulta_fornecedores'))


@app.route("/visualizar-venda-main", methods=["POST", "GET"])
def visualizar_venda_main():
    try:
        codigo_venda = request.form.get("codigo")        
        info_venda, info_produtos = get_venda_info(codigo_venda)

        return render_template("visualizar-venda.html", info_venda=info_venda, info_produtos=info_produtos)
    
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro

def get_venda_info(codigo_venda):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )

    mycursor = mydb.cursor()
    query = f"""SELECT 
                v.id,
                DATE_FORMAT(v.data_venda, '%d/%m/%Y'),
                DATE_FORMAT(v.data_entrega, '%d/%m/%Y'),
                v.forma_pagamento, 
                v.taxa_entrega, 
                v.endereco_entrega, 
                c.nome, 
                v.desconto, 
                v.observacoes,
                REPLACE(FORMAT(v.total_venda  , 2), '.', ','),
                v.status_venda                
                FROM `tr-sale-system`.vendas v
                left join clientes c on c.id = v.id_cliente 
                where v.id = {codigo_venda};
                    """
    
    query_produtos = f"""SELECT 
                        nome_produto, 
                        quantidade, 
                        REPLACE(FORMAT(valor_unitario  , 2), '.', ',') AS campo_formatado,
                        REPLACE(FORMAT(quantidade * valor_unitario , 2), '.', ',') AS campo_formatado2
                        FROM `tr-sale-system`.vendas_produtos
                        where id_venda = {codigo_venda}
                    """

    mycursor.execute(query)
    myresult1 = mycursor.fetchall()

    mycursor.execute(query_produtos)
    myresult2 = mycursor.fetchall()

    return myresult1[0], myresult2


@app.route('/cancelaVenda/<int:idvenda>/<string:motivo>', methods=["POST"])
def cancelar_venda(idvenda, motivo):
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
    )
    print(motivo)
    status_venda = '❌ Cancelada'
    cursor = mydb.cursor()
    query = "UPDATE `tr-sale-system`.vendas set status_venda = %s, motivo_cancelamento = %s WHERE id= %s"
    cursor.execute(query, (status_venda, motivo, idvenda ))

    mydb.commit()
    cursor.close()
    return redirect(url_for('consulta_vendas'))


################################################## RELATORIOS ###########################################

@app.route("/relatorios-main", methods=["POST", "GET"])
def relatorios_main():
    try:
        return render_template("relatorios.html")
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro


@app.route("/visualizar-relatorio", methods=["POST", "GET"])
def visualiza_relatorio():
    try:
        data_inicio = request.form.get("dataInicio")
        data_fim = request.form.get("dataFim")
        if request.form.get("tipoRelatorio") == "Vendas por Período":           

            grafico_html, data_inicio, data_fim, total_vendas, total_produtos, ticket_medio, total_transacoes, vendas_periodo = reports.visualiza_relatorio_vendas_periodo(data_inicio, data_fim)

            return render_template("visualizar-relatorio-vendas-periodo.html", grafico_html=grafico_html, data_inicio=data_inicio, data_fim=data_fim, total_vendas=total_vendas, total_produtos=total_produtos, ticket_medio=ticket_medio, total_transacoes=total_transacoes, vendas_periodo=vendas_periodo)  

        elif request.form.get("tipoRelatorio") == "Produtos Mais Vendidos":
            grafico_html, data_inicio, data_fim, quantidade_total, total_produtos, tabela_produtos = reports.visualiza_relatorio_produtos_mais_vendidos(data_inicio, data_fim)

            return render_template("visualizar-relatorio-produtos-mais-vendidos.html", grafico_html=grafico_html, data_inicio=data_inicio, data_fim=data_fim,quantidade_total=quantidade_total, total_produtos=total_produtos, tabela_produtos=tabela_produtos)  
        
        elif request.form.get("tipoRelatorio") == "Estoque Crítico":
            grafico_html, quantidade_produtos_critico, list_items = reports.visualiza_relatorio_estoque_critico()

            return render_template("visualizar-relatorio-estoque-critico.html", grafico_html=grafico_html, quantidade_produtos_critico=quantidade_produtos_critico, tabela_produtos=list_items)  
        
        elif request.form.get("tipoRelatorio") == "Vendas por Cliente":
            grafico_html, data_inicio, data_fim, quantidade_clientes, lucro_total, list_items = reports.visualiza_relatorio_vendas_clientes(data_inicio, data_fim)

            return render_template("visualizar-relatorio-vendas-clientes.html", grafico_html=grafico_html, data_inicio=data_inicio, data_fim=data_fim, quantidade_clientes=quantidade_clientes, lucro_total=lucro_total, list_clientes=list_items)  
            
        elif request.form.get("tipoRelatorio") == "Lucro por Produto":
            grafico_html, data_inicio, data_fim, quantidade_produtos_vendidos, receita_total, custo_total, lucro_bruto_total, list_items = reports.visualiza_relatorio_lucro_produtos(data_inicio, data_fim)

            return render_template("visualizar-relatorio-lucro-produto.html", grafico_html=grafico_html, data_inicio=data_inicio, data_fim=data_fim, quantidade_produtos_vendidos=quantidade_produtos_vendidos, receita_total=receita_total, custo_total=custo_total, lucro_bruto_total=lucro_bruto_total, tabela_produtos=list_items) 

        elif request.form.get("tipoRelatorio") == "Vendas por Fornecedor":
            grafico_html, data_inicio, data_fim, quantidade_fornecedores, lucro_total, list_items = reports.visualiza_relatorio_vendas_fornecedor(data_inicio, data_fim)

            return render_template("visualizar-relatorio-vendas-fornecedores.html", grafico_html=grafico_html, data_inicio=data_inicio, data_fim=data_fim, quantidade_fornecedores=quantidade_fornecedores, lucro_total=lucro_total, tabela_fornecedores=list_items)

        elif request.form.get("tipoRelatorio") == "Relatório de Cancelamentos":
            print(reports.visualiza_relatorio_vendas_cancelamentos(data_inicio, data_fim))
            grafico_html, data_inicio, data_fim, quantidade_cancelamentos, total_cancelado, list_items, grafico_html2 = reports.visualiza_relatorio_vendas_cancelamentos(data_inicio, data_fim)

            return render_template("visualizar-relatorio-vendas-canceladas.html", grafico_html=grafico_html, data_inicio=data_inicio, data_fim=data_fim, quantidade_cancelamentos=quantidade_cancelamentos, total_cancelado=total_cancelado, tabela_canceladas=list_items, grafico_html2=grafico_html2)  
            
    except Exception as e:
        print('eeeeeeeeeeeee', e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    

app.run(debug=True)