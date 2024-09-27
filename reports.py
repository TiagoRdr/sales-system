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

        fig.update_layout(
            yaxis_title='Produtos mais vendidos',  # Título do eixo Y
            title='Quantidade vendida',  # Título do gráfico
            title_x=0.5  # Centraliza o título
        )

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
        
        fig.update_layout(
            yaxis_title='Estoque Crítico',  # Título do eixo Y
            title='Quantidade em Estoque',  # Título do gráfico
            title_x=0.5  # Centraliza o título
        )

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
        query = f"""SELECT c.nome AS nome_cliente, 
                        SUM(vp.quantidade) AS total_produtos_comprados, 
                        SUM(vp.quantidade * (vp.valor_unitario - p.custo_aquisicao)) AS lucro_total
                        FROM `tr-sale-system`.clientes c
                        JOIN `tr-sale-system`.vendas v ON c.id = v.id_cliente
                        JOIN `tr-sale-system`.vendas_produtos vp ON v.id = vp.id_venda
                        JOIN `tr-sale-system`.produtos p ON vp.id_produto = p.id
                        WHERE v.status_venda NOT LIKE '%Cancelada%'
                        and v.data_venda BETWEEN '{data_inicio}' AND '{data_fim}'
                        GROUP BY c.nome
                        ORDER BY lucro_total DESC; 
                """

        df = pd.read_sql(query, conn)

        # Criando o gráfico de linha com Plotly
        fig = go.Figure(data=[
            go.Bar(x=df['nome_cliente'], y=df['total_produtos_comprados'], text=df['total_produtos_comprados'], textposition='auto')
        ])

        fig.update_layout(
            yaxis_title='Total por Cliente',  # Título do eixo Y
            title='Vendas por Cliente',  # Título do gráfico
            title_x=0.5  # Centraliza o título
        )

        # Salvando o gráfico em formato HTML
        grafico_html = pio.to_html(fig, full_html=False)
        # Obtenha os valores necessários
        quantidade_clientes = len(df)
        lucro_total = df['lucro_total'].sum()
        list_items = df.values.tolist()

        
        return grafico_html, datetime.strptime(data_inicio, '%Y-%m-%d').strftime("%d/%m/%Y"), datetime.strptime(data_fim, '%Y-%m-%d').strftime("%d/%m/%Y"), quantidade_clientes, lucro_total, list_items

    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    
#############################################################################################################################

def visualiza_relatorio_lucro_produtos(data_inicio, data_fim):
    try:
        conn = conexao()
        query = f"""select 
                        max(p.nome) as nome_produto,
                        sum(vp.quantidade) as quantidade_vendida,
                        max(p.valor_unitario) as valor_unitario,
                        sum(vp.quantidade * vp.valor_unitario) as receita_total,
                        sum(vp.quantidade * p.custo_aquisicao) as custo_total,
                        (SUM(vp.quantidade * vp.valor_unitario) - sum(vp.quantidade * p.custo_aquisicao)) as lucro_bruto
                        from vendas_produtos vp 
                        join vendas v on v.id = vp.id_venda
                        join produtos p on p.id = vp.id_produto
                        WHERE data_venda BETWEEN '{data_inicio}' AND '{data_fim}'
                        AND status_venda NOT LIKE '%Cancelada%'
                        group by vp.id_produto
                        order by lucro_bruto desc;
                """

        df = pd.read_sql(query, conn)

        # # Criando o gráfico de linha com Plotly
        # fig = px.bar(df, x='nome_produto', y='quantidade', title="Vendas por Produto",
        #                 labels={"nome_produto": "Produto", "quantidade": "Quantidade vendida"})

        fig = go.Figure(data=[
            go.Bar(x=df['nome_produto'], y=df['lucro_bruto'], text=df['lucro_bruto'], textposition='auto')
        ])


        fig.update_layout(
            yaxis_title='Lucro Bruto',  # Título do eixo Y
            title='Lucro por Produto',  # Título do gráfico
            title_x=0.5  # Centraliza o título
        )

        # Salvando o gráfico em formato HTML
        grafico_html = pio.to_html(fig, full_html=False)
        # Obtenha os valores necessários

        quantidade_produtos_vendidos = df['quantidade_vendida'].sum()
        receita_total = df['receita_total'].sum()
        custo_total = df['custo_total'].sum()
        lucro_bruto_total = df['lucro_bruto'].sum()

        list_items = df.values.tolist()
        
        return grafico_html, datetime.strptime(data_inicio, '%Y-%m-%d').strftime("%d/%m/%Y"), datetime.strptime(data_fim, '%Y-%m-%d').strftime("%d/%m/%Y"), quantidade_produtos_vendidos, receita_total, custo_total, lucro_bruto_total, list_items
    
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    
#########################################################################################################################################################

