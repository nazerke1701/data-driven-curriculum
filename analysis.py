import numpy as np
import pandas as pd
from scipy import stats

LOW_THRESHOLD = 50
MIN_N = 30
ALPHA = 0.05
NO_DIFF = "нет значимой разницы"
MAX_SCORE = 100


def _minmax(s):
    rng = s.max() - s.min()
    return (s - s.min()) / rng if rng > 0 else s * 0


def wilson_interval(k, n, z=1.96):
    """Доверительный интервал Уилсона для доли k/n."""
    if n <= 0:
        return np.nan, np.nan
    p = k / n
    den = 1 + z ** 2 / n
    centre = (p + z ** 2 / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


def holm_adjust(p):
    """Поправка Холма на множественные сравнения (NaN пропускаются)."""
    p = np.asarray(p, dtype=float)
    adj = np.full(p.shape, np.nan)
    ok = ~np.isnan(p)
    vals = p[ok]
    m = len(vals)
    if m == 0:
        return adj
    out = np.empty(m)
    running = 0.0
    for rank, i in enumerate(np.argsort(vals)):
        running = max(running, (m - rank) * vals[i])
        out[i] = min(1.0, running)
    adj[ok] = out
    return adj


# ---------- Проверка входных данных ----------
def validate_data(df, max_score=MAX_SCORE):
    """Список проблем: (тип, колонка, количество)."""
    issues = []
    for c in ["pre_score", "score"]:
        num = pd.to_numeric(df[c], errors="coerce")
        n_bad = int(num.isna().sum())
        if n_bad:
            issues.append(("missing", c, n_bad))
        n_out = int(((num < 0) | (num > max_score)).sum())
        if n_out:
            issues.append(("range", c, n_out))
    n_hours = int((df.groupby(["grade", "topic"])["hours_current"].nunique() > 1).sum())
    if n_hours:
        issues.append(("hours", "hours_current", n_hours))
    return issues


def clean_data(df, max_score=MAX_SCORE):
    d = df.copy()
    for c in ["pre_score", "score", "hours_current"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["school", "grade", "textbook", "topic",
                         "pre_score", "score", "hours_current"])
    for c in ["pre_score", "score"]:
        d = d[(d[c] >= 0) & (d[c] <= max_score)]
    return d.reset_index(drop=True)


# ---------- Темы ----------
def topic_stats(df, threshold=LOW_THRESHOLD):
    g = df.groupby(["grade", "topic"])
    out = g.agg(
        n=("score", "count"), mean=("score", "mean"), median=("score", "median"),
        std=("score", "std"), hours_current=("hours_current", "first"),
        n_low=("score", lambda x: int((x < threshold).sum())),
    ).reset_index()
    out["std"] = out["std"].fillna(0)
    out["share_low"] = out["n_low"] / out["n"]
    ci = [wilson_interval(k, n) for k, n in zip(out["n_low"], out["n"])]
    out["share_low_lo"] = [c[0] for c in ci]
    out["share_low_hi"] = [c[1] for c in ci]
    out["reliable"] = out["n"] >= MIN_N
    out = out.drop(columns="n_low")
    out["difficulty_index"] = 100 * (
        0.55 * _minmax(100 - out["mean"])
        + 0.30 * _minmax(out["share_low"])
        + 0.15 * _minmax(out["std"])
    )
    out["is_hard"] = out["difficulty_index"] >= out["difficulty_index"].quantile(0.8)
    return out.sort_values("difficulty_index", ascending=False).reset_index(drop=True)


# ---------- Учебники ----------
def _ols_hc3(X, y):
    """МНК с робастными ошибками HC3 (устойчивы к неравной дисперсии)."""
    n, k = X.shape
    dof = n - k
    if dof < 1:
        return None
    xtx_inv = np.linalg.pinv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    resid = y - X @ beta
    h = np.clip(np.einsum("ij,jk,ik->i", X, xtx_inv, X), 0, 0.999)
    xe = X * (resid / (1 - h))[:, None]
    cov = xtx_inv @ (xe.T @ xe) @ xtx_inv
    se = np.sqrt(np.clip(np.diag(cov), 0, None))
    sigma = np.sqrt(resid @ resid / dof)
    return beta, se, sigma, dof


def compare_textbooks(df, topic, control_school=True):
    d = df[df["topic"] == topic].dropna(subset=["score", "pre_score", "textbook"]).copy()
    counts = d["textbook"].value_counts()
    books = sorted(counts.index, key=lambda b: (-counts[b], str(b)))
    base = books[0]          # базовый учебник: самый распространённый
    others = books[1:]

    cols = [np.ones(len(d)), d["pre_score"].to_numpy(float)]
    cols += [(d["textbook"] == b).to_numpy(float) for b in others]
    X = np.column_stack(cols)
    school_adj = False
    if control_school and others and "school" in d and d["school"].nunique() > 1:
        sd = pd.get_dummies(d["school"], drop_first=True).to_numpy(float)
        X2 = np.column_stack([X, sd])
        if np.linalg.matrix_rank(X2) == X2.shape[1] and len(d) - X2.shape[1] >= 1:
            X, school_adj = X2, True
    fit = _ols_hc3(X, d["score"].to_numpy(float)) if others else None

    rows = []
    for b in books:
        sub = d[d["textbook"] == b]
        row = {"textbook": b, "n": len(sub), "mean_score": sub["score"].mean(),
               "adj_effect": 0.0, "ci_low": 0.0, "ci_high": 0.0,
               "effect_size": 0.0, "p_raw": np.nan}
        if b != base:
            if fit is None:
                row.update(adj_effect=np.nan, ci_low=np.nan, ci_high=np.nan, effect_size=np.nan)
            else:
                beta, se, sigma, dof = fit
                i = 2 + others.index(b)
                tcrit = stats.t.ppf(0.975, dof)
                row.update(adj_effect=beta[i], ci_low=beta[i] - tcrit * se[i],
                           ci_high=beta[i] + tcrit * se[i], effect_size=beta[i] / sigma if sigma > 0 else np.nan,
                           p_raw=2 * stats.t.sf(abs(beta[i] / se[i]), dof) if se[i] > 0 else np.nan)
        row["reliable"] = row["n"] >= MIN_N
        rows.append(row)
    res = pd.DataFrame(rows)
    res["p_value"] = holm_adjust(res["p_raw"].to_numpy())   # с поправкой Холма
    res.attrs["base"] = base
    res.attrs["school_adjusted"] = school_adj
    return res


def best_textbook_by_topic(df):
    results = {t: compare_textbooks(df, t) for t in df["topic"].unique()}
    keys, praw = [], []
    for t, r in results.items():
        for _, row in r.iterrows():
            if not np.isnan(row["p_raw"]):
                keys.append((t, row["textbook"]))
                praw.append(row["p_raw"])
    padj = dict(zip(keys, holm_adjust(praw)))     # поправка по всем темам сразу
    rows = []
    for t, r in results.items():
        base = r.attrs["base"]
        r = r.copy()
        r["p_g"] = [padj.get((t, b), np.nan) for b in r["textbook"]]
        best = r.loc[r["adj_effect"].idxmax()]
        if best["textbook"] != base:
            ok = best["p_g"] < ALPHA and best["reliable"]
            name = best["textbook"] if ok else NO_DIFF
        else:
            worse = r[(r["textbook"] != base) & (r["p_g"] < ALPHA)
                      & (r["adj_effect"] < 0) & r["reliable"]]
            name = base if not worse.empty else NO_DIFF
        rows.append({"topic": t, "best_textbook": name,
                     "adj_effect_vs_base": best["adj_effect"], "p_value": best["p_g"],
                     "effect_size": best["effect_size"]})
    return pd.DataFrame(rows)


def textbook_school_overlap(df):
    out = df.groupby("textbook").agg(n=("score", "size"), schools=("school", "nunique")).reset_index()
    out["single_school"] = out["schools"] < 2
    return out


# ---------- Часы ----------
def _split(total, weights):
    raw = weights * total / weights.sum()
    base = np.floor(raw).astype(int)
    rem = int(total - base.sum())
    for k in (raw - base).sort_values(ascending=False).index[:rem]:
        base.loc[k] += 1
    return base


def _allocate(g, budget, min_h, max_growth):
    cur = g["hours_current"].astype(float)
    lower = np.minimum(min_h, cur).round()
    upper = np.maximum((cur * (1 + max_growth)).round(), cur)
    budget = int(min(max(budget, lower.sum()), upper.sum()))
    weight = 0.4 + g["difficulty_index"] / 100
    hours = (budget * weight / weight.sum()).clip(lower=lower, upper=upper).round()
    diff = int(budget - hours.sum())
    order = g["difficulty_index"].sort_values(ascending=(diff < 0)).index
    step = 1 if diff > 0 else -1
    while diff != 0:
        moved = False
        for idx in order:
            if diff == 0:
                break
            new = hours[idx] + step
            if lower[idx] <= new <= upper[idx]:
                hours[idx] = new
                diff -= step
                moved = True
        if not moved:
            break
    return hours.astype(int)


def recommend_hours(ts, total_hours=None, min_h=4, max_growth=0.5):
    """Часы перераспределяются внутри каждого класса: бюджет класса фиксирован."""
    t = ts.copy().reset_index(drop=True)
    cur_total = int(t["hours_current"].sum())
    total = int(total_hours or cur_total)
    grade_cur = t.groupby("grade")["hours_current"].sum().astype(float)
    budgets = _split(total, grade_cur)
    hours = pd.Series(0, index=t.index, dtype=int)
    for grade, idx in t.groupby("grade").groups.items():
        hours.loc[idx] = _allocate(t.loc[idx], budgets[grade], min_h, max_growth)
    t["hours_recommended"] = hours.astype(int)
    t["delta"] = t["hours_recommended"] - t["hours_current"]
    t["why"] = np.where(
        t["delta"] > 0, "Сложная тема: низкий балл и много слабых результатов",
        np.where(t["delta"] < 0, "Тема усваивается хорошо, часы можно перераспределить",
                 "Без изменений"))
    return t
