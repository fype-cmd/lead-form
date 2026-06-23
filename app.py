import re
from datetime import datetime, timezone

import requests
import streamlit as st

# ============================================================
# CONFIGURAÇÃO
# - WEBHOOK_URL: defina nos Secrets do Streamlit Cloud (n8n).
# - IMAGEM_CAPA: URL da imagem da capa (ou deixe vazio p/ placeholder).
# - LINK_AGENDAMENTO: URL do Calendly/agenda (botão final).
# ============================================================
WEBHOOK_URL = st.secrets.get("WEBHOOK_URL", "")
IMAGEM_CAPA = st.secrets.get("IMAGEM_CAPA", "")  # ex.: link de uma imagem .jpg/.png
LINK_AGENDAMENTO = st.secrets.get("LINK_AGENDAMENTO", "")  # ex.: https://calendly.com/...

st.set_page_config(page_title="Tráfego pago p/ distribuidoras", page_icon="📦", layout="centered")

# ------------------------------------------------------------
# Estilo estilo Typeform (tema claro)
# ------------------------------------------------------------
st.markdown(
    """
    <style>
      #MainMenu, header, footer {visibility: hidden;}
      .stDeployButton {display: none;}
      .stApp {background: #ffffff;}
      .block-container {padding-top: 4rem; padding-bottom: 4rem; max-width: 720px;}

      /* Numero do passo */
      .passo-num {color:#2f6fed; font-weight:600; font-size:0.95rem; margin-bottom:8px;}

      /* Pergunta e ajuda */
      .pergunta {font-size: 1.9rem; font-weight: 600; line-height: 1.3; color:#243044; margin-bottom:6px;}
      .ajuda {font-size: 1rem; color:#9aa3af; margin-bottom: 26px;}

      /* Inputs: linha azul, placeholder azul claro */
      input, textarea {
        background: transparent !important;
        color: #243044 !important;
        font-size: 1.4rem !important;
        border: none !important;
        border-bottom: 1.5px solid #2f6fed !important;
        border-radius: 0 !important;
        padding: 6px 2px !important;
        box-shadow: none !important;
      }
      input:focus, textarea:focus {box-shadow: none !important; border-bottom: 1.5px solid #1f4fd0 !important;}
      input::placeholder, textarea::placeholder {color:#8bb4f0 !important; font-size: 1.25rem !important;}
      div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="base-input"] {
        background: transparent !important; border: none !important;
      }

      /* Botoes de OPCAO (multipla escolha) = secondary */
      .stButton button[kind="secondary"] {
        width: 100%;
        text-align: left !important;
        justify-content: flex-start !important;
        background: #ffffff !important;
        color: #2f6fed !important;
        border: 1.5px solid #cfe0fb !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        margin-bottom: 4px;
      }
      .stButton button[kind="secondary"]:hover {
        background: #f3f8ff !important; border-color: #2f6fed !important; color:#1f4fd0 !important;
      }

      /* Botao CTA principal = primary */
      .stButton button[kind="primary"], .stFormSubmitButton button {
        background: #2f6fed !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 28px !important;
        letter-spacing: .3px;
      }
      .stButton button[kind="primary"]:hover, .stFormSubmitButton button:hover {background:#1f4fd0 !important;}

      .bullets {font-size: 1rem; color:#3a4658; line-height: 2;}
      .obs {font-size: .92rem; color:#9aa3af; font-style: italic; margin: 14px 0 22px;}
      .capa-titulo {font-size: 1.5rem; color:#243044; line-height:1.4; margin-bottom:18px;}
      .dica-enter {font-size: .82rem; color:#9aa3af; margin-top:6px;}

      .espere {text-align:center;}
      .espere h1 {font-size: 2.4rem; color:#111; font-weight:800; letter-spacing:1px; margin-bottom:0;}
      .espere .pct {font-size: 2.2rem; color:#f5821f; font-weight:800;}
      .espere p {font-size: 1.3rem; color:#243044; font-weight:700; margin-top:8px;}

      /* Placeholder de imagem da capa */
      .capa-img-ph {
        width:100%; aspect-ratio: 4/3; border-radius:10px;
        background: linear-gradient(135deg,#1e3a8a,#2f6fed);
        display:flex; align-items:center; justify-content:center; color:#cfe0fb; font-size:2.4rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Validações
# ------------------------------------------------------------
def telefone_valido(v: str) -> bool:
    return 10 <= len(re.sub(r"\D", "", v)) <= 11


def nao_vazio(v: str) -> bool:
    return len(v.strip()) >= 2


# ------------------------------------------------------------
# Estado
# ------------------------------------------------------------
if "passo" not in st.session_state:
    st.session_state.passo = "capa"
if "respostas" not in st.session_state:
    st.session_state.respostas = {}

R = st.session_state.respostas


def ir(passo: str):
    st.session_state.passo = passo
    st.rerun()


# Ordem das perguntas (para a barra de progresso)
ORDEM = ["nome", "whatsapp", "instagram", "faturamento", "investimento"]


def progresso(passo):
    if passo in ORDEM:
        return (ORDEM.index(passo)) / (len(ORDEM) + 1)
    return None


def enviar_lead(qualificado: bool):
    dados = {
        "nome": R.get("nome", ""),
        "whatsapp": R.get("whatsapp", ""),
        "whatsapp_digitos": re.sub(r"\D", "", R.get("whatsapp", "")),
        "instagram": R.get("instagram", ""),
        "faturamento": R.get("faturamento", ""),
        "disposto_investir": R.get("investimento", ""),
        "observacao": R.get("desqualificacao", ""),
        "qualificado": qualificado,
        "origem": "streamlit-quiz",
        "capturado_em": datetime.now(timezone.utc).isoformat(),
    }
    if not WEBHOOK_URL:
        st.session_state.modo_teste = dados
        return
    resp = requests.post(WEBHOOK_URL, json=dados, timeout=10)
    resp.raise_for_status()


# ------------------------------------------------------------
# Helpers de UI
# ------------------------------------------------------------
def cabecalho_pergunta(passo, titulo, ajuda="Se desejar, adicione uma descrição..."):
    p = progresso(passo)
    if p is not None:
        st.progress(p)
    st.markdown(f'<div class="pergunta">{titulo}</div>', unsafe_allow_html=True)
    if ajuda:
        st.markdown(f'<div class="ajuda">{ajuda}</div>', unsafe_allow_html=True)


def tela_texto(passo, titulo, placeholder, proximo, validar=None, erro="", ajuda="Se desejar, adicione uma descrição...", multiline=False):
    cabecalho_pergunta(passo, titulo, ajuda)
    with st.form(f"f_{passo}"):
        atual = R.get(passo, "")
        if multiline:
            val = st.text_area(" ", value=atual, placeholder=placeholder, label_visibility="collapsed")
        else:
            val = st.text_input(" ", value=atual, placeholder=placeholder, label_visibility="collapsed")
        ok = st.form_submit_button("OK  ✓")
        st.markdown('<div class="dica-enter">pressione <b>Enter ↵</b></div>', unsafe_allow_html=True)
    if ok:
        if validar and not validar(val):
            st.error(erro)
        else:
            R[passo] = val.strip()
            ir(proximo)
    if st.button("← Voltar", key=f"v_{passo}"):
        ir(_anterior(passo))


def tela_opcoes(passo, titulo, opcoes, ao_escolher):
    """opcoes: lista de (letra, texto). ao_escolher(texto_completo) define o próximo passo."""
    cabecalho_pergunta(passo, titulo)
    for letra, texto in opcoes:
        if st.button(f"{letra}    {texto}", key=f"{passo}_{letra}", type="secondary"):
            R[passo] = f"{letra}) {texto}"
            ao_escolher(f"{letra}) {texto}")
    if st.button("← Voltar", key=f"v_{passo}"):
        ir(_anterior(passo))


FLUXO_LINEAR = ["capa", "nome", "whatsapp", "instagram", "faturamento", "investimento"]


def _anterior(passo):
    if passo in FLUXO_LINEAR:
        i = FLUXO_LINEAR.index(passo)
        return FLUXO_LINEAR[max(0, i - 1)]
    if passo == "desqualificacao":
        return "investimento"
    return "capa"


# ============================================================
# TELAS
# ============================================================
passo = st.session_state.passo

# ---- CAPA ----
if passo == "capa":
    col_img, col_txt = st.columns([1, 1], gap="large")
    with col_img:
        if IMAGEM_CAPA:
            st.image(IMAGEM_CAPA, use_container_width=True)
        else:
            st.markdown('<div class="capa-img-ph">📦</div>', unsafe_allow_html=True)
    with col_txt:
        st.markdown(
            '<div class="capa-titulo">🧊 <b>Tráfego pago</b> para distribuidoras de '
            'limpeza/descartáveis que querem <b>mais e novas empresas e condomínios</b> na carteira</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="bullets">'
            "🚩 Leads novos todos os dias<br>"
            "✅ <b>Empresas que preferem qualidade</b><br>"
            "✅ Método validado em 250+ empresas<br>"
            "🏅 <b>Seja a nº1 da sua cidade e região</b>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="obs">➜ Apenas para distribuidoras que faturam R$100k+ por mês '
            "e dispostas a investir ao menos R$2k em anúncios</div>",
            unsafe_allow_html=True,
        )
        if st.button("QUERO + CLIENTES NA CARTEIRA  →", type="primary"):
            ir("nome")

# ---- NOME ----
elif passo == "nome":
    tela_texto("nome", "Qual seu nome e sobrenome?", "Sua resposta...", "whatsapp",
               validar=nao_vazio, erro="Por favor, informe seu nome.")

# ---- WHATSAPP ----
elif passo == "whatsapp":
    tela_texto("whatsapp", "Qual seu WhatsApp (com DDD)?", "Um número...", "instagram",
               validar=telefone_valido, erro="Informe um número válido com DDD.")

# ---- INSTAGRAM ----
elif passo == "instagram":
    tela_texto("instagram", "Qual o @ do instagram da sua distribuidora?", "Sua resposta...", "faturamento",
               validar=nao_vazio, erro="Por favor, informe o @ do Instagram.")

# ---- FATURAMENTO ----
elif passo == "faturamento":
    opcoes = [
        ("A", "Ainda não estou faturando"),
        ("B", "Menos de R$50.000 por mês"),
        ("C", "De R$50.001 a R$100.000 por mês"),
        ("D", "De R$100.001 a R$250.000 por mês"),
        ("E", "De R$250.001 a R$500.000 por mês"),
        ("F", "De R$500.001 a R$1.000.000 por mês"),
        ("G", "Acima de R$1.000.000 por mês"),
    ]
    tela_opcoes("faturamento", "Qual o faturamento médio mensal do seu negócio?", opcoes,
                ao_escolher=lambda _: ir("investimento"))

# ---- INVESTIMENTO (branch) ----
elif passo == "investimento":
    opcoes = [
        ("A", "Sim! É o que eu preciso e estou disposto!"),
        ("B", "Não estou disposto a investir no meu negócio."),
    ]

    def _escolha_invest(valor):
        if valor.startswith("B"):
            ir("desqualificacao")
        else:
            ir("final")

    tela_opcoes(
        "investimento",
        "Nossa mão de obra se inicia em R$ 1.490 por mês. Está disposto a investir esse valor "
        "e elevar seu negócio a um novo patamar de faturamento e vendas?",
        opcoes,
        ao_escolher=_escolha_invest,
    )

# ---- DESQUALIFICAÇÃO ----
elif passo == "desqualificacao":
    st.markdown(
        '<div class="pergunta">Para ter acesso aos nossos serviços, '
        "<b>o investimento é necessário</b>. Infelizmente não conseguimos seguir adiante se você "
        "não tiver essa abertura ou for um montante excessivo para o momento da sua distribuidora.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ajuda">Caso você tenha preenchido errado e consiga fazer o investimento, '
        "basta colocar sua resposta em texto fazendo essa retificação e nos passando os motivos "
        "para entrarmos em contato com você.</div>",
        unsafe_allow_html=True,
    )
    with st.form("f_desq"):
        val = st.text_area(" ", value=R.get("desqualificacao", ""), placeholder="Sua resposta...", label_visibility="collapsed")
        ok = st.form_submit_button("Enviar  ✓")
    if ok:
        R["desqualificacao"] = val.strip()
        # Se reconsiderou (escreveu algo), trata como lead; senão, encerra como não-qualificado
        try:
            enviar_lead(qualificado=bool(val.strip()))
            ir("final")
        except Exception as exc:  # noqa: BLE001
            st.error("Não foi possível enviar agora. Tente novamente.")
            st.caption(f"Detalhe técnico: {exc}")
    if st.button("← Voltar", key="v_desq"):
        ir("investimento")

# ---- FINAL ----
elif passo == "final":
    # Garante o envio do lead qualificado (caso tenha vindo pelo fluxo A)
    if not st.session_state.get("enviado_final") and "desqualificacao" not in R:
        try:
            enviar_lead(qualificado=True)
            st.session_state.enviado_final = True
        except Exception as exc:  # noqa: BLE001
            st.error("Não foi possível registrar agora. Tente novamente.")
            st.caption(f"Detalhe técnico: {exc}")

    st.markdown(
        '<div class="espere">'
        "<h1>ESPERE!</h1>"
        '<div class="pct">98% PREENCHIDO</div>'
        "<p>agende agora uma breve reunião com um de nossos especialistas ↓</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    col = st.columns([1, 2, 1])[1]
    with col:
        if LINK_AGENDAMENTO:
            st.link_button("✓ ESTOU PRONTO(A)", LINK_AGENDAMENTO, use_container_width=True)
        else:
            if st.button("✓ ESTOU PRONTO(A)", type="primary", use_container_width=True):
                st.success("✅ Recebemos seus dados! Em breve nossa equipe entra em contato.")

    if st.session_state.get("modo_teste"):
        with st.expander("🔧 Modo de teste — lead capturado (webhook não configurado)"):
            st.json(st.session_state.modo_teste)
