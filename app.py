import re
from datetime import datetime, timezone

import requests
import streamlit as st
import streamlit.components.v1 as components

# ============================================================
# CONFIGURAÇÃO (Secrets do Streamlit Cloud)
# - WEBHOOK_URL: endpoint do n8n.
# - IMAGEM_CAPA: URL da imagem da capa (ou vazio p/ placeholder).
# - LINK_AGENDAMENTO: URL do Calendly/agenda (botão final).
# ============================================================
WEBHOOK_URL = st.secrets.get("WEBHOOK_URL", "")
IMAGEM_CAPA = st.secrets.get("IMAGEM_CAPA", "")
LINK_AGENDAMENTO = st.secrets.get("LINK_AGENDAMENTO", "")
META_PIXEL_ID = st.secrets.get("META_PIXEL_ID", "")  # ex.: 123456789012345

st.set_page_config(page_title="Tráfego pago p/ distribuidoras", page_icon="📦", layout="centered")

# ------------------------------------------------------------
# Estilo (Typeform-like, tema claro)
# ------------------------------------------------------------
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

      html, body, [class*="css"], input, textarea, button, p, div, span, h1, h2, h3 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
      }

      #MainMenu, header, footer {visibility: hidden;}
      .stDeployButton {display: none;}
      .stApp {background: #ffffff;}
      .block-container {padding-top: 6vh; padding-bottom: 4rem; max-width: 680px;}

      /* Animação de entrada a cada tela (sensação de transição) */
      @keyframes surge {
        from {opacity: 0; transform: translateY(14px);}
        to   {opacity: 1; transform: translateY(0);}
      }
      .block-container {animation: surge .38s cubic-bezier(.21,.61,.35,1);}

      /* Pergunta e ajuda */
      .pergunta {
        font-size: 2rem; font-weight: 600; line-height: 1.32;
        color: #1f2a3a; margin-bottom: 8px; letter-spacing: -.01em;
      }
      .ajuda {font-size: 1.02rem; color: #9aa3af; margin-bottom: 30px; line-height: 1.5;}

      /* Inputs: linha azul, placeholder azul claro */
      input, textarea {
        background: transparent !important;
        color: #1f2a3a !important;
        font-size: 1.5rem !important;
        border: none !important;
        border-bottom: 2px solid #d4e2fb !important;
        border-radius: 0 !important;
        padding: 8px 2px !important;
        box-shadow: none !important;
        transition: border-color .2s ease;
      }
      input:focus, textarea:focus {box-shadow: none !important; border-bottom: 2px solid #2f6fed !important;}
      input::placeholder, textarea::placeholder {color: #9cc0f5 !important; font-size: 1.35rem !important;}
      div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="base-input"] {
        background: transparent !important; border: none !important;
      }

      /* Botões de OPÇÃO (múltipla escolha) = secondary */
      .stButton button[kind="secondary"] {
        width: 100%;
        text-align: left !important;
        justify-content: flex-start !important;
        background: #ffffff !important;
        color: #2f6fed !important;
        border: 1.5px solid #d4e2fb !important;
        border-radius: 12px !important;
        padding: 16px 18px !important;
        font-size: 1.08rem !important;
        font-weight: 500 !important;
        margin-bottom: 10px;
        box-shadow: 0 2px 6px rgba(47,111,237,0.06);
        transition: all .16s ease;
      }
      .stButton button[kind="secondary"]:hover {
        background: #f5f9ff !important;
        border-color: #2f6fed !important;
        color: #1f4fd0 !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(47,111,237,0.16);
      }

      /* Botão CTA principal = primary / submit */
      .stButton button[kind="primary"], .stFormSubmitButton button {
        background: linear-gradient(135deg, #2f6fed, #1f4fd0) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 13px 30px !important;
        letter-spacing: .4px;
        box-shadow: 0 6px 18px rgba(47,111,237,0.28);
        transition: all .16s ease;
      }
      .stButton button[kind="primary"]:hover, .stFormSubmitButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 26px rgba(47,111,237,0.36);
      }

      /* Botão Voltar discreto */
      .voltar a, .voltar button {color:#9aa3af !important;}

      /* Barra de progresso fina e azul */
      .stProgress {margin-bottom: 26px;}
      .stProgress > div > div > div {background-color: #eef3fb !important; height: 6px !important;}
      .stProgress > div > div > div > div {background: linear-gradient(90deg,#2f6fed,#5b8df5) !important;}

      .bullets {font-size: 1.02rem; color: #3a4658; line-height: 2.05;}
      .obs {font-size: .92rem; color: #9aa3af; font-style: italic; margin: 16px 0 24px; line-height:1.5;}
      .capa-titulo {font-size: 1.5rem; color: #1f2a3a; line-height: 1.42; margin-bottom: 18px;}
      .dica-enter {font-size: .82rem; color: #b3bac4; margin-top: 8px;}

      .espere {text-align: center; padding-top: 4vh;}
      .espere h1 {font-size: 2.6rem; color: #0f1115; font-weight: 800; letter-spacing: 1.5px; margin-bottom: 0;}
      .espere .pct {font-size: 2.3rem; color: #f5821f; font-weight: 800; margin: 4px 0 10px;}
      .espere p {font-size: 1.3rem; color: #1f2a3a; font-weight: 700; line-height: 1.4;}

      .capa-img-ph {
        width: 100%; aspect-ratio: 4/3; border-radius: 14px;
        background: linear-gradient(135deg,#1e3a8a,#2f6fed);
        display: flex; align-items: center; justify-content: center;
        color: #cfe0fb; font-size: 2.6rem;
        box-shadow: 0 12px 30px rgba(31,58,138,0.25);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# Meta Pixel — carrega o base + PageView uma única vez (no documento pai)
# ------------------------------------------------------------
if META_PIXEL_ID and not st.session_state.get("pixel_base_carregado"):
    components.html(
        f"""
        <script>
        (function (f, b, e, v) {{
          if (f.fbq) return;
          var n = f.fbq = function () {{
            n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
          }};
          if (!f._fbq) f._fbq = n;
          n.push = n; n.loaded = !0; n.version = '2.0'; n.queue = [];
          var t = b.createElement(e); t.async = !0; t.src = v;
          var s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s);
        }})(window.parent, window.parent.document, 'script',
            'https://connect.facebook.net/en_US/fbevents.js');
        window.parent.fbq('init', '{META_PIXEL_ID}');
        window.parent.fbq('track', 'PageView');
        </script>
        """,
        height=0,
    )
    st.session_state.pixel_base_carregado = True


def disparar_evento_lead():
    """Dispara fbq('track', 'Lead') no documento pai."""
    if not META_PIXEL_ID:
        return
    components.html(
        """
        <script>
        (function () {
          if (window.parent.fbq) { window.parent.fbq('track', 'Lead'); }
        })();
        </script>
        """,
        height=0,
    )


# Letras em círculo (badge real, sem precisar de CSS por opção)
CIRCULADO = {"A": "Ⓐ", "B": "Ⓑ", "C": "Ⓒ", "D": "Ⓓ", "E": "Ⓔ", "F": "Ⓕ", "G": "Ⓖ"}


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


ORDEM = ["nome", "whatsapp", "instagram", "faturamento", "investimento"]
FLUXO_LINEAR = ["capa", "nome", "whatsapp", "instagram", "faturamento", "investimento"]


def progresso(passo):
    if passo in ORDEM:
        return ORDEM.index(passo) / (len(ORDEM) + 1)
    return None


def _anterior(passo):
    if passo in FLUXO_LINEAR:
        i = FLUXO_LINEAR.index(passo)
        return FLUXO_LINEAR[max(0, i - 1)]
    if passo == "desqualificacao":
        return "investimento"
    return "capa"


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
def autofocus():
    """Coloca o cursor no primeiro campo da tela (foco automático ao trocar de slide)."""
    components.html(
        """
        <script>
        (function () {
          const doc = window.parent.document;
          let tentativas = 0;
          const timer = setInterval(function () {
            tentativas++;
            const campo = doc.querySelector(
              'input[type="text"], input:not([type]), input[type="tel"], textarea'
            );
            if (campo) { campo.focus(); clearInterval(timer); }
            if (tentativas > 25) clearInterval(timer);
          }, 40);
        })();
        </script>
        """,
        height=0,
    )


def cabecalho(passo, titulo, ajuda=""):
    p = progresso(passo)
    if p is not None:
        st.progress(p)
    st.markdown(f'<div class="pergunta">{titulo}</div>', unsafe_allow_html=True)
    if ajuda:
        st.markdown(f'<div class="ajuda">{ajuda}</div>', unsafe_allow_html=True)


def botao_voltar(passo, destino=None):
    st.write("")
    if st.button("← Voltar", key=f"v_{passo}"):
        ir(destino or _anterior(passo))


def tela_texto(passo, titulo, placeholder, proximo, validar=None, erro="", ajuda="", multiline=False):
    cabecalho(passo, titulo, ajuda)
    with st.form(f"f_{passo}"):
        atual = R.get(passo, "")
        if multiline:
            val = st.text_area(" ", value=atual, placeholder=placeholder, label_visibility="collapsed")
        else:
            val = st.text_input(" ", value=atual, placeholder=placeholder, label_visibility="collapsed")
        ok = st.form_submit_button("OK  ✓")
        st.markdown('<div class="dica-enter">pressione <b>Enter ↵</b></div>', unsafe_allow_html=True)
    autofocus()
    if ok:
        if validar and not validar(val):
            st.error(erro)
        else:
            R[passo] = val.strip()
            ir(proximo)
    botao_voltar(passo)


def tela_opcoes(passo, titulo, opcoes, ao_escolher):
    cabecalho(passo, titulo)
    for letra, texto in opcoes:
        rotulo = f"{CIRCULADO.get(letra, letra)}   {texto}"
        if st.button(rotulo, key=f"{passo}_{letra}", type="secondary"):
            R[passo] = f"{letra}) {texto}"
            ao_escolher(f"{letra}) {texto}")
    botao_voltar(passo)


# ============================================================
# TELAS
# ============================================================
passo = st.session_state.passo

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

elif passo == "nome":
    tela_texto("nome", "Qual seu nome e sobrenome?", "Sua resposta...", "whatsapp",
               validar=nao_vazio, erro="Por favor, informe seu nome.")

elif passo == "whatsapp":
    tela_texto("whatsapp", "Qual seu WhatsApp (com DDD)?", "Um número...", "instagram",
               validar=telefone_valido, erro="Informe um número válido com DDD.")

elif passo == "instagram":
    tela_texto("instagram", "Qual o @ do instagram da sua distribuidora?", "Sua resposta...", "faturamento",
               validar=nao_vazio, erro="Por favor, informe o @ do Instagram.")

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

elif passo == "investimento":
    opcoes = [
        ("A", "Sim! É o que eu preciso e estou disposto!"),
        ("B", "Não estou disposto a investir no meu negócio."),
    ]

    def _escolha(valor):
        ir("desqualificacao") if valor.startswith("B") else ir("final")

    tela_opcoes(
        "investimento",
        "Nossa mão de obra se inicia em R$ 1.490 por mês. Está disposto a investir esse valor "
        "e elevar seu negócio a um novo patamar de faturamento e vendas?",
        opcoes,
        ao_escolher=_escolha,
    )

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
    autofocus()
    if ok:
        R["desqualificacao"] = val.strip()
        try:
            enviar_lead(qualificado=bool(val.strip()))
            ir("final")
        except Exception as exc:  # noqa: BLE001
            st.error("Não foi possível enviar agora. Tente novamente.")
            st.caption(f"Detalhe técnico: {exc}")
    botao_voltar("desq", destino="investimento")

elif passo == "final":
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
        if st.button("✓ ESTOU PRONTO(A)", type="primary", use_container_width=True):
            disparar_evento_lead()  # fbq('track', 'Lead')
            if LINK_AGENDAMENTO:
                # dá um instante pro pixel disparar e então redireciona ao agendamento
                components.html(
                    f"<script>setTimeout(function(){{window.parent.location.href="
                    f"'{LINK_AGENDAMENTO}';}}, 500);</script>",
                    height=0,
                )
                st.info("Abrindo a agenda…")
            else:
                st.success("✅ Recebemos seus dados! Em breve nossa equipe entra em contato.")

    if st.session_state.get("modo_teste"):
        with st.expander("🔧 Modo de teste — lead capturado (webhook não configurado)"):
            st.json(st.session_state.modo_teste)
