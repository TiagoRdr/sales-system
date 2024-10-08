from flask import request, render_template
from datetime import datetime, date
import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from database import DatabaseConnection
from app_conf import app

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
            grafico_html, data_inicio, data_fim, total_vendas, total_produtos, ticket_medio, total_transacoes, vendas_periodo = visualiza_relatorio_vendas_periodo(data_inicio, data_fim)

            return render_template("visualizar-relatorio-vendas-periodo.html", grafico_html=grafico_html, data_inicio=data_inicio, data_fim=data_fim, total_vendas=total_vendas, total_produtos=total_produtos, ticket_medio=ticket_medio, total_transacoes=total_transacoes, vendas_periodo=vendas_periodo)  

        elif request.form.get("tipoRelatorio") == "Produtos Mais Vendidos":
            grafico_html, data_inicio, data_fim, quantidade_total, total_produtos, tabela_produtos = visualiza_relatorio_produtos_mais_vendidos(data_inicio, data_fim)

            return render_template("visualizar-relatorio-produtos-mais-vendidos.html", grafico_html=grafico_html, data_inicio=data_inicio, data_fim=data_fim,quantidade_total=quantidade_total, total_produtos=total_produtos, tabela_produtos=tabela_produtos)  
        
        elif request.form.get("tipoRelatorio") == "Estoque Crítico":
            grafico_html, quantidade_produtos_critico, list_items = visualiza_relatorio_estoque_critico()

            return render_template("visualizar-relatorio-estoque-critico.html", grafico_html=grafico_html, quantidade_produtos_critico=quantidade_produtos_critico, tabela_produtos=list_items)  
        
        elif request.form.get("tipoRelatorio") == "Vendas por Cliente":
            grafico_html, data_inicio, data_fim, quantidade_clientes, lucro_total, list_items = visualiza_relatorio_vendas_clientes(data_inicio, data_fim)

            return render_template("visualizar-relatorio-vendas-clientes.html", grafico_html=grafico_html, data_inicio=data_inicio, data_fim=data_fim, quantidade_clientes=quantidade_clientes, lucro_total=lucro_total, list_clientes=list_items)  
            
        elif request.form.get("tipoRelatorio") == "Fluxo de caixa":
            grafico_html, data_inicio, data_fim, quantidade_produtos_vendidos, receita_total, custo_total, lucro_bruto_total, list_items = visualiza_relatorio_fluxo_caixa(data_inicio, data_fim)

            return render_template("visualizar-relatorio-lucro-produto.html", grafico_html=grafico_html, data_inicio=data_inicio, data_fim=data_fim, quantidade_produtos_vendidos=quantidade_produtos_vendidos, receita_total=receita_total, custo_total=custo_total, lucro_bruto_total=lucro_bruto_total, tabela_produtos=list_items) 

        elif request.form.get("tipoRelatorio") == "Vendas por Fornecedor":
            grafico_html, data_inicio, data_fim, quantidade_fornecedores, lucro_total, list_items = visualiza_relatorio_vendas_fornecedor(data_inicio, data_fim)

            return render_template("visualizar-relatorio-vendas-fornecedores.html", grafico_html=grafico_html, data_inicio=data_inicio, data_fim=data_fim, quantidade_fornecedores=quantidade_fornecedores, lucro_total=lucro_total, tabela_fornecedores=list_items)

        elif request.form.get("tipoRelatorio") == "Relatório de Cancelamentos":
            print(visualiza_relatorio_vendas_cancelamentos(data_inicio, data_fim))
            grafico_html, data_inicio, data_fim, quantidade_cancelamentos, total_cancelado, list_items, grafico_html2 = visualiza_relatorio_vendas_cancelamentos(data_inicio, data_fim)

            return render_template("visualizar-relatorio-vendas-canceladas.html", grafico_html=grafico_html, data_inicio=data_inicio, data_fim=data_fim, quantidade_cancelamentos=quantidade_cancelamentos, total_cancelado=total_cancelado, tabela_canceladas=list_items, grafico_html2=grafico_html2)  
            
    except Exception as e:
        print('eeeeeeeeeeeee', e)
        return "Não existem dados para o período selecionado", 500  # Retornar uma mensagem de erro

def consulta_vendas_mes(data_inicio, data_fim):

    db_connection = DatabaseConnection()
    db_connection.connect()

    query_vendas_mes = f"""select
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
                    """
    
    result_vendas_filtros = db_connection.execute_query(query_vendas_mes)
    return result_vendas_filtros

