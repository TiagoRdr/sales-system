from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Float, Date, BLOB
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()
engine = create_engine('mysql+mysqlconnector://root:root@localhost/tr-sale-system')
Session = sessionmaker(bind=engine)
session = Session()

class Produto(Base):
    __tablename__ = 'produtos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    id_fornecedor = Column(Integer, nullable=False)
    qtd_estoque = Column(Integer, nullable=False)
    valor_unitario = Column(Float, nullable=False)
    marca = Column(String(100), nullable=True)
    data_validade = Column(Date, nullable=True)
    peso = Column(String(100), nullable=True)
    custo_aquisicao = Column(Float, nullable=True)
    foto = Column(BLOB, nullable=True)

    def __repr__(self):
        return f"<Produto(id={self.id}, nome={self.nome}, preco={self.valor_unitario})>"



def consulta_produtos(coluna=None, valor=None):
    if coluna is None:
        produtos = session.query(Produto).all()
    else:
        produtos = session.query(Produto).filter_by(coluna=valor).first()

    return produtos

def inserir_produtos(nome_produto, codigo_fornecedor, qtd_estoque_produto, valor_unitario_produto, marca_produto=None, data_validade_produto=None, peso_produto=None, custo_produto=None, imagem_binaria=None):
    novo_produto = Produto(
        nome=nome_produto,
        id_fornecedor=codigo_fornecedor,
        qtd_estoque=qtd_estoque_produto,
        valor_unitario=valor_unitario_produto,
        marca=marca_produto,
        data_validade=data_validade_produto,
        peso=peso_produto,
        custo_aquisicao=custo_produto,
        foto=imagem_binaria
    )
    session.add(novo_produto)
    session.commit()  

def atualizar_produto(id, nome_produto, codigo_fornecedor, qtd_estoque_produto, valor_unitario_produto, marca_produto=None, data_validade_produto=None, peso_produto=None, custo_produto=None, imagem_binaria=None):
    produto = session.query(Produto).filter_by(id=f"{id}").first()
    produto.nome_produto = nome_produto
    produto.codigo_fornecedor = codigo_fornecedor
    produto.qtd_estoque_produto = qtd_estoque_produto
    produto.valor_unitario_produto = valor_unitario_produto
    produto.marca_produto = marca_produto
    produto.data_validade_produto = data_validade_produto
    produto.peso_produto = peso_produto
    produto.custo_produto = custo_produto
    produto.imagem_binaria = imagem_binaria
    session.commit()  

def deletando_produto(id):
    produto = session.query(Produto).filter_by(id=f"{id}").first()
    session.delete(produto)
    session.commit()  


consulta_produtos()