import io

import pandas as pd
import plotly.express as px
import streamlit as st

from analysis import (best_textbook_by_topic, compare_textbooks,
                      recommend_hours, topic_stats)
from theme import SCALE, RED, TEAL, style, insight, apply_theme

st.set_page_config(page_title="Sapa Edu", page_icon="📊", layout="wide")

REQUIRED = ["school", "grade", "textbook", "topic", "pre_score", "score", "hours_current"]
RSCALE = [[0, TEAL], [0.5, "#FFC21A"], [1, RED]]

# ---------- Переводы: ключ -> (русский, қазақша) ----------
T = {
    "badge": ("Для методистов", "Әдіскерлер үшін"),
    "hero_p": ("Какие темы даются школьникам тяжелее всего, какой учебник работает лучше и как перераспределить учебные часы. Решения по измеримым результатам, а не по ощущениям.",
               "Қай тақырыптар оқушыларға ең қиын, қай оқулық тиімдірек және оқу сағаттарын қалай қайта бөлу керек. Шешімдер сезімге емес, өлшенетін нәтижелерге негізделеді."),
    "sb_data": ("Данные", "Деректер"),
    "upload": ("Загрузите CSV с результатами тестов", "Тест нәтижелері бар CSV файлын жүктеңіз"),
    "columns": ("Колонки: ", "Бағандар: "),
    "template_btn": ("Скачать шаблон CSV", "CSV үлгісін жүктеу"),
    "threshold": ("Порог слабого результата (балл)", "Әлсіз нәтиже шегі (балл)"),
    "sb_filters": ("Фильтры", "Сүзгілер"),
    "grades": ("Классы", "Сыныптар"),
    "schools": ("Школы", "Мектептер"),
    "source_label": ("Источник данных: ", "Дерек көзі: "),
    "src_file": ("ваш файл", "сіздің файлыңыз"),
    "src_demo": ("демонстрационные синтетические данные", "демонстрациялық синтетикалық деректер"),
    "err_missing": ("В файле не хватает колонок: ", "Файлда мына бағандар жетіспейді: "),
    "err_nofile": ("Нет файла data/results.csv. Запустите: python generate_data.py",
                   "data/results.csv файлы жоқ. Мынаны іске қосыңыз: python generate_data.py"),
    "warn_empty": ("Выберите хотя бы один класс и одну школу.", "Кемінде бір сынып пен бір мектепті таңдаңыз."),
    "tab_overview": ("🏠 Обзор", "🏠 Шолу"),
    "tab_risk": ("🚨 Зона риска", "🚨 Тәуекел аймағы"),
    "tab_hard": ("🔥 Сложные темы", "🔥 Қиын тақырыптар"),
    "tab_books": ("📚 Учебники", "📚 Оқулықтар"),
    "tab_schools": ("🏫 Школы", "🏫 Мектептер"),
    "tab_hours": ("⏱ Часы", "⏱ Сағаттар"),
    "m_records": ("Записей", "Жазбалар"),
    "m_schools": ("Школ", "Мектеп"),
    "m_topics": ("Тем", "Тақырып"),
    "m_mean": ("Средний балл", "Орташа балл"),
    "m_gain": ("Средний прирост", "Орташа өсім"),
    "main_title": ("Главное для методиста", "Әдіскерге маңыздысы"),
    "ins_hardest": ("<b>Самая сложная тема:</b> {topic} ({grade} класс). Средний балл {mean:.1f}, {share:.0f}% учеников ниже порога {thr}.",
                    "<b>Ең қиын тақырып:</b> {topic} ({grade}-сынып). Орташа балл {mean:.1f}, оқушылардың {share:.0f}%-ы {thr} шегінен төмен."),
    "ins_bestbook": ("<b>Лучший прирост знаний:</b> учебник «{book}» ({gain:+.1f} балла в среднем). Подробное сравнение с поправкой на входной уровень на вкладке «Учебники».",
                     "<b>Білімнің ең жақсы өсімі:</b> «{book}» оқулығы (орта есеппен {gain:+.1f} балл). Кіру деңгейін ескеретін толық салыстыру «Оқулықтар» қойындысында."),
    "ins_worstschool": ("<b>Школа с наименьшим приростом:</b> {school} ({gain:+.1f}). Стоит посмотреть, какие темы и учебники там используются.",
                        "<b>Өсімі ең төмен мектеп:</b> {school} ({gain:+.1f}). Онда қандай тақырыптар мен оқулықтар қолданылатынын қарап шығу керек."),
    "ins_small": ("Для {n} тем меньше 30 записей, выводы по ним ненадёжны.",
                  "{n} тақырып бойынша 30-дан аз жазба бар, қорытындылар сенімсіз."),
    "map_school_topic": ("Карта: школа × тема (средний балл)", "Карта: мектеп × тақырып (орташа балл)"),
    "lbl_score": ("Балл", "Балл"),
    "risk_title": ("Зона риска: где школьникам нужна помощь", "Тәуекел аймағы: оқушыларға қайда көмек керек"),
    "risk_caption": ("Доля учеников, набравших меньше {thr} баллов. Темы, где слабых больше трети, выделены в списке ниже.",
                     "{thr} баллдан аз жинаған оқушылар үлесі. Әлсіздер үштен астам болатын тақырыптар төмендегі тізімде бөлектелген."),
    "risk_none": ("Тем, где слабых учеников больше трети, нет.", "Әлсіз оқушылар үштен астам болатын тақырыптар жоқ."),
    "risk_high": ("<b>Высокий риск:</b> {topic} ({grade} класс): {share:.0f}% учеников ниже порога.",
                  "<b>Жоғары тәуекел:</b> {topic} ({grade}-сынып): оқушылардың {share:.0f}%-ы шектен төмен."),
    "risk_mid": ("<b>Средний риск:</b> {topic} ({grade} класс): {share:.0f}% учеников ниже порога.",
                 "<b>Орташа тәуекел:</b> {topic} ({grade}-сынып): оқушылардың {share:.0f}%-ы шектен төмен."),
    "risk_chart": ("Доля слабых учеников по темам", "Тақырыптар бойынша әлсіз оқушылар үлесі"),
    "risk_axis": ("Доля слабых, %", "Әлсіздер үлесі, %"),
    "risk_line": ("треть", "үштен бір"),
    "risk_heat": ("Доля слабых учеников: школа × тема (%)", "Әлсіз оқушылар үлесі: мектеп × тақырып (%)"),
    "risk_table": ("Таблица рисков", "Тәуекелдер кестесі"),
    "col_level": ("Уровень риска", "Тәуекел деңгейі"),
    "lvl_high": ("Высокий", "Жоғары"),
    "lvl_mid": ("Средний", "Орташа"),
    "lvl_low": ("Низкий", "Төмен"),
    "hard_title": ("Рейтинг сложности тем", "Тақырыптардың қиындық рейтингі"),
    "idx_axis": ("Индекс сложности (0–100)", "Қиындық индексі (0–100)"),
    "dist_title": ("Распределение баллов", "Баллдардың таралуы"),
    "pick_topic": ("Тема", "Тақырып"),
    "all_topics": ("Все темы", "Барлық тақырыптар"),
    "students": ("Учеников", "Оқушылар"),
    "thr_label": ("порог", "шек"),
    "all_topics_table": ("Все темы (таблица)", "Барлық тақырыптар (кесте)"),
    "col_grade": ("Класс", "Сынып"),
    "col_topic": ("Тема", "Тақырып"),
    "col_n": ("Записей", "Жазбалар"),
    "col_mean": ("Средний балл", "Орташа балл"),
    "col_median": ("Медиана", "Медиана"),
    "col_std": ("Разброс", "Таралу"),
    "col_share": ("Доля слабых", "Әлсіздер үлесі"),
    "col_hours": ("Часы сейчас", "Қазіргі сағат"),
    "col_idx": ("Индекс сложности", "Қиындық индексі"),
    "col_hard": ("Сложная", "Қиын"),
    "books_title": ("Какой учебник работает лучше", "Қай оқулық тиімдірек"),
    "books_caption": ("Сравнение идёт с поправкой на входной тест: ученики в разных школах начинают с разного уровня.",
                      "Салыстыру кіру тестін ескереді: әр мектепте оқушылар әртүрлі деңгейден бастайды."),
    "effect_axis": ("Эффект относительно «{base}» (баллы)", "«{base}» оқулығына қатысты әсер (балл)"),
    "ins_nosig": ("Значимых различий между учебниками на этой теме не обнаружено.",
                  "Бұл тақырып бойынша оқулықтар арасында маңызды айырмашылық табылмады."),
    "ins_sigbook": ("При одинаковом входном уровне «{book}» даёт в среднем на {eff:.1f} балла больше, чем «{base}» (95% ДИ: {lo:.1f}…{hi:.1f}).",
                    "Кіру деңгейі бірдей болғанда «{book}» «{base}» оқулығына қарағанда орта есеппен {eff:.1f} балға жоғары нәтиже береді (95% СА: {lo:.1f}…{hi:.1f})."),
    "ins_basebest": ("«{base}» значимо лучше остальных учебников на этой теме.",
                     "«{base}» бұл тақырыпта қалған оқулықтардан айтарлықтай жақсы."),
    "col_book": ("Учебник", "Оқулық"),
    "col_eff": ("Эффект с поправкой", "Түзетілген әсер"),
    "ci_lo": ("ДИ от", "СА бастап"),
    "ci_hi": ("ДИ до", "СА дейін"),
    "col_p": ("p-значение", "p-мәні"),
    "col_enough": ("Достаточно данных", "Дерек жеткілікті"),
    "best_by_topic": ("Лучший учебник по каждой теме", "Әр тақырып бойынша үздік оқулық"),
    "map_topic_book": ("Карта: тема × учебник (средний балл)", "Карта: тақырып × оқулық (орташа балл)"),
    "seg_title": ("Для кого учебник работает", "Оқулық кімге тиімді"),
    "seg_caption": ("Делим учеников по входному баллу на три равные группы и считаем средний прирост (итоговый балл − входной) для каждого учебника. Сравнивайте учебники внутри одной группы, а не группы между собой: у слабых прирост естественно выше.",
                    "Оқушыларды кіру балына қарай үш тең топқа бөліп, әр оқулық үшін орташа өсімді (қорытынды балл − кіру балы) есептейміз. Оқулықтарды бір топ ішінде салыстырыңыз, топтарды бір-бірімен емес: әлсіздердің өсімі табиғи түрде жоғары."),
    "seg_weak": ("Слабые", "Әлсіздер"),
    "seg_mid": ("Средние", "Орташалар"),
    "seg_strong": ("Сильные", "Күштілер"),
    "seg_group": ("Группа по входному баллу", "Кіру балы бойынша топ"),
    "seg_axis": ("Средний прирост", "Орташа өсім"),
    "seg_diff": ("<b>Лучший учебник зависит от группы:</b> {parts}.", "<b>Үздік оқулық топқа байланысты:</b> {parts}."),
    "seg_same": ("Во всех группах лидирует один учебник: «{book}».", "Барлық топта бір оқулық көш бастайды: «{book}»."),
    "seg_small": ("В некоторых группах меньше 10 записей на учебник, такие результаты ненадёжны.",
                  "Кейбір топтарда оқулыққа 10-нан аз жазба бар, мұндай нәтижелер сенімсіз."),
    "seg_nodata": ("Недостаточно данных для сравнения.", "Салыстыру үшін дерек жеткіліксіз."),
    "schools_title": ("Сравнение школ", "Мектептерді салыстыру"),
    "gain_axis": ("Средний прирост (балл − входной балл)", "Орташа өсім (балл − кіру балы)"),
    "pre_axis": ("Входной балл", "Кіру балы"),
    "post_axis": ("Итоговый балл", "Қорытынды балл"),
    "schools_caption": ("Школы выше диагонали улучшили результат относительно входного уровня.",
                        "Диагональдан жоғары мектептер нәтижені кіру деңгейімен салыстырғанда жақсартты."),
    "col_school": ("Школа", "Мектеп"),
    "col_pre": ("Вход", "Кіру"),
    "col_post": ("Итог", "Қорытынды"),
    "col_gain": ("Прирост", "Өсім"),
    "hours_title": ("Рекомендации по распределению часов", "Сағаттарды бөлу бойынша ұсыныстар"),
    "budget": ("Общий бюджет часов", "Сағаттың жалпы бюджеті"),
    "per_hour": ("Ожидаемый прирост балла на 1 доп. час (параметр модели)", "1 қосымша сағатқа күтілетін балл өсімі (модель параметрі)"),
    "var_label": ("Вариант", "Нұсқа"),
    "var_now": ("Сейчас", "Қазір"),
    "var_rec": ("Рекомендуется", "Ұсынылады"),
    "hours_axis": ("Часы", "Сағат"),
    "edit_hint": ("**Скорректируйте часы вручную** (колонка «Часы»), и система пересчитает эффект.",
                  "**Сағаттарды қолмен түзетіңіз** («Сағат» бағаны), жүйе әсерді қайта есептейді."),
    "col_hours_edit": ("Часы (можно править)", "Сағат (түзетуге болады)"),
    "sum_mismatch": ("Сумма часов {new} не равна бюджету {budget}.", "Сағат сомасы {new} бюджетке {budget} тең емес."),
    "sum_ok": ("Бюджет соблюдён: {new} часов.", "Бюджет сақталды: {new} сағат."),
    "m_before": ("Средний балл по сложным темам: сейчас", "Қиын тақырыптар бойынша орташа балл: қазір"),
    "m_after": ("Прогноз после перераспределения", "Қайта бөлгеннен кейінгі болжам"),
    "forecast_note": ("Прогноз ориентировочный: упрощённая модель, параметр задаёт методист. Точную оценку даст пилот на реальных данных.",
                      "Болжам шамамен: жеңілдетілген модель, параметрді әдіскер береді. Нақты бағаны нақты деректермен пилот береді."),
    "reasons_title": ("Почему так: обоснование рекомендаций", "Неге солай: ұсыныстардың негіздемесі"),
    "reason_up": ("<b>{topic}</b> ({grade} класс): средний балл {mean:.0f}, {share:.0f}% учеников ниже порога. Рекомендуем <b>+{d} ч</b> ({cur} → {new}): тема даётся тяжело.",
                  "<b>{topic}</b> ({grade}-сынып): орташа балл {mean:.0f}, оқушылардың {share:.0f}%-ы шектен төмен. <b>+{d} сағат</b> ұсынамыз ({cur} → {new}): тақырып қиын меңгеріледі."),
    "reason_down": ("<b>{topic}</b> ({grade} класс): средний балл {mean:.0f}, {share:.0f}% учеников ниже порога. Часы сокращаются на <b>{d} ч</b> ({cur} → {new}): они перераспределены на более сложные темы.",
                    "<b>{topic}</b> ({grade}-сынып): орташа балл {mean:.0f}, оқушылардың {share:.0f}%-ы шектен төмен. Сағат <b>{d} сағатқа</b> қысқарады ({cur} → {new}): олар неғұрлым қиын тақырыптарға бөлінген."),
    "reason_none": ("Распределение часов пока не отличается от текущего.", "Сағаттарды бөлу әзірге қазіргіден өзгеше емес."),
    "reason_note": ("Показаны темы с самыми большими изменениями (не больше шести).", "Ең көп өзгерген тақырыптар көрсетілген (алтыдан көп емес)."),
    "download": ("⬇️ Скачать отчёт (Excel)", "⬇️ Есепті жүктеу (Excel)"),
    "sh_topics": ("Темы", "Тақырыптар"),
    "sh_hours": ("Часы", "Сағаттар"),
    "sh_schools": ("Школы", "Мектептер"),
    "sh_books": ("Учебники", "Оқулықтар"),
    "sh_risk": ("Риск", "Тәуекел"),
    "meth_title": ("ℹ️ Методология: как это считается", "ℹ️ Әдістеме: бұл қалай есептеледі"),
    "meth_body": (
        """**Сложные темы.** Для каждой темы считаем средний балл, медиану, разброс и долю учеников ниже порога. Индекс сложности (0–100) строится на этих показателях: чем он выше, тем тяжелее тема.

**Зона риска.** Доля учеников, набравших меньше порога. Если слабых больше трети, риск средний, если половина и больше, высокий.

**Сравнение учебников.** Сравниваем не средние баллы, а результат при одинаковом входном уровне, потому что в разных школах ученики начинают с разной подготовки. Показываем 95% доверительный интервал и p-значение. Вывод делаем только если различие значимо (p < 0,05) и данных достаточно.

**Для кого учебник работает.** Делим учеников на три равные группы по входному баллу и считаем средний прирост (итоговый балл минус входной) для каждого учебника внутри группы.

**Часы.** Общий бюджет часов распределяется между темами с учётом их сложности, а методист может поправить результат вручную. В прогнозе каждый дополнительный час повышает балл темы на заданную величину, а сокращение часов снижает его на 30% от этой величины. Это упрощённая модель для сценариев, а не доказанная зависимость.

**Ограничения.** Демонстрационные данные синтетические. Если записей мало, выводы помечаются как ненадёжные. Точную оценку даст пилот на реальных данных.""",
        """**Қиын тақырыптар.** Әр тақырып үшін орташа балл, медиана, таралу және шектен төмен балл жинаған оқушылар үлесін есептейміз. Қиындық индексі (0–100) осы көрсеткіштерге негізделген: ол неғұрлым жоғары болса, тақырып соғұрлым қиын.

**Тәуекел аймағы.** Шектен төмен балл жинаған оқушылар үлесі. Әлсіздер үштен астам болса, тәуекел орташа, жартысы немесе одан көп болса, жоғары.

**Оқулықтарды салыстыру.** Орташа баллдарды емес, кіру деңгейі бірдей болғандағы нәтижені салыстырамыз, өйткені әр мектепте оқушылар әртүрлі дайындықпен бастайды. 95% сенім аралығы мен p-мәнін көрсетеміз. Қорытындыны айырмашылық маңызды (p < 0,05) және дерек жеткілікті болғанда ғана жасаймыз.

**Оқулық кімге тиімді.** Оқушыларды кіру балына қарай үш тең топқа бөліп, топ ішінде әр оқулық бойынша орташа өсімді (қорытынды балл минус кіру балы) есептейміз.

**Сағаттар.** Сағаттың жалпы бюджеті тақырыптар арасында олардың қиындығын ескере отырып бөлінеді, ал әдіскер нәтижені қолмен түзете алады. Болжамда әр қосымша сағат тақырып балын берілген шамаға арттырады, ал сағатты қысқарту оны сол шаманың 30%-ына төмендетеді. Бұл сценарийлерге арналған жеңілдетілген модель, дәлелденген тәуелділік емес.

**Шектеулер.** Демонстрациялық деректер синтетикалық. Жазба аз болса, қорытындылар сенімсіз деп белгіленеді. Нақты бағаны нақты деректермен пилот береді."""),
}