def visualiza_relatorio_vendas_fornecedor(data_inicio, data_fim):
    try:
        conn = conexao()
        query = f"""SELECT f.nome AS nome_fornecedor, 
                        SUM(vp.quantidade) AS total_produtos_vendidos,
                        SUM(vp.quantidade * (vp.valor_unitario - p.custo_aquisicao)) AS lucro_total
                        FROM `tr-sale-system`.fornecedores f
                        JOIN `tr-sale-system`.produtos p ON f.id = p.id_fornecedor
                        JOIN `tr-sale-system`.vendas_produtos vp ON p.id = vp.id_produto
                        JOIN `tr-sale-system`.vendas v ON vp.id_venda = v.id
                        WHERE v.status_venda NOT LIKE '%Cancelada%'
                        and v.data_venda BETWEEN '{data_inicio}' AND '{data_fim}'
                        GROUP BY f.nome
                        ORDER BY total_produtos_vendidos DESC;
                """

        df = pd.read_sql(query, conn)

        # Criando o gráfico de linha com Plotly
        fig = go.Figure(data=[
            go.Bar(x=df['nome_fornecedor'], y=df['total_produtos_vendidos'], text=df['total_produtos_vendidos'], textposition='auto')
        ])


        # Adicionando o label ao eixo Y
        fig.update_layout(
            yaxis_title='Total de Produtos Vendidos',  # Título do eixo Y
            title='Vendas por Fornecedor',  # Título do gráfico
            title_x=0.5  # Centraliza o título
        )

        # Salvando o gráfico em formato HTML
        grafico_html = pio.to_html(fig, full_html=False)
        # Obtenha os valores necessários

        quantidade_fornecedores = len(df)
        lucro_total = df['lucro_total'].sum()
        list_items = df.values.tolist()

        return grafico_html, datetime.strptime(data_inicio, '%Y-%m-%d').strftime("%d/%m/%Y"), datetime.strptime(data_fim, '%Y-%m-%d').strftime("%d/%m/%Y"), quantidade_fornecedores, lucro_total, list_items

    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    

######################################################################################################################################
    
def visualiza_relatorio_vendas_cancelamentos(data_inicio, data_fim):
    try:
        conn = conexao()
        query = f"""select
                        v.id as id_venda,
                        v.data_venda as data_venda,
                        c.nome as nome_cliente,
                        v.total_venda as total_venda,
                        v.motivo_cancelamento,
                        (select count(id) from vendas v where status_venda not like '%Cancelada%') as quantidade_vendas
                        from vendas v 
                        join clientes c on v.id_cliente = c.id 
                        where v.status_venda like '%Cancelada%'
                        and v.data_venda BETWEEN '{data_inicio}' AND '{data_fim}'
                """

        df = pd.read_sql(query, conn)

        df['data_venda'] = pd.to_datetime(df['data_venda'])

        cancelamento_counts = df['motivo_cancelamento'].value_counts()
        # Criando o gráfico de linha com Plotly
        fig = px.pie(cancelamento_counts, values=cancelamento_counts.values, names=cancelamento_counts.index)

        # Salvando o gráfico em formato HTML
        grafico_html = pio.to_html(fig, full_html=False)

        quantidade_cancelamentos = len(df)
        total_cancelado = df['total_venda'].sum()
        # Obtenha os valores necessários

        list_items = df.values.tolist()
        return grafico_html, datetime.strptime(data_inicio, '%Y-%m-%d').strftime("%d/%m/%Y"), datetime.strptime(data_fim, '%Y-%m-%d').strftime("%d/%m/%Y"), quantidade_cancelamentos, total_cancelado, list_items    

    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro