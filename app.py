import re
from datetime import datetime, timezone

import requests
import streamlit as st

# ============================================================
# CONFIGURAÇÃO
# A URL do webhook do n8n fica em .streamlit/secrets.toml (local)
# ou nos "Secrets" do Streamlit Cloud (produção), como WEBHOOK_URL.
# Se não estiver configurada, o app roda em MODO DE TESTE.
# ============================================================
WEBHOOK_URL = st.secrets.get("WEBHOOK_URL", "")

st.set_page_config(page_title="Fale com a gente", page_icon="💬", layout="centered")

# ---- Estilo opcional ----
st.markdown(
    """
    <style>
      .stApp { background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%); }
      .bloco {
          background: #fff; padding: 32px; border-radius: 20px;
          box-shadow: 0 20px 60px rgba(0,0,0,0.2); max-width: 520px; margin: 0 auto;
      }
      .stButton button {
          width: 100%; background: #6c5ce7; color: #fff; font-weight: 600;
          border: none; padding: 12px; border-radius: 10px;
      }
      .stButton button:hover { background: #5b4bd4; color: #fff; }
    </style>
    """,
    unsafe_allow_html=True,
)


def email_valido(email: str) -> bool:
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email))


def telefone_valido(tel: str) -> bool:
    digitos = re.sub(r"\D", "", tel)
    return 10 <= len(digitos) <= 11


st.markdown('<div class="bloco">', unsafe_allow_html=True)
st.title("Fale com a gente 👋")
st.caption("Deixe seus dados e nossa equipe entra em contato rapidinho.")

with st.form("form_lead", clear_on_submit=True):
    nome = st.text_input("Nome *", placeholder="Seu nome completo")
    email = st.text_input("E-mail *", placeholder="voce@email.com")
    telefone = st.text_input("WhatsApp / Telefone *", placeholder="(11) 99999-9999")
    empresa = st.text_input("Empresa", placeholder="Nome da sua empresa (opcional)")
    mensagem = st.text_area("Mensagem", placeholder="Conte rapidamente o que você precisa (opcional)")
    consentimento = st.checkbox(
        "Autorizo o contato e o tratamento dos meus dados conforme a Política de Privacidade (LGPD)."
    )
    enviar = st.form_submit_button("Quero ser contatado")

if enviar:
    erros = []
    if len(nome.strip()) < 2:
        erros.append("Informe seu nome.")
    if not email_valido(email.strip()):
        erros.append("Informe um e-mail válido.")
    if not telefone_valido(telefone):
        erros.append("Informe um telefone válido com DDD.")
    if not consentimento:
        erros.append("É necessário aceitar o tratamento dos dados (LGPD).")

    if erros:
        for e in erros:
            st.error(e)
    else:
        dados = {
            "nome": nome.strip(),
            "email": email.strip(),
            "telefone": telefone.strip(),
            "telefone_digitos": re.sub(r"\D", "", telefone),
            "empresa": empresa.strip(),
            "mensagem": mensagem.strip(),
            "consentimento": True,
            "origem": "streamlit",
            "capturado_em": datetime.now(timezone.utc).isoformat(),
        }

        try:
            if not WEBHOOK_URL:
                # Modo de teste: sem webhook configurado
                st.info("Modo de teste (webhook não configurado). Lead capturado:")
                st.json(dados)
            else:
                resp = requests.post(WEBHOOK_URL, json=dados, timeout=10)
                resp.raise_for_status()
                st.success("✅ Recebemos seus dados! Em breve entraremos em contato.")
        except Exception as exc:  # noqa: BLE001
            st.error("Não foi possível enviar agora. Tente novamente em instantes.")
            st.caption(f"Detalhe técnico: {exc}")

st.markdown(
    '<p style="text-align:center;color:#636e72;font-size:12px;margin-top:16px;">'
    "🔒 Seus dados estão seguros e não serão compartilhados.</p>",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)