# ---------- Язык ----------
LANGS = {"Русский": "ru", "Қазақша": "kk"}
with st.sidebar:
    lang = LANGS[st.radio("Язык / Тіл", list(LANGS), horizontal=True)]


def t(key, **kw):
    s = T[key][0 if lang == "ru" else 1]
    return s.format(**kw) if kw else s


apply_theme()
st.markdown(f"""<div class="hero">
<div class="hero-text">
<span class="badge">{t('badge')}</span>
<h1>Data-Driven<br>Curriculum</h1>
<p>{t('hero_p')}</p>
</div>
<div class="caps">
<div class="cap c1">📚</div>
<div class="cap c2">📈</div>
<div class="cap c3">🎯</div>
<div class="cap c4">🏫</div>
</div>
<i class="dot d1"></i><i class="dot d2"></i><i class="dot d3"></i>
</div>""", unsafe_allow_html=True)

# ---------- Данные ----------
with st.sidebar:
    st.header(t("sb_data"))
    uploaded = st.file_uploader(t("upload"), type="csv")
    st.caption(t("columns") + ", ".join(REQUIRED))
    template = pd.DataFrame(columns=REQUIRED).to_csv(index=False).encode("utf-8")
    st.download_button(t("template_btn"), template, file_name="template.csv", mime="text/csv")
    threshold = st.slider(t("threshold"), 30, 70, 50)

