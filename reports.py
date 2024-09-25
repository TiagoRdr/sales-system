from flask import request
from datetime import datetime, date
import mysql.connector
import pandas as pd
import calendar
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

def conexao():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="tr-sale-system"
        )
    
    return mydb

def consulta_vendas_mes(data_inicio, data_fim):

    conn = conexao()

    mycursor = conn.cursor()    
    mycursor.execute(f"""select
                            v.id,
                            DATE_FORMAT(v.data_venda, '%d/%m/%Y') AS data_formatada,
                            v.forma_pagamento,
                            c2.nome,
                            REPLACE(FORMAT(v.total_venda , 2), '.', ',') AS campo_formatado                                
                            from vendas v 
                            left join clientes c2 on v.id_cliente  = c2.id
                            where data_venda between '{data_inicio}' and '{data_fim}'
                            and status_venda not like '%Cancelada%'
                            ORDER BY v.id desc
                    """)
    myresult = mycursor.fetchall()
    return myresult

def visualiza_relatorio_vendas_periodo(data_inicio, data_fim):
    try:
        conn = conexao()
        query = f"""SELECT
                        data_venda AS Data,
                        CAST(sum(total_venda)AS FLOAT) AS Totais,
                        CAST((SELECT SUM(total_venda) FROM vendas WHERE data_venda BETWEEN '{data_inicio}' AND '{data_fim}' AND status_venda NOT LIKE '%Cancelada%') AS FLOAT) AS soma_total,
                        (SELECT sum(vp.quantidade) FROM vendas_produtos vp LEFT JOIN vendas v ON v.id = vp.id_venda WHERE v.data_venda BETWEEN '{data_inicio}' AND '{data_fim}' AND v.status_venda NOT LIKE '%Cancelada%') AS qtd_produtos,
                        CAST((SELECT AVG(total_venda) FROM vendas WHERE data_venda BETWEEN '{data_inicio}' AND '{data_fim}' AND status_venda NOT LIKE '%Cancelada%') AS FLOAT) AS ticket_medio,
                        (SELECT COUNT(id) FROM vendas WHERE data_venda BETWEEN '{data_inicio}' AND '{data_fim}' AND status_venda NOT LIKE '%Cancelada%') AS total_transacoes
                    FROM vendas
                    WHERE data_venda BETWEEN '{data_inicio}' AND '{data_fim}'
                    AND status_venda NOT LIKE '%Cancelada%'
                    GROUP BY data_venda
                    ORDER BY data_venda ASC;  -- Ordenar pela data em ordem crescente
                """

        df = pd.read_sql(query, conn)

        df['Data'] = pd.to_datetime(df['Data'])

        # Criando o gráfico de linha com Plotly
        fig = px.line(df, x='Data', y='Totais', title="Vendas por período",
                        labels={"Totais": "Total de Vendas", "Data": "Data"})

        # Salvando o gráfico em formato HTML
        grafico_html = pio.to_html(fig, full_html=False)
        vendas_periodo = consulta_vendas_mes(data_inicio, data_fim)
        # Obtenha os valores necessários
        total_vendas = str(round(df['soma_total'][1], 2)).replace(".", ",")
        total_produtos = df['qtd_produtos'].iloc[0]  # Altere o índice para 0, pois df[1] pode não existir
        ticket_medio = str(round(df['ticket_medio'].iloc[0], 2)).replace(".", ",")  # Altere o índice para 0
        total_transacoes = df['total_transacoes'].iloc[0]  # Altere o índice para 0

        return grafico_html, datetime.strptime(data_inicio, '%Y-%m-%d').strftime("%d/%m/%Y"), datetime.strptime(data_fim, '%Y-%m-%d').strftime("%d/%m/%Y"), total_vendas, total_produtos, ticket_medio, total_transacoes, vendas_periodo    
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    
###########################################################################################################################

