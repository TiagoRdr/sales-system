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


def format_value(value):
    return str(format(value, '.2f')).replace(".", ",")

def format_value_visual(value):
    return str(format(value, '.2f')).replace(".", ",")


class TelaInicial:
    def __init__(self, db_connection) -> None:
        self.db_connection = db_connection
    
    def get_monthly_values(self):
        ultimo_dia_mes = calendar.monthrange(date.today().year, date.today().month)[1]

        query = f"""select
                            sum(total_venda),
                            count( distinct(id_cliente)),
                            avg(total_venda),
                            coalesce((select sum(total_venda) from vendas where month(data_venda) = '{date.today().month}'),0) - coalesce((select sum(total_venda) from vendas where month(data_venda) = '{date.today().month -1}'),0) as variacao
                            from vendas v 
                            where data_venda between '{date.today().year}-{date.today().month}-01' and '{date.today().year}-{date.today().month}-{ultimo_dia_mes}'
                        """

        result = self.db_connection.execute_query(query)
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
        variacao_mensal = format_value(valores_mensal[3])

        return render_template("index.html", 
                                total_mensal=total_mensal, 
                                total_clientes=total_clientes, 
                                ticket_medio=ticket_medio, 
                                variacao_mensal=variacao_mensal)





app.run(debug=True)