if uploaded is not None:
    df = pd.read_csv(uploaded)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        st.error(t("err_missing") + ", ".join(missing))
        st.stop()
    source = t("src_file")
else:
    try:
        df = pd.read_csv("data/results.csv")
    except FileNotFoundError:
        st.error(t("err_nofile"))
        st.stop()
    source = t("src_demo")

with st.sidebar:
    st.header(t("sb_filters"))
    grades = sorted(df["grade"].unique())
    chosen = st.multiselect(t("grades"), grades, default=grades)
    schools = sorted(df["school"].unique())
    chosen_schools = st.multiselect(t("schools"), schools, default=schools)
    st.info(t("source_label") + source)

df = df[df["grade"].isin(chosen) & df["school"].isin(chosen_schools)]
if df.empty:
    st.warning(t("warn_empty"))
    st.stop()

df = df.assign(gain=df["score"] - df["pre_score"])
ts = topic_stats(df, threshold)

tab0, tabr, tab1, tab2, tab3, tab4 = st.tabs([
    t("tab_overview"), t("tab_risk"), t("tab_hard"), t("tab_books"), t("tab_schools"), t("tab_hours")])

# ---------- Обзор ----------
with tab0:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(t("m_records"), f"{len(df):,}".replace(",", " "))
    c2.metric(t("m_schools"), df["school"].nunique())
    c3.metric(t("m_topics"), df["topic"].nunique())
    c4.metric(t("m_mean"), f"{df['score'].mean():.1f}")
    c5.metric(t("m_gain"), f"{df['gain'].mean():+.1f}")

    st.subheader(t("main_title"))
    hardest = ts.iloc[0]
    insight(t("ins_hardest", topic=hardest["topic"], grade=int(hardest["grade"]),
              mean=hardest["mean"], share=hardest["share_low"] * 100, thr=threshold), "bad")
    tb_gain = df.groupby("textbook")["gain"].mean().sort_values(ascending=False)
    if len(tb_gain) > 1:
        insight(t("ins_bestbook", book=tb_gain.index[0], gain=tb_gain.iloc[0]), "good")
    sch_gain = df.groupby("school")["gain"].mean().sort_values()
    if len(sch_gain) > 1:
        insight(t("ins_worstschool", school=sch_gain.index[0], gain=sch_gain.iloc[0]), "warn")
    small = int((ts["n"] < 30).sum())
    if small:
        insight(t("ins_small", n=small), "warn")

    st.subheader(t("map_school_topic"))
    heat = df.groupby(["school", "topic"])["score"].mean().unstack()
    heat = heat[[x for x in ts["topic"] if x in heat.columns]]
    st.plotly_chart(style(px.imshow(heat.round(0), color_continuous_scale=SCALE, aspect="auto",
                                    text_auto=True, labels={"color": t("lbl_score"), "x": "", "y": ""}), 420))

