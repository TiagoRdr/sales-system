from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from datetime import datetime, date
import mysql.connector
import calendar
import reports
from database import DatabaseConnection
import new_sale
from consults import ConsultaProdutos, ConsultaClientes, ConsultaFornecedores
from cadastros import CadastroProdutos
from update import AtualizaClientes, AtualizaFornecedores, AtualizaProdutos
import support
from app_conf import app
from dateutil.relativedelta import relativedelta


def format_value(value):
    return str(format(value, '.2f')).replace(".", ",")

def format_value_visual(value):
    return str(format(value, '.2f')).replace(".", ",")


class TelaInicial:
    def __init__(self, db_connection) -> None:
        self.db_connection = db_connection
    
    def get_monthly_values(self):
        ultimo_dia_mes_atual = calendar.monthrange(date.today().year, date.today().month)[1]

        query = f"""select
                            coalesce(sum(total_venda),0),
                            count( distinct(id_cliente)),
                            coalesce(avg(total_venda),0),
                            (select count(distinct(p2.nome)) from produtos p2 where qtd_estoque <= 10) as qtd_produtos_estoque_critico
                            from vendas v
                            where data_venda between '{date.today().year}-{date.today().month}-01' and '{date.today().year}-{date.today().month}-{ultimo_dia_mes_atual}'
                        """

        result = self.db_connection.execute_query(query)
        print(result)
        return result[0]

    @app.route('/', methods=["GET", "POST"])
    def main():   

        db_connection = DatabaseConnection()
        db_connection.connect() 

        telainicial = TelaInicial(db_connection)

        valores_mensal = telainicial.get_monthly_values()
        db_connection.close()


        total_mensal = format_value(valores_mensal[0])
        total_clientes = valores_mensal[1]
        ticket_medio = format_value(valores_mensal[2])
        qtd_produtos_estoque_critico = valores_mensal[3]

        return render_template("index.html", 
                                total_mensal=total_mensal, 
                                total_clientes=total_clientes, 
                                ticket_medio=ticket_medio, 
                                qtd_produtos_estoque_critico=qtd_produtos_estoque_critico)





app.run(debug=True)