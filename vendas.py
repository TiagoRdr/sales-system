from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, date
import mysql.connector
import calendar


app = Flask(__name__)



app.config['FLASK_ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TESTING'] = True

data_atual = date.today().strftime("%Y-%m-%d")
produtos = []

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



@app.route('/nova_venda', methods=["GET", "POST"])
def nova_venda():  
    # Se estiver fora da função
    total_prods = total_produtos()    
    return render_template("new_sale.html", data_atual=data_atual, produtos=produtos, total_prods=total_prods)

def total_produtos():
    total_prods = 0
    try:
        for i in range(len(produtos)):
            total_prods += round((int(produtos[i][1]) * float(str(produtos[i][2]).replace(",","."))),2)
    except Exception as e:
        print(e)
        total_prods = 0

    return total_prods

def total_vendas(taxaentrega, desconto):
    total_venda = 0
    total_prod = total_produtos()    
    try:
        total_venda = round(float(total_prod) + (float(str(taxaentrega).replace(",",".")) - float(str(desconto).replace(",","."))),2)
    except Exception as e:
        print(e)
        total_venda = 0
    return total_venda


@app.route('/add_product', methods=['POST'])
def add_product():    
    product_name = request.form.get('produto')
    product_qtd = request.form.get('quantidade')
    product_valor_unit = request.form.get('valorunitario')
    print(product_name, product_qtd, product_valor_unit)
    
    if product_name and product_qtd and product_valor_unit:
        produtos.append([product_name, product_qtd, product_valor_unit])

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
        total_prods = total_produtos()
        product_taxa = request.form.get('valortaxa') 
        product_desconto = request.form.get('valordesconto')
        nomecliente = request.form.get('nomecliente') if len(request.form.get('nomecliente')) > 1 else '-'
        datavenda = datetime.strptime(request.form.get('datavenda'), '%Y-%m-%d').date().strftime('%d/%m/%Y')
        dataentrega = datetime.strptime(request.form.get('dataentrega'), '%Y-%m-%d').date().strftime('%d/%m/%Y')       
        metodopagamento = request.form.get('metodopagamento')
        observacoes = request.form.get('observacoes') if len(request.form.get('observacoes')) > 1 else '-'

        if not product_taxa or not product_desconto:
            return jsonify({"error": "Missing values"}), 400  # Retorna erro 400 se valores ausentes

        total_venda = total_vendas(product_taxa, product_desconto)
        return render_template('/resume-sale.html', total_prods=str(total_prods).replace(".",","), total_venda=str(total_venda).replace(".",","), taxaentrega=str(product_taxa).replace(".",","), desconto=str(product_desconto).replace(".",","), nomecliente=nomecliente, datavenda=datavenda, dataentrega=dataentrega, metodopagamento=metodopagamento, observacoes=observacoes, produtos=produtos)

    
    except Exception as e:
        print("Erro no processamento:", str(e))
        return jsonify({"error": "Server error"}), 500


@app.route("/consulta")
def consulta_main():
    return render_template("consulta.html")


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
                            v.taxa_entrega,
                            c2.nome,
                            REPLACE(FORMAT(v.total_venda , 2), '.', ',') AS campo_formatado 
                            from vendas v 
                            left join clientes c2 on v.id_cliente  = c2.id
                            where data_venda between '{date.today().year}-{date.today().month}-01' and '{date.today().year}-{date.today().month}-{ultimo_dia_mes}'
                            ORDER BY v.id desc
                    """)
    myresult = mycursor.fetchall()
    return myresult



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
                            f.nome,
                            p.qtd_estoque, 
                            REPLACE(FORMAT(p.valor_unitario  , 2), '.', ',') AS campo_formatado                            
                            from produtos p
                            left join fornecedores f on p.id_fornecedor = f.id 
                            ORDER BY p.id desc
                    """)
    myresult = mycursor.fetchall()
    return myresult


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



app.run(debug=True)