# ---------- Зона риска ----------
risk = ts[["grade", "topic", "share_low"]].copy()
risk["pct"] = risk["share_low"] * 100
risk = risk.sort_values("pct", ascending=False)
risk["level"] = risk["pct"].map(lambda p: t("lvl_high") if p >= 50 else (t("lvl_mid") if p >= 100 / 3 else t("lvl_low")))

with tabr:
    st.subheader(t("risk_title"))
    st.caption(t("risk_caption", thr=threshold))
    danger = risk[risk["pct"] >= 100 / 3]
    if danger.empty:
        insight(t("risk_none"), "good")
    for _, r in danger.head(5).iterrows():
        high = r["pct"] >= 50
        insight(t("risk_high" if high else "risk_mid", topic=r["topic"], grade=int(r["grade"]), share=r["pct"]),
                "bad" if high else "warn")

    st.subheader(t("risk_chart"))
    fig_r = px.bar(risk, x="topic", y="pct", color="pct", color_continuous_scale=RSCALE,
                   labels={"topic": "", "pct": t("risk_axis")})
    fig_r.add_hline(y=100 / 3, line_dash="dash", line_color="#FFC21A", annotation_text=t("risk_line"))
    st.plotly_chart(style(fig_r, 420))

    st.subheader(t("risk_heat"))
    low = df.assign(low=(df["score"] < threshold) * 100).groupby(["school", "topic"])["low"].mean().unstack()
    low = low[[x for x in ts["topic"] if x in low.columns]]
    st.plotly_chart(style(px.imshow(low.round(0), color_continuous_scale=RSCALE, aspect="auto",
                                    text_auto=True, labels={"color": "%", "x": "", "y": ""}), 420))

    st.subheader(t("risk_table"))
    risk_show = risk[["topic", "grade", "pct", "level"]].rename(columns={
        "topic": t("col_topic"), "grade": t("col_grade"), "pct": t("risk_axis"), "level": t("col_level")}).round(1)
    st.dataframe(risk_show)

