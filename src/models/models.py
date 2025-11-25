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
    telefone = db.Column(db.String(15))                   # Telefone (opcional)
    senha = db.Column(db.String(255), nullable=False)     # Senha criptografada (hash)
    perfil = db.Column(db.String(18), default='admin')    # Tipo de usuário
    status = db.Column(db.String(20), default='Online')   # Status do usuário
    avatar_url = db.Column(db.String(255))                # URL da imagem de perfil
    
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
            'telefone': self.telefone,
            'perfil': self.perfil,
            'status': self.status,
            'avatar_url': self.avatar_url
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
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresas.id_empresa'), nullable=True)   # Empresa emissora
    # Endereço selecionado no momento do orçamento (opcional)
    id_endereco = db.Column(db.Integer, db.ForeignKey('enderecos.id_endereco'), nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)  # Data de criação
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)      # Valor total do orçamento
    status = db.Column(db.String(15), nullable=False, default='Pendente')  # Status do orçamento
    
    # Relacionamento (um orçamento pode ter vários serviços)
    orcamento_servicos = db.relationship('OrcamentoServicos', backref='orcamento', lazy=True, cascade='all, delete-orphan')
    # Relacionamento com Endereco
    endereco = db.relationship('Endereco', backref='orcamentos', lazy=True)
    empresa = db.relationship('Empresa', backref='orcamentos', lazy=True)
    
    # Converte o orçamento para formato JSON
    def para_dict(self):
        return {
            'id_orcamento': self.id_orcamento,
            'id_cliente': self.id_cliente,
            'id_usuario': self.id_usuario,
            'id_empresa': self.id_empresa,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'valor_total': float(self.valor_total),
            'status': self.status,
            'cliente_nome': self.cliente.nome if self.cliente else None,
            'usuario_nome': self.usuario.nome if self.usuario else None,
            'empresa_nome': self.empresa.nome if self.empresa else None,
            'id_endereco': self.id_endereco
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

# ========================================
# MODELO: ENDEREÇO (múltiplos endereços por cliente)
# ========================================
class Endereco(db.Model):
    __tablename__ = 'enderecos'

    id_endereco = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    logradouro = db.Column(db.String(120), nullable=False)
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(60))
    bairro = db.Column(db.String(80))
    cidade = db.Column(db.String(80))
    uf = db.Column(db.String(2))
    cep = db.Column(db.String(10))
    apelido = db.Column(db.String(40))
    is_padrao = db.Column(db.Boolean, default=False)

    def para_dict(self):
        return {
            'id_endereco': self.id_endereco,
            'id_cliente': self.id_cliente,
            'logradouro': self.logradouro,
            'numero': self.numero,
            'complemento': self.complemento,
            'bairro': self.bairro,
            'cidade': self.cidade,
            'uf': self.uf,
            'cep': self.cep,
            'apelido': self.apelido,
            'is_padrao': self.is_padrao,
        }

# Relacionamento em Cliente
Cliente.enderecos = db.relationship('Endereco', backref='cliente', lazy=True, cascade='all, delete-orphan')


# ========================================
# MODELOS: VENDAS (conversão de orçamento)
# ========================================
# MODELO: EMPRESA
# Representa as empresas cadastradas
# ========================================
class Empresa(db.Model):
    __tablename__ = 'empresas'
    id_empresa = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    cnpj = db.Column(db.String(14), nullable=False, unique=True)
    telefone = db.Column(db.String(11))
    endereco = db.Column(db.String(55))
    email = db.Column(db.String(50))
    logo = db.Column(db.String(255))  # Caminho do arquivo da logo

    def para_dict(self):
        return {
            'id_empresa': self.id_empresa,
            'nome': self.nome,
            'cnpj': self.cnpj,
            'telefone': self.telefone,
            'endereco': self.endereco,
            'email': self.email,
            'logo': self.logo
        }
# ========================================
class Venda(db.Model):
    __tablename__ = 'vendas'

    id_venda = db.Column(db.Integer, primary_key=True)
    id_orcamento = db.Column(db.Integer, db.ForeignKey('orcamento.id_orcamento'), unique=True, nullable=False)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    data_venda = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    codigo_venda = db.Column(db.String(40), unique=True, nullable=False)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)

    itens = db.relationship('VendaItem', backref='venda', lazy=True, cascade='all, delete-orphan')

    def para_dict(self):
        return {
            'id_venda': self.id_venda,
            'id_orcamento': self.id_orcamento,
            'id_cliente': self.id_cliente,
            'id_usuario': self.id_usuario,
            'data_venda': self.data_venda.isoformat() if self.data_venda else None,
            'codigo_venda': self.codigo_venda,
            'valor_total': float(self.valor_total),
        }


class VendaItem(db.Model):
    __tablename__ = 'venda_itens'

    id_item = db.Column(db.Integer, primary_key=True)
    id_venda = db.Column(db.Integer, db.ForeignKey('vendas.id_venda'), nullable=False)
    id_servico = db.Column(db.Integer, db.ForeignKey('servicos.id_servicos'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    def para_dict(self):
        return {
            'id_item': self.id_item,
            'id_venda': self.id_venda,
            'id_servico': self.id_servico,
            'quantidade': self.quantidade,
            'valor_unitario': float(self.valor_unitario),
            'subtotal': float(self.subtotal),
        }


# ========================================
# MODELO: AGENDAMENTO
# Representa os agendamentos de serviços
# ========================================
class Agendamento(db.Model):
    __tablename__ = 'agendamentos'
    
    # Campos da tabela
    id_agendamento = db.Column(db.Integer, primary_key=True)  # ID único
    id_servico = db.Column(db.Integer, db.ForeignKey('servicos.id_servicos'), nullable=False)  # Serviço agendado
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)   # Usuário que criou
    data_hora = db.Column(db.DateTime, nullable=False)        # Data e hora do agendamento
    valor = db.Column(db.Numeric(10, 2), nullable=False)      # Valor do serviço na época do agendamento
    status = db.Column(db.String(20), default='Agendado')     # Status: Agendado, Concluído, Cancelado
    observacoes = db.Column(db.Text)                          # Observações adicionais
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Data de criação
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Data de atualização
    
    # Relacionamentos
    servico = db.relationship('Servico', backref='agendamentos', lazy=True)
    usuario = db.relationship('Usuario', backref='agendamentos', lazy=True)
    
    # Converte o agendamento para formato JSON
    def para_dict(self):
        return {
            'id_agendamento': self.id_agendamento,
            'id_servico': self.id_servico,
            'id_usuario': self.id_usuario,
            'data_hora': self.data_hora.isoformat() if self.data_hora else None,
            'valor': float(self.valor),
            'status': self.status,
            'observacoes': self.observacoes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'servico_nome': self.servico.nome if self.servico else None,
            'servico_descricao': self.servico.descricao if self.servico else None,
            'usuario_nome': self.usuario.nome if self.usuario else None
        }

# ========================================
# MODELO: TOKEN DE RECUPERAÇÃO DE SENHA
# ========================================
class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'

    id_token = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)

    def para_dict(self):
        return {
            'id_token': self.id_token,
            'id_usuario': self.id_usuario,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used_at': self.used_at.isoformat() if self.used_at else None,
        }