def visualiza_relatorio_produtos_mais_vendidos(data_inicio, data_fim):
    try:
        conn = conexao()
        query = f"""select
                    max(vp.nome_produto) as nome_produto,
                    sum(quantidade) as quantidade,
                    (select sum(vp2.quantidade) from vendas_produtos vp2 left join vendas v2 on v2.id = vp2.id_venda WHERE v2.data_venda BETWEEN '{data_inicio}' AND '{data_fim}' AND v2.status_venda NOT LIKE '%Cancelada%') as quantidade_total,
                    sum(quantidade * valor_unitario) as total_vendido
                    from vendas_produtos vp 
                    left join vendas v on v.id = vp.id_venda 
                    WHERE data_venda BETWEEN '{data_inicio}' AND '{data_fim}'
                    AND status_venda NOT LIKE '%Cancelada%'
                    group by vp.id_produto, quantidade
                    order by quantidade desc;
                """

        df = pd.read_sql(query, conn)

        # # Criando o gráfico de linha com Plotly
        # fig = px.bar(df, x='nome_produto', y='quantidade', title="Vendas por Produto",
        #                 labels={"nome_produto": "Produto", "quantidade": "Quantidade vendida"})

        fig = go.Figure(data=[
            go.Bar(x=df['nome_produto'], y=df['quantidade'], text=df['quantidade'], textposition='auto')
        ])

        # Salvando o gráfico em formato HTML
        grafico_html = pio.to_html(fig, full_html=False)
        # Obtenha os valores necessários
        quantidade_total = df['quantidade_total'].astype(int).iloc[0]
        total_produtos = str(round(df['total_vendido'].sum(), 2)).replace(".", ",")  # Altere o índice para 0, pois df[1] pode não existir
        list_items = df.values.tolist()
        
        return grafico_html, datetime.strptime(data_inicio, '%Y-%m-%d').strftime("%d/%m/%Y"), datetime.strptime(data_fim, '%Y-%m-%d').strftime("%d/%m/%Y"), quantidade_total, total_produtos, list_items
    
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    

###############################################################################################################################
    

def visualiza_relatorio_estoque_critico():
    try:
        conn = conexao()
        query = f"""select
                    max(p.nome) as nome_produto,
                    max(f.nome) as fornecedor,  
                    max(p.qtd_estoque) as qtd_estoque,
                    (select count(distinct(p2.nome)) from produtos p2 where qtd_estoque <= 10)  as qtd_produtos_estoque_critico
                    from produtos p 
                    left join fornecedores f on p.id_fornecedor = f.id 
                    where qtd_estoque <= 10
                    group by p.nome, p.qtd_estoque
                    order by p.qtd_estoque asc
                """

        df = pd.read_sql(query, conn)

        # # Criando o gráfico de linha com Plotly
        # fig = px.bar(df, x='nome_produto', y='quantidade', title="Vendas por Produto",
        #                 labels={"nome_produto": "Produto", "quantidade": "Quantidade vendida"})

        fig = go.Figure(data=[
            go.Bar(x=df['nome_produto'], y=df['qtd_estoque'], text=df['qtd_estoque'], textposition='auto')
        ])
        
        # Salvando o gráfico em formato HTML
        grafico_html = pio.to_html(fig, full_html=False)


        # Obtenha os valores necessários
        quantidade_produtos_critico = df['qtd_produtos_estoque_critico'].astype(int).iloc[0]

        list_items = df.values.tolist()        
        return grafico_html, quantidade_produtos_critico, list_items
    
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    

##############################################################################################################
    

def visualiza_relatorio_vendas_clientes(data_inicio, data_fim):
    try:
        conn = conexao()
        query = f"""select 
                    max(c.nome) as nome_cliente,
                    (select count(v.id_cliente) from vendas v2 left join clientes c on v.id_cliente = c.id WHERE data_venda BETWEEN '{data_inicio}' AND '{data_fim}' AND status_venda NOT LIKE '%Cancelada%' GROUP BY v.id_cliente) as total_vendas_cliente                    
                    from vendas v 
                    left join clientes c on v.id_cliente = c.id 
                    WHERE data_venda BETWEEN '{data_inicio}' AND '{data_fim}' 
                    AND status_venda NOT LIKE '%Cancelada%'
                    GROUP BY v.id_cliente 
                    ORDER BY total_vendas_cliente desc
                    limit 15; 
                """

        df = pd.read_sql(query, conn)

        # Criando o gráfico de linha com Plotly
        fig = go.Figure(data=[
            go.Bar(x=df['nome_cliente'], y=df['total_vendas_cliente'], text=df['total_vendas_cliente'], textposition='auto')
        ])

        # Salvando o gráfico em formato HTML
        grafico_html = pio.to_html(fig, full_html=False)
        vendas_periodo = consulta_vendas_mes(data_inicio, data_fim)
        # Obtenha os valores necessários
        nome_clientes = df['nome_cliente'].iloc[0]

        quantidade_clientes = len(df)

        
        return grafico_html, datetime.strptime(data_inicio, '%Y-%m-%d').strftime("%d/%m/%Y"), datetime.strptime(data_fim, '%Y-%m-%d').strftime("%d/%m/%Y"), nome_clientes, vendas_periodo, quantidade_clientes

    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    