# ---------- Сложные темы ----------
with tab1:
    st.subheader(t("hard_title"))
    top = ts.head(10).iloc[::-1]
    fig = px.bar(top, x="difficulty_index", y="topic", orientation="h", color="mean",
                 color_continuous_scale=SCALE,
                 labels={"difficulty_index": t("idx_axis"), "topic": "", "mean": t("m_mean")})
    st.plotly_chart(style(fig, 450))

    st.subheader(t("dist_title"))
    pick = st.selectbox(t("pick_topic"), [t("all_topics")] + ts["topic"].tolist(), key="dist_topic")
    sub = df if pick == t("all_topics") else df[df["topic"] == pick]
    fig_h = px.histogram(sub, x="score", nbins=20, labels={"score": t("lbl_score"), "count": t("students")})
    fig_h.add_vline(x=threshold, line_dash="dash", line_color=RED, annotation_text=t("thr_label"))
    st.plotly_chart(style(fig_h, 320))

    with st.expander(t("all_topics_table")):
        show = ts.rename(columns={
            "grade": t("col_grade"), "topic": t("col_topic"), "n": t("col_n"), "mean": t("col_mean"),
            "median": t("col_median"), "std": t("col_std"), "share_low": t("col_share"),
            "hours_current": t("col_hours"), "difficulty_index": t("col_idx"),
            "is_hard": t("col_hard")}).round(2)
        st.dataframe(show)

