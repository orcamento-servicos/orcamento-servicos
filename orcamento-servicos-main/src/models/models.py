# ========================================
# MODELOS DO BANCO DE DADOS
# Sistema de Orçamentos de Serviços
# ========================================

# Importações necessárias
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Inicializa o banco de dados
db = SQLAlchemy()

# ========================================
# MODELO: USUÁRIO
# Representa os usuários do sistema
# ========================================
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'
    
    # Campos da tabela
    id_usuario = db.Column(db.Integer, primary_key=True)  # ID único
    nome = db.Column(db.String(80), nullable=False)       # Nome completo
    email = db.Column(db.String(50), unique=True, nullable=False)  # Email (único)
    senha = db.Column(db.String(40), nullable=False)      # Senha criptografada
    perfil = db.Column(db.String(18), default='admin')    # Tipo de usuário
    
    # Relacionamentos (um usuário pode ter vários orçamentos e logs)
    orcamentos = db.relationship('Orcamento', backref='usuario', lazy=True)
    logs = db.relationship('LogsAcesso', backref='usuario', lazy=True)
    
    # Método obrigatório para o Flask-Login funcionar
    def get_id(self):
        return str(self.id_usuario)
    
    # Criptografa e salva a senha
    def definir_senha(self, senha):
        self.senha = generate_password_hash(senha)
    
    # Verifica se a senha digitada está correta
    def verificar_senha(self, senha):
        return check_password_hash(self.senha, senha)
    
    # Converte o usuário para formato JSON (para APIs)
    def para_dict(self):
        return {
            'id_usuario': self.id_usuario,
            'nome': self.nome,
            'email': self.email,
            'perfil': self.perfil
        }

# ========================================
# MODELO: CLIENTE
# Representa os clientes da empresa
# ========================================
class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    # Campos da tabela
    id_cliente = db.Column(db.Integer, primary_key=True)  # ID único
    nome = db.Column(db.String(80), nullable=False)       # Nome (obrigatório)
    telefone = db.Column(db.String(11))                   # Telefone (opcional)
    email = db.Column(db.String(50))                      # Email (opcional)
    endereco = db.Column(db.String(55))                   # Endereço (opcional)
    
    # Relacionamento (um cliente pode ter vários orçamentos)
    orcamentos = db.relationship('Orcamento', backref='cliente', lazy=True)
    
    # Converte o cliente para formato JSON
    def para_dict(self):
        return {
            'id_cliente': self.id_cliente,
            'nome': self.nome,
            'telefone': self.telefone,
            'email': self.email,
            'endereco': self.endereco
        }

# ========================================
# MODELO: SERVIÇO
# Representa os serviços oferecidos
# ========================================
class Servico(db.Model):
    __tablename__ = 'servicos'
    
    # Campos da tabela
    id_servicos = db.Column(db.Integer, primary_key=True)  # ID único
    nome = db.Column(db.String(80), nullable=False)        # Nome do serviço
    descricao = db.Column(db.String(255))                  # Descrição detalhada
    valor = db.Column(db.Numeric(10, 2), nullable=False)   # Preço do serviço
    
    # Relacionamento (um serviço pode estar em vários orçamentos)
    orcamento_servicos = db.relationship('OrcamentoServicos', backref='servico', lazy=True)
    
    # Converte o serviço para formato JSON
    def para_dict(self):
        return {
            'id_servicos': self.id_servicos,
            'nome': self.nome,
            'descricao': self.descricao,
            'valor': float(self.valor)  # Converte Decimal para float
        }

# ========================================
# MODELO: ORÇAMENTO
# Representa um orçamento criado
# ========================================
class Orcamento(db.Model):
    __tablename__ = 'orcamento'
    
    # Campos da tabela
    id_orcamento = db.Column(db.Integer, primary_key=True)  # ID único
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)  # Cliente
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)   # Usuário que criou
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)  # Data de criação
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)      # Valor total do orçamento
    status = db.Column(db.String(15), nullable=False, default='Pendente')  # Status do orçamento
    
    # Relacionamento (um orçamento pode ter vários serviços)
    orcamento_servicos = db.relationship('OrcamentoServicos', backref='orcamento', lazy=True, cascade='all, delete-orphan')
    
    # Converte o orçamento para formato JSON
    def para_dict(self):
        return {
            'id_orcamento': self.id_orcamento,
            'id_cliente': self.id_cliente,
            'id_usuario': self.id_usuario,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'valor_total': float(self.valor_total),
            'status': self.status,
            'cliente_nome': self.cliente.nome if self.cliente else None,
            'usuario_nome': self.usuario.nome if self.usuario else None
        }

# ========================================
# MODELO: ORÇAMENTO_SERVIÇOS
# Tabela de ligação entre orçamentos e serviços
# ========================================
class OrcamentoServicos(db.Model):
    __tablename__ = 'orcamento_servicos'
    
    # Chaves primárias compostas
    id_orcamento = db.Column(db.Integer, db.ForeignKey('orcamento.id_orcamento'), primary_key=True)
    id_servico = db.Column(db.Integer, db.ForeignKey('servicos.id_servicos'), primary_key=True)
    
    # Campos adicionais
    quantidade = db.Column(db.Integer, default=1)                    # Quantidade do serviço
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)    # Preço na época do orçamento
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)          # Quantidade × Valor unitário
    
    # Converte para formato JSON
    def para_dict(self):
        return {
            'id_orcamento': self.id_orcamento,
            'id_servico': self.id_servico,
            'quantidade': self.quantidade,
            'valor_unitario': float(self.valor_unitario),
            'subtotal': float(self.subtotal),
            'servico_nome': self.servico.nome if self.servico else None,
            'servico_descricao': self.servico.descricao if self.servico else None
        }

# ========================================
# MODELO: LOGS DE ACESSO
# Registra as ações dos usuários no sistema
# ========================================
class LogsAcesso(db.Model):
    __tablename__ = 'logs_acesso'
    
    # Campos da tabela
    id_log = db.Column(db.Integer, primary_key=True)       # ID único
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)  # Usuário
    acao = db.Column(db.String(100), nullable=False)       # Descrição da ação
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)  # Quando aconteceu
    
    # Converte para formato JSON
    def para_dict(self):
        return {
            'id_log': self.id_log,
            'id_usuario': self.id_usuario,
            'acao': self.acao,
            'data_hora': self.data_hora.isoformat() if self.data_hora else None,
            'usuario_nome': self.usuario.nome if self.usuario else None
        }