def visualiza_relatorio_vendas_periodo(data_inicio, data_fim):
    try:
        db_connection = DatabaseConnection()
        db_connection.connect()

        query = f"""SELECT
                        data_venda AS Data,
                        coalesce(CAST(sum(total_venda)AS FLOAT),0) AS Totais,
                        coalesce(CAST((SELECT SUM(total_venda) FROM vendas WHERE data_venda BETWEEN '{data_inicio}' AND '{data_fim}' AND status_venda NOT LIKE '%Cancelada%') AS FLOAT),0) AS soma_total,
                        coalesce((SELECT sum(vp.quantidade) FROM vendas_produtos vp LEFT JOIN vendas v ON v.id = vp.id_venda WHERE v.data_venda BETWEEN '{data_inicio}' AND '{data_fim}' AND v.status_venda NOT LIKE '%Cancelada%'),0) AS qtd_produtos,
                        coalesce(CAST((SELECT AVG(total_venda) FROM vendas WHERE data_venda BETWEEN '{data_inicio}' AND '{data_fim}' AND status_venda NOT LIKE '%Cancelada%') AS FLOAT),0) AS ticket_medio,
                        coalesce((SELECT COUNT(id) FROM vendas WHERE data_venda BETWEEN '{data_inicio}' AND '{data_fim}' AND status_venda NOT LIKE '%Cancelada%'),0) AS total_transacoes
                    FROM vendas
                    WHERE data_venda BETWEEN '{data_inicio}' AND '{data_fim}'
                    AND status_venda NOT LIKE '%Cancelada%'
                    GROUP BY data_venda
                    ORDER BY data_venda ASC;
                """

        df = pd.read_sql(query, con=db_connection.connection)
        
        if len(df) > 0:
            df['Data'] = pd.to_datetime(df['Data'])
            
            # Criando o gráfico de linha com Plotly
            fig = px.line(df, x='Data', y='Totais', title="Vendas por período",
                            labels={"Totais": "Total de Vendas", "Data": "Data"})

            # Salvando o gráfico em formato HTML
            grafico_html = pio.to_html(fig, full_html=False)
            vendas_periodo = consulta_vendas_mes(data_inicio, data_fim)
            # Obtenha os valores necessários

            total_vendas = str(format(df['soma_total'][0], '.2f')).replace(".", ",")

            total_produtos = int(df['qtd_produtos'].iloc[0])  # Altere o índice para 0, pois df[1] pode não existir
            ticket_medio = str(format(df['ticket_medio'].iloc[0], '.2f')).replace(".", ",")  # Altere o índice para 0
            total_transacoes = df['total_transacoes'].iloc[0]  # Altere o índice para 0

            return grafico_html, datetime.strptime(data_inicio, '%Y-%m-%d').strftime("%d/%m/%Y"), datetime.strptime(data_fim, '%Y-%m-%d').strftime("%d/%m/%Y"), total_vendas, total_produtos, ticket_medio, total_transacoes, vendas_periodo 
            
    except Exception as e:
        print(e)
        return "Não existem dados para o período selecionado", 500  # Retornar uma mensagem de erro
    
###########################################################################################################################

def visualiza_relatorio_produtos_mais_vendidos(data_inicio, data_fim):
    try:
        db_connection = DatabaseConnection()
        db_connection.connect()

        query = f"""select
                    max(vp.nome_produto) as nome_produto,
                    sum(quantidade) as quantidade,
                    (select sum(vp2.quantidade) from vendas_produtos vp2 left join vendas v2 on v2.id = vp2.id_venda WHERE v2.data_venda BETWEEN '{data_inicio}' AND '{data_fim}' AND v2.status_venda NOT LIKE '%Cancelada%') as quantidade_total,
                    sum(quantidade * valor_unitario) as total_vendido
                    from vendas_produtos vp 
                    left join vendas v on v.id = vp.id_venda 
                    WHERE data_venda BETWEEN '{data_inicio}' AND '{data_fim}'
                    AND status_venda NOT LIKE '%Cancelada%'
                    group by vp.id_produto
                    order by quantidade desc;
                """
        print(query)
        df = pd.read_sql(query, con=db_connection.connection)

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
        total_produtos = str(format(df['total_vendido'].sum(), '.2f')).replace(".", ",")  # Altere o índice para 0, pois df[1] pode não existir
        
        df['quantidade'] = df['quantidade'].astype(int)
        df['total_vendido'] = df['total_vendido'].apply(lambda x: f"{x:.2f}".replace('.', ','))

        list_items = df.values.tolist()

        return grafico_html, datetime.strptime(data_inicio, '%Y-%m-%d').strftime("%d/%m/%Y"), datetime.strptime(data_fim, '%Y-%m-%d').strftime("%d/%m/%Y"), quantidade_total, total_produtos, list_items
    
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    