# ---------- Учебники ----------
with tab2:
    st.subheader(t("books_title"))
    st.caption(t("books_caption"))
    topic = st.selectbox(t("pick_topic"), ts["topic"].tolist(), key="books_topic")
    res = compare_textbooks(df, topic)
    base = res.attrs["base"]

    res["err_plus"] = res["ci_high"] - res["adj_effect"]
    res["err_minus"] = res["adj_effect"] - res["ci_low"]
    fig2 = px.bar(res, x="textbook", y="adj_effect", error_y="err_plus", error_y_minus="err_minus",
                  labels={"textbook": "", "adj_effect": t("effect_axis", base=base)})
    st.plotly_chart(style(fig2, 380))

    sig = res[(res["textbook"] != base) & (res["p_value"] < 0.05) & (res["reliable"])]
    pos = sig[sig["adj_effect"] > 0]
    if sig.empty:
        insight(t("ins_nosig"), "warn")
    elif not pos.empty:
        b = pos.loc[pos["adj_effect"].idxmax()]
        insight(t("ins_sigbook", book=b["textbook"], base=base, eff=b["adj_effect"],
                  lo=b["ci_low"], hi=b["ci_high"]), "good")
    else:
        insight(t("ins_basebest", base=base), "good")

    st.dataframe(res[["textbook", "n", "mean_score", "adj_effect", "ci_low",
                      "ci_high", "p_value", "reliable"]].rename(columns={
        "textbook": t("col_book"), "n": t("col_n"), "mean_score": t("col_mean"),
        "adj_effect": t("col_eff"), "ci_low": t("ci_lo"), "ci_high": t("ci_hi"),
        "p_value": t("col_p"), "reliable": t("col_enough")}).round(3))

    # --- Для кого учебник работает ---
    st.subheader(t("seg_title"))
    st.caption(t("seg_caption"))
    seg_pick = st.selectbox(t("pick_topic"), [t("all_topics")] + ts["topic"].tolist(), key="seg_topic")
    rank = df["pre_score"].rank(pct=True, method="first")
    seg_codes = pd.cut(rank, [0, 1 / 3, 2 / 3, 1], labels=["w", "m", "s"], include_lowest=True)
    seg_names = {"w": t("seg_weak"), "m": t("seg_mid"), "s": t("seg_strong")}
    sd = df.assign(seg=seg_codes.astype(str).map(seg_names))
    if seg_pick != t("all_topics"):
        sd = sd[sd["topic"] == seg_pick]
    order = [seg_names["w"], seg_names["m"], seg_names["s"]]
    g = sd.groupby(["seg", "textbook"]).agg(n=("gain", "size"), gain=("gain", "mean")).reset_index()

    if g.empty or g["textbook"].nunique() < 2:
        insight(t("seg_nodata"), "warn")
    else:
        fig_seg = px.bar(g, x="seg", y="gain", color="textbook", barmode="group",
                         category_orders={"seg": order},
                         labels={"seg": t("seg_group"), "gain": t("seg_axis"), "textbook": t("col_book")})
        st.plotly_chart(style(fig_seg, 380))

        best = {}
        for s in order:
            part = g[(g["seg"] == s) & (g["n"] >= 10)]
            if not part.empty:
                best[s] = part.loc[part["gain"].idxmax(), "textbook"]
        if len(best) >= 2 and len(set(best.values())) > 1:
            parts = "; ".join(f"{k}: «{v}»" for k, v in best.items())
            insight(t("seg_diff", parts=parts), "good")
        elif len(best) >= 2:
            insight(t("seg_same", book=list(best.values())[0]), "good")
        else:
            insight(t("seg_nodata"), "warn")
        if (g["n"] < 10).any():
            insight(t("seg_small"), "warn")

        st.dataframe(g.rename(columns={"seg": t("seg_group"), "textbook": t("col_book"),
                                       "n": t("col_n"), "gain": t("seg_axis")}).round(2))

    st.subheader(t("best_by_topic"))
    st.dataframe(best_textbook_by_topic(df))

    st.subheader(t("map_topic_book"))
    pivot = df.groupby(["topic", "textbook"])["score"].mean().unstack()
    pivot = pivot.reindex([x for x in ts["topic"] if x in pivot.index])
    st.plotly_chart(style(px.imshow(pivot.round(0), color_continuous_scale=SCALE, aspect="auto",
                                    text_auto=True, labels={"color": t("lbl_score"), "x": "", "y": ""}), 750))

