import re
from datetime import datetime, timezone

import requests
import streamlit as st

# ============================================================
# CONFIGURAÇÃO
# Defina WEBHOOK_URL nos Secrets do Streamlit Cloud.
# Sem webhook configurado, o app roda em MODO DE TESTE.
# ============================================================
WEBHOOK_URL = st.secrets.get("WEBHOOK_URL", "")

st.set_page_config(page_title="Fale com a gente", page_icon="💬", layout="centered")

# ------------------------------------------------------------
# Estilo estilo Typeform
# ------------------------------------------------------------
st.markdown(
    """
    <style>
      /* Esconde elementos do Streamlit */
      #MainMenu, header, footer {visibility: hidden;}
      .stDeployButton {display: none;}
      .block-container {padding-top: 3rem; max-width: 720px;}

      .stApp {
        background: linear-gradient(135deg, #4834d4 0%, #6c5ce7 60%, #8e7cff 100%);
        color: #ffffff;
      }

      /* Pergunta */
      .pergunta {
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.25;
        color: #ffffff;
        margin-bottom: 6px;
      }
      .ajuda {
        font-size: 1rem;
        color: rgba(255,255,255,0.75);
        margin-bottom: 28px;
      }
      .passo-num {
        font-size: 0.95rem;
        color: rgba(255,255,255,0.85);
        margin-bottom: 10px;
        font-weight: 600;
      }

      /* Inputs grandes e limpos */
      input, textarea {
        background: transparent !important;
        color: #ffffff !important;
        font-size: 1.5rem !important;
        border: none !important;
        border-bottom: 2px solid rgba(255,255,255,0.4) !important;
        border-radius: 0 !important;
        padding: 6px 2px !important;
        box-shadow: none !important;
      }
      input:focus, textarea:focus {
        border-bottom: 2px solid #ffffff !important;
        box-shadow: none !important;
      }
      input::placeholder, textarea::placeholder {
        color: rgba(255,255,255,0.45) !important;
        font-size: 1.3rem !important;
      }
      div[data-baseweb="input"], div[data-baseweb="textarea"] {
        background: transparent !important;
        border: none !important;
      }

      /* Botão OK */
      .stButton button, .stFormSubmitButton button {
        background: #ffffff !important;
        color: #4834d4 !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 26px !important;
        margin-top: 18px;
      }
      .stButton button:hover, .stFormSubmitButton button:hover {
        background: #f1f0ff !important;
        color: #4834d4 !important;
      }

      /* Barra de progresso */
      .stProgress > div > div > div > div {background-color: #ffffff;}

      .dica-enter {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.7);
        margin-top: 8px;
      }
      label {color: #ffffff !important; font-size: 1.05rem !important;}

      /* Checkbox */
      .stCheckbox label {color: rgba(255,255,255,0.9) !important; font-size: 0.95rem !important;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Validações
# ------------------------------------------------------------
def email_valido(v: str) -> bool:
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", v.strip()))


def telefone_valido(v: str) -> bool:
    return 10 <= len(re.sub(r"\D", "", v)) <= 11


def nao_vazio(v: str) -> bool:
    return len(v.strip()) >= 2


# ------------------------------------------------------------
# Definição das perguntas (uma por tela)
# ------------------------------------------------------------
PERGUNTAS = [
    {
        "chave": "nome",
        "titulo": "Qual é o seu nome?",
        "ajuda": "Pode ser só o primeiro 🙂",
        "placeholder": "Digite seu nome aqui...",
        "tipo": "text",
        "validar": nao_vazio,
        "erro": "Por favor, informe seu nome.",
    },
    {
        "chave": "email",
        "titulo": "Qual o seu melhor e-mail?",
        "ajuda": "É por onde podemos te retornar.",
        "placeholder": "voce@email.com",
        "tipo": "text",
        "validar": email_valido,
        "erro": "Informe um e-mail válido.",
    },
    {
        "chave": "telefone",
        "titulo": "E o seu WhatsApp?",
        "ajuda": "Com DDD, por favor.",
        "placeholder": "(11) 99999-9999",
        "tipo": "text",
        "validar": telefone_valido,
        "erro": "Informe um telefone válido com DDD.",
    },
    {
        "chave": "empresa",
        "titulo": "Você representa alguma empresa?",
        "ajuda": "Se for pessoal, é só deixar em branco e avançar.",
        "placeholder": "Nome da empresa (opcional)",
        "tipo": "text",
        "validar": None,  # opcional
        "erro": "",
    },
    {
        "chave": "mensagem",
        "titulo": "Como podemos te ajudar?",
        "ajuda": "Conte rapidamente o que você precisa (opcional).",
        "placeholder": "Escreva aqui...",
        "tipo": "textarea",
        "validar": None,  # opcional
        "erro": "",
    },
]

TOTAL = len(PERGUNTAS) + 1  # +1 = tela de consentimento/envio

# ------------------------------------------------------------
# Estado
# ------------------------------------------------------------
if "passo" not in st.session_state:
    st.session_state.passo = 0
if "respostas" not in st.session_state:
    st.session_state.respostas = {}
if "enviado" not in st.session_state:
    st.session_state.enviado = False


def avancar():
    st.session_state.passo += 1


def voltar():
    if st.session_state.passo > 0:
        st.session_state.passo -= 1


def enviar_lead():
    dados = {
        **st.session_state.respostas,
        "telefone_digitos": re.sub(r"\D", "", st.session_state.respostas.get("telefone", "")),
        "consentimento": True,
        "origem": "streamlit",
        "capturado_em": datetime.now(timezone.utc).isoformat(),
    }
    if not WEBHOOK_URL:
        st.session_state.modo_teste = dados
        return True
    resp = requests.post(WEBHOOK_URL, json=dados, timeout=10)
    resp.raise_for_status()
    return True


# ------------------------------------------------------------
# Tela final (sucesso)
# ------------------------------------------------------------
if st.session_state.enviado:
    st.progress(1.0)
    st.markdown('<div class="pergunta">Tudo certo! 🎉</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="ajuda">Recebemos seus dados e em breve nossa equipe entra em contato.</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.get("modo_teste"):
        st.info("Modo de teste (webhook não configurado). Lead capturado:")
        st.json(st.session_state.modo_teste)
    if st.button("Enviar outra resposta"):
        st.session_state.passo = 0
        st.session_state.respostas = {}
        st.session_state.enviado = False
        st.session_state.pop("modo_teste", None)
        st.rerun()
    st.stop()

# ------------------------------------------------------------
# Barra de progresso
# ------------------------------------------------------------
st.progress(st.session_state.passo / TOTAL)

passo = st.session_state.passo

# ------------------------------------------------------------
# Telas de perguntas
# ------------------------------------------------------------
if passo < len(PERGUNTAS):
    p = PERGUNTAS[passo]
    st.markdown(f'<div class="passo-num">{passo + 1} → {TOTAL}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pergunta">{p["titulo"]}</div>', unsafe_allow_html=True)
    if p["ajuda"]:
        st.markdown(f'<div class="ajuda">{p["ajuda"]}</div>', unsafe_allow_html=True)

    with st.form(f"form_{p['chave']}", clear_on_submit=False):
        valor_atual = st.session_state.respostas.get(p["chave"], "")
        if p["tipo"] == "textarea":
            valor = st.text_area(" ", value=valor_atual, placeholder=p["placeholder"], label_visibility="collapsed")
        else:
            valor = st.text_input(" ", value=valor_atual, placeholder=p["placeholder"], label_visibility="collapsed")

        col1, col2 = st.columns([1, 5])
        with col1:
            ok = st.form_submit_button("OK ✓")
        st.markdown('<div class="dica-enter">pressione <b>Enter ↵</b> para avançar</div>', unsafe_allow_html=True)

    if ok:
        if p["validar"] and not p["validar"](valor):
            st.error(p["erro"])
        else:
            st.session_state.respostas[p["chave"]] = valor.strip()
            avancar()
            st.rerun()

    if passo > 0:
        if st.button("← Voltar"):
            voltar()
            st.rerun()

# ------------------------------------------------------------
# Tela de consentimento + envio
# ------------------------------------------------------------
else:
    st.markdown(f'<div class="passo-num">{TOTAL} → {TOTAL}</div>', unsafe_allow_html=True)
    st.markdown('<div class="pergunta">Quase lá! 🚀</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="ajuda">Confirme o consentimento para finalizarmos.</div>',
        unsafe_allow_html=True,
    )

    consentimento = st.checkbox(
        "Autorizo o contato e o tratamento dos meus dados conforme a Política de Privacidade (LGPD)."
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Enviar ✓"):
            if not consentimento:
                st.error("É necessário aceitar o tratamento dos dados (LGPD).")
            else:
                try:
                    enviar_lead()
                    st.session_state.enviado = True
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error("Não foi possível enviar agora. Tente novamente em instantes.")
                    st.caption(f"Detalhe técnico: {exc}")
    with col2:
        if st.button("← Voltar"):
            voltar()
            st.rerun()
