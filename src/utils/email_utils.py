import os
import smtplib
from email.message import EmailMessage
from typing import List, Optional


def _get_env(key_names, default=None):
    for k in key_names:
        v = os.environ.get(k)
        if v:
            return v
    return default


def get_smtp_config():
    """Retorna um dicionário com configuração SMTP, tentando nomes alternativos usados no projeto."""
    host = _get_env(['SMTP_HOST', 'SMTP_SERVER'])
    user = _get_env(['SMTP_USER', 'SMTP_USERNAME'])
    password = _get_env(['SMTP_PASS', 'SMTP_PASSWORD'])
    port = int(os.environ.get('SMTP_PORT', os.environ.get('SMTP_SMTP_PORT', '587')))
    tls = os.environ.get('SMTP_TLS', 'true').lower() in ('1', 'true', 'yes')
    mail_from = _get_env(['SMTP_FROM', 'SMTP_SENDER', 'SMTP_FROM_ADDRESS']) or user
    timeout = int(os.environ.get('SMTP_TIMEOUT', '20'))
    return {
        'host': host,
        'user': user,
        'password': password,
        'port': port,
        'tls': tls,
        'mail_from': mail_from,
        'timeout': timeout,
    }


def send_email(subject: str, body: str, to: List[str], attachments: Optional[List[dict]] = None) -> (bool, str):
    cfg = get_smtp_config()
    if not cfg['host'] or not cfg['user'] or not cfg['password']:
        return False, 'Configuração SMTP incompleta (host/user/password)'

    msg = EmailMessage()
    msg['From'] = cfg['mail_from']
    msg['To'] = ', '.join(to)
    msg['Subject'] = subject
    msg.set_content(body)

    if attachments:
        for att in attachments:
            try:
                msg.add_attachment(att['content'], maintype=att.get('maintype', 'application'), subtype=att.get('subtype', 'octet-stream'), filename=att.get('filename'))
            except Exception as e:
                return False, f'Falha ao anexar arquivo: {e}'

    try:
        # Lógica INTELIGENTE: Se for porta 465, usa conexão segura direta (SSL)
        if cfg['port'] == 465:
            server = smtplib.SMTP_SSL(cfg['host'], cfg['port'], timeout=cfg['timeout'])
        else:
            server = smtplib.SMTP(cfg['host'], cfg['port'], timeout=cfg['timeout'])
            if cfg['tls']:
                server.starttls()
        
        with server:
            server.login(cfg['user'], cfg['password'])
            server.send_message(msg)
        return True, 'OK'
    except smtplib.SMTPAuthenticationError as e:
        return False, f'Autenticação SMTP falhou: {e}'
    except smtplib.SMTPConnectError as e:
        return False, f'Erro de conexão SMTP: {e}'
    except Exception as e:
        return False, f'Erro ao enviar e-mail: {e}'