###############################################################################################################################
    

def visualiza_relatorio_estoque_critico():
    try:
        db_connection = DatabaseConnection()
        db_connection.connect()

        query = f"""select
                    max(p.id),
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

        df = pd.read_sql(query, con=db_connection.connection)

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
        db_connection = DatabaseConnection()
        db_connection.connect()

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

        df = pd.read_sql(query, con=db_connection.connection)

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

        df['total_produtos_comprados'] = df['total_produtos_comprados'].astype(int)
        df['lucro_total'] = df['lucro_total'].apply(lambda x: f"{x:.2f}".replace('.', ','))


        list_items = df.values.tolist()

        
        return grafico_html, datetime.strptime(data_inicio, '%Y-%m-%d').strftime("%d/%m/%Y"), datetime.strptime(data_fim, '%Y-%m-%d').strftime("%d/%m/%Y"), quantidade_clientes, lucro_total, list_items

    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    
#############################################################################################################################

def visualiza_relatorio_fluxo_caixa(data_inicio, data_fim):
    try:
        db_connection = DatabaseConnection()
        db_connection.connect()

        query = f"""select 
                        max(p.nome) as nome_produto,
                        sum(vp.quantidade) as quantidade_vendida,
                        max(p.valor_unitario) as valor_unitario,
                        sum(vp.quantidade * vp.valor_unitario) as receita_total,
                        coalesce(sum(vp.quantidade * p.custo_aquisicao),0) as custo_total,
                        (SUM(vp.quantidade * vp.valor_unitario) - sum(vp.quantidade * coalesce(p.custo_aquisicao,0))) as lucro_bruto
                        from vendas_produtos vp 
                        join vendas v on v.id = vp.id_venda
                        join produtos p on p.id = vp.id_produto
                        WHERE data_venda BETWEEN '{data_inicio}' AND '{data_fim}'
                        AND status_venda NOT LIKE '%Cancelada%'
                        group by vp.id_produto
                        order by lucro_bruto desc;
                """

        df = pd.read_sql(query, con=db_connection.connection)

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

        quantidade_produtos_vendidos = int(df['quantidade_vendida'].sum())
        receita_total = str(format(df['receita_total'].sum(), '.2f')).replace(".", ",")
        custo_total = str(format(df['custo_total'].sum(), '.2f')).replace(".", ",")
        lucro_bruto_total = str(format(df['lucro_bruto'].sum(), '.2f')).replace(".", ",")


        df['quantidade_vendida'] = df['quantidade_vendida'].astype(int)
        df['valor_unitario'] = df['valor_unitario'].apply(lambda x: f"{x:.2f}".replace('.', ','))
        df['receita_total'] = df['receita_total'].apply(lambda x: f"{x:.2f}".replace('.', ','))
        df['custo_total'] = df['custo_total'].apply(lambda x: f"{x:.2f}".replace('.', ','))
        df['lucro_bruto'] = df['lucro_bruto'].apply(lambda x: f"{x:.2f}".replace('.', ','))

        list_items = df.values.tolist()
        
        return grafico_html, datetime.strptime(data_inicio, '%Y-%m-%d').strftime("%d/%m/%Y"), datetime.strptime(data_fim, '%Y-%m-%d').strftime("%d/%m/%Y"), quantidade_produtos_vendidos, receita_total, custo_total, lucro_bruto_total, list_items
    
    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    
#########################################################################################################################################################

def visualiza_relatorio_vendas_fornecedor(data_inicio, data_fim):
    try:
        db_connection = DatabaseConnection()
        db_connection.connect()

        query = f"""SELECT f.nome AS nome_fornecedor, 
                        SUM(vp.quantidade) AS total_produtos_vendidos,
                        SUM(vp.quantidade * (vp.valor_unitario - coalesce(p.custo_aquisicao,0))) AS     
                        FROM `tr-sale-system`.fornecedores f
                        JOIN `tr-sale-system`.produtos p ON f.id = p.id_fornecedor
                        JOIN `tr-sale-system`.vendas_produtos vp ON p.id = vp.id_produto
                        JOIN `tr-sale-system`.vendas v ON vp.id_venda = v.id
                        WHERE v.status_venda NOT LIKE '%Cancelada%'
                        and v.data_venda BETWEEN '{data_inicio}' AND '{data_fim}'
                        GROUP BY f.nome
                        ORDER BY total_produtos_vendidos DESC;
                """

        df = pd.read_sql(query, con=db_connection.connection)

        # Criando o gráfico de linha com Plotly
        fig = go.Figure(data=[
            go.Bar(x=df['nome_fornecedor'], y=df['total_produtos_vendidos'], text=df['total_produtos_vendidos'], textposition='auto')
        ])

        print(query)
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

        df['total_produtos_vendidos'] = df['total_produtos_vendidos'].astype(int)
        df['lucro_total'] = df['lucro_total'].apply(lambda x: f"{x:.2f}".replace('.', ','))

        list_items = df.values.tolist()

        return grafico_html, datetime.strptime(data_inicio, '%Y-%m-%d').strftime("%d/%m/%Y"), datetime.strptime(data_fim, '%Y-%m-%d').strftime("%d/%m/%Y"), quantidade_fornecedores, lucro_total, list_items

    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro
    

######################################################################################################################################
    
def visualiza_relatorio_vendas_cancelamentos(data_inicio, data_fim):
    try:
        db_connection = DatabaseConnection()
        db_connection.connect()

        query = f"""select
                        v.id as id_venda,
                        DATE_FORMAT(data_venda, '%d/%m/%Y') as data_venda,
                        c.nome as nome_cliente,
                        v.total_venda as total_venda,
                        v.motivo_cancelamento,
                        (select count(id) from vendas v where status_venda not like '%Cancelada%') as quantidade_vendas_nao_canceladas
                        from vendas v 
                        join clientes c on v.id_cliente = c.id 
                        where v.status_venda like '%Cancelada%'
                        and v.data_venda BETWEEN '{data_inicio}' AND '{data_fim}'
                """

        df = pd.read_sql(query, con=db_connection.connection)

        #Somando as quantidades de diferentes tipos de cancelamentos
        cancelamento_counts = df['motivo_cancelamento'].value_counts()
        df_cancelamentos = cancelamento_counts.reset_index()
        df_cancelamentos.columns = ['Motivo Cancelamento', 'Total']

        #Tratando os  campos
        quantidade_vendas_nao_canceladas = df['quantidade_vendas_nao_canceladas'].iloc[0] # Altere o índice para 0
        quantidade_cancelamentos = len(df)
        total_cancelado = str(format(df['total_venda'].sum(), '.2f')).replace(".",",")

        #Porcentagens para o segundo grafico
        porcentagem_cancelamentos = round((quantidade_cancelamentos * 100) / (quantidade_vendas_nao_canceladas + quantidade_cancelamentos),2)        
        porcentagens = [["Vendas Canceladas", porcentagem_cancelamentos], ["Vendas Finalizadas", round((100 - porcentagem_cancelamentos),2)]]
        df2 = pd.DataFrame(porcentagens, columns=["Tipo de Venda", "Porcentagem"])

        #Ajusta do total da venda
        df['total_venda'] = df['total_venda'].apply(lambda x: f"{x:.2f}".replace('.', ','))
        list_items = df.values.tolist()

        #Gerando Graficos
        fig = px.pie(df_cancelamentos, values=df_cancelamentos['Total'], names=df_cancelamentos['Motivo Cancelamento'], hole=.3)
        grafico_html = pio.to_html(fig, full_html=False)

        fig2 = px.pie(df2, values=df2['Porcentagem'], names=df2['Tipo de Venda'], hole=.3)
        grafico_html2 = pio.to_html(fig2, full_html=False)

        
        return grafico_html, datetime.strptime(data_inicio, '%Y-%m-%d').strftime("%d/%m/%Y"), datetime.strptime(data_fim, '%Y-%m-%d').strftime("%d/%m/%Y"), quantidade_cancelamentos, total_cancelado, list_items, grafico_html2 

    except Exception as e:
        print(e)
        return "Ocorreu um erro ao atualizar o produto.", 500  # Retornar uma mensagem de erro