import streamlit as st

LIME, VIOLET, YELLOW = "#C6F135", "#9B6BFF", "#FFC21A"
BLUE, CORAL, GREEN = "#3B9EFF", "#FF5D4D", "#2FBF71"
BG, CARD, TEXT = "#141218", "#1E1B27", "#F4F4F8"
INK, TEAL, AMBER, RED = BG, LIME, YELLOW, CORAL
SCALE = [[0, CORAL], [0.5, YELLOW], [1, LIME]]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;700&family=Unbounded:wght@500;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, button, input { font-family: 'Rubik', sans-serif; }
.block-container { padding-top: 1.5rem; max-width: 1300px; }
header[data-testid="stHeader"] { background: transparent; }
h2, h3 { font-family: 'Unbounded', sans-serif; font-weight: 700; color: #F4F4F8; letter-spacing: -0.3px; }

.hero { position: relative; display: flex; justify-content: space-between; align-items: center; gap: 24px;
  background: radial-gradient(circle at 8% 0%, #3B2D63 0%, #141218 60%); border: 1px solid #2A2635;
  border-radius: 32px; padding: 38px 42px; margin-bottom: 24px; overflow: hidden; }
.hero-text { max-width: 560px; position: relative; z-index: 2; }
.hero h1 { font-family: 'Unbounded', sans-serif; font-size: 2.5rem; font-weight: 800; line-height: 1.12;
  color: #fff; margin: 14px 0 12px; padding: 0; }
.hero p { color: #C9C6D8; font-size: 1.02rem; margin: 0; line-height: 1.5; }
.badge { display: inline-block; background: #C6F135; color: #141218; font-weight: 700; font-size: .85rem;
  padding: 6px 16px; border-radius: 999px; }
.caps { display: flex; gap: 12px; align-items: flex-end; height: 240px; position: relative; z-index: 2; }
.cap { width: 76px; border-radius: 40px; display: flex; align-items: flex-start; justify-content: center;
  padding-top: 18px; font-size: 2rem; }
.c1 { height: 190px; background: #FFC21A; }
.c2 { height: 240px; background: #7C3AED; }
.c3 { height: 175px; background: #3B9EFF; }
.c4 { height: 215px; background: #2FBF71; }
.dot { position: absolute; border-radius: 50%; display: block; }
.d1 { width: 22px; height: 22px; background: #FF5D4D; top: 26px; left: 52%; }
.d2 { width: 16px; height: 16px; background: #FFC21A; bottom: 30px; left: 46%; }
.d3 { width: 14px; height: 14px; background: #C6F135; top: 60px; right: 6%; }
@media (max-width: 800px) { .caps { display: none; } .hero h1 { font-size: 1.8rem; } }

div[data-testid="stMetric"] { background: #1E1B27; border: 1px solid #2A2635; border-radius: 24px; padding: 16px 20px; }
div[data-testid="stMetricValue"] { font-family: 'Unbounded', sans-serif; font-weight: 700; color: #C6F135; font-size: 1.5rem; }

.stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: none; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
.stTabs [data-baseweb="tab"] { background: #1E1B27; border-radius: 999px; padding: 10px 22px; height: auto; border: 1px solid #2A2635; }
.stTabs [data-baseweb="tab"] p { font-weight: 600; color: #D8D6E6; }
.stTabs [aria-selected="true"] { background: #C6F135; border-color: #C6F135; }
.stTabs [aria-selected="true"] p { color: #141218; }

.insight { background: #1E1B27; border: 1px solid #2A2635; border-radius: 20px; padding: 16px 22px; margin-bottom: 12px; color: #E8E6F2; }
.insight.bad { border-left: 7px solid #FF5D4D; }
.insight.good { border-left: 7px solid #C6F135; }
.insight.warn { border-left: 7px solid #FFC21A; }

.stButton > button, .stDownloadButton > button { border-radius: 999px; background: #C6F135; border: none; padding: 8px 22px; }
.stButton > button p, .stDownloadButton > button p { color: #141218; font-weight: 700; }
</style>
"""

HERO = """<div class="hero">
<div class="hero-text">
<span class="badge">Для методистов</span>
<h1>Data-Driven<br>Curriculum</h1>
<p>Какие темы даются школьникам тяжелее всего, какой учебник работает лучше и как перераспределить учебные часы. Решения по измеримым результатам, а не по ощущениям.</p>
</div>
<div class="caps">
<div class="cap c1">📚</div>
<div class="cap c2">📈</div>
<div class="cap c3">🎯</div>
<div class="cap c4">🏫</div>
</div>
<i class="dot d1"></i><i class="dot d2"></i><i class="dot d3"></i>
</div>"""


def apply_theme():
    st.markdown(CSS, unsafe_allow_html=True)


def hero():
    st.markdown(HERO, unsafe_allow_html=True)


def style(fig, height=None):
    fig.update_layout(template="plotly_dark", font_family="Rubik", font_color=TEXT,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=10, r=10, t=30, b=10),
                      colorway=[LIME, VIOLET, YELLOW, BLUE, CORAL])
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.07)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.07)")
    if height:
        fig.update_layout(height=height)
    return fig


def insight(text, kind="good"):
    st.markdown(f'<div class="insight {kind}">{text}</div>', unsafe_allow_html=True)