# ---------- Школы ----------
with tab3:
    st.subheader(t("schools_title"))
    sch = df.groupby("school").agg(n=("score", "size"), pre=("pre_score", "mean"),
                                   post=("score", "mean"), gain=("gain", "mean")).reset_index()
    sch = sch.sort_values("gain", ascending=False)
    fig_s = px.bar(sch, x="school", y="gain", color="gain", color_continuous_scale=SCALE,
                   labels={"school": "", "gain": t("gain_axis")})
    st.plotly_chart(style(fig_s, 380))
    fig_p = px.scatter(sch, x="pre", y="post", size="n", text="school",
                       labels={"pre": t("pre_axis"), "post": t("post_axis")})
    fig_p.update_traces(textposition="top center")
    st.caption(t("schools_caption"))
    st.plotly_chart(style(fig_p, 400))
    st.dataframe(sch.rename(columns={"school": t("col_school"), "n": t("col_n"), "pre": t("col_pre"),
                                     "post": t("col_post"), "gain": t("col_gain")}).round(2))

# ---------- Часы ----------
with tab4:
    st.subheader(t("hours_title"))
    col_a, col_b = st.columns(2)
    budget = col_a.number_input(t("budget"), min_value=1, value=int(ts["hours_current"].sum()))
    per_hour = col_b.slider(t("per_hour"), 0.0, 3.0, 1.0, 0.1)

    rec = recommend_hours(ts, int(budget))

    long = rec.melt(id_vars="topic", value_vars=["hours_current", "hours_recommended"],
                    var_name="variant", value_name="hours")
    long["variant"] = long["variant"].map({"hours_current": t("var_now"), "hours_recommended": t("var_rec")})
    order_h = rec.sort_values("difficulty_index", ascending=False)["topic"].tolist()
    fig4 = px.bar(long, x="topic", y="hours", color="variant", barmode="group",
                  category_orders={"topic": order_h},
                  labels={"topic": "", "hours": t("hours_axis"), "variant": t("var_label")},
                  color_discrete_map={t("var_now"): "#6B6880", t("var_rec"): TEAL})
    st.plotly_chart(style(fig4, 450))

    st.markdown(t("edit_hint"))
    edit = rec[["grade", "topic", "hours_current", "hours_recommended",
                "difficulty_index", "mean", "is_hard"]].copy()
    edited = st.data_editor(
        edit, hide_index=True, key="hours_editor",
        disabled=["grade", "topic", "hours_current"],
        column_config={
            "grade": t("col_grade"), "topic": t("col_topic"), "hours_current": t("col_hours"),
            "hours_recommended": st.column_config.NumberColumn(
                t("col_hours_edit"), min_value=0, max_value=60, step=1),
            "difficulty_index": None, "mean": None, "is_hard": None})

    new_total = int(edited["hours_recommended"].sum())
    if new_total != int(budget):
        insight(t("sum_mismatch", new=new_total, budget=int(budget)), "warn")
    else:
        insight(t("sum_ok", new=new_total), "good")

    delta = edited["hours_recommended"] - edited["hours_current"]
    gain = delta.where(delta > 0, delta * 0.3) * per_hour
    new_mean = (edited["mean"] + gain).clip(0, 100)
    hard = edited["is_hard"]
    before = edited.loc[hard, "mean"].mean()
    after = new_mean[hard].mean()
    m1, m2 = st.columns(2)
    m1.metric(t("m_before"), f"{before:.1f}")
    m2.metric(t("m_after"), f"{after:.1f}", f"{after - before:+.1f}")
    st.caption(t("forecast_note"))

    # --- Обоснование рекомендаций ---
    st.subheader(t("reasons_title"))
    rs = edited.merge(ts[["grade", "topic", "share_low"]], on=["grade", "topic"], how="left")
    rs["share_low"] = rs["share_low"].fillna(0)
    rs["delta"] = (rs["hours_recommended"] - rs["hours_current"]).astype(int)
    rs["abs_delta"] = rs["delta"].abs()
    rs = rs[rs["delta"] != 0].sort_values("abs_delta", ascending=False).head(6)
    if rs.empty:
        insight(t("reason_none"), "warn")
    else:
        for _, r in rs.iterrows():
            up = r["delta"] > 0
            insight(t("reason_up" if up else "reason_down", topic=r["topic"], grade=int(r["grade"]),
                      mean=r["mean"], share=r["share_low"] * 100, d=int(r["abs_delta"]),
                      cur=int(r["hours_current"]), new=int(r["hours_recommended"])),
                    "warn" if up else "good")
        st.caption(t("reason_note"))

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        ts.to_excel(writer, sheet_name=t("sh_topics"), index=False)
        edited.to_excel(writer, sheet_name=t("sh_hours"), index=False)
        sch.to_excel(writer, sheet_name=t("sh_schools"), index=False)
        risk_show.to_excel(writer, sheet_name=t("sh_risk"), index=False)
        best_textbook_by_topic(df).to_excel(writer, sheet_name=t("sh_books"), index=False)
    st.download_button(t("download"), buf.getvalue(), file_name="curriculum_report.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---------- Методология ----------
st.write("")
with st.expander(t("meth_title")):
    st.markdown(t("meth_body"))
