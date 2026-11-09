import numpy as np
import pandas as pd
from scipy import stats

LOW_THRESHOLD = 50
MIN_N = 30


def _minmax(s):
    rng = s.max() - s.min()
    return (s - s.min()) / rng if rng > 0 else s * 0


def topic_stats(df, threshold=LOW_THRESHOLD):
    g = df.groupby(["grade", "topic"])
    out = g["score"].agg(n="count", mean="mean", median="median", std="std").reset_index()
    out["share_low"] = g["score"].apply(lambda x: (x < threshold).mean()).values
    out["hours_current"] = g["hours_current"].first().values
    out["difficulty_index"] = 100 * (
        0.55 * _minmax(100 - out["mean"])
        + 0.30 * _minmax(out["share_low"])
        + 0.15 * _minmax(out["std"])
    )
    out["is_hard"] = out["difficulty_index"] >= out["difficulty_index"].quantile(0.8)
    return out.sort_values("difficulty_index", ascending=False).reset_index(drop=True)


def compare_textbooks(df, topic):
    d = df[df["topic"] == topic].copy()
    books = sorted(d["textbook"].unique())
    base = books[0]
    X = np.column_stack(
        [np.ones(len(d)), d["pre_score"].to_numpy()]
        + [(d["textbook"] == b).astype(float).to_numpy() for b in books[1:]]
    )
    y = d["score"].to_numpy()
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    dof = len(y) - X.shape[1]
    sigma2 = resid @ resid / dof
    cov = sigma2 * np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    tcrit = stats.t.ppf(0.975, dof)

    rows = []
    for b in books:
        sub = d[d["textbook"] == b]
        row = {"textbook": b, "n": len(sub), "mean_score": sub["score"].mean()}
        if b == base:
            row.update(adj_effect=0.0, ci_low=0.0, ci_high=0.0, p_value=np.nan)
        else:
            i = 2 + books.index(b) - 1
            t = beta[i] / se[i]
            row.update(
                adj_effect=beta[i], ci_low=beta[i] - tcrit * se[i],
                ci_high=beta[i] + tcrit * se[i],
                p_value=2 * (1 - stats.t.cdf(abs(t), dof)),
            )
        row["reliable"] = row["n"] >= MIN_N
        rows.append(row)
    res = pd.DataFrame(rows)
    res.attrs["base"] = base
    return res


def best_textbook_by_topic(df):
    rows = []
    for topic in df["topic"].unique():
        r = compare_textbooks(df, topic)
        base = r.attrs["base"]
        best = r.loc[r["adj_effect"].idxmax()]
        significant = best["textbook"] != base and best["p_value"] < 0.05 and best["reliable"]
        rows.append({"topic": topic,
                     "best_textbook": best["textbook"] if significant else "нет значимой разницы",
                     "adj_effect_vs_base": best["adj_effect"], "p_value": best["p_value"]})
    return pd.DataFrame(rows)


def recommend_hours(ts, total_hours=None, min_h=4, max_growth=0.5):
    t = ts.copy()
    total = int(total_hours or t["hours_current"].sum())
    weight = 0.4 + t["difficulty_index"] / 100
    raw = total * weight / weight.sum()
    upper = (t["hours_current"] * (1 + max_growth)).round()
    hours = raw.clip(lower=min_h, upper=upper).round()
    diff = int(total - hours.sum())
    order = t["difficulty_index"].sort_values(ascending=(diff < 0)).index
    for idx in list(order) * 20:
        if diff == 0:
            break
        step = 1 if diff > 0 else -1
        new = hours[idx] + step
        if min_h <= new <= upper[idx]:
            hours[idx] = new
            diff -= step
    t["hours_recommended"] = hours.astype(int)
    t["delta"] = t["hours_recommended"] - t["hours_current"]
    t["why"] = np.where(
        t["delta"] > 0, "Сложная тема: низкий балл и много слабых результатов",
        np.where(t["delta"] < 0, "Тема усваивается хорошо, часы можно перераспределить",
                 "Без изменений"))
    return t


if __name__ == "__main__":
    df = pd.read_csv("data/results.csv")
    ts = topic_stats(df)
    print("\nТОП-7 сложных тем:")
    print(ts.head(7)[["grade", "topic", "mean", "share_low", "difficulty_index"]].round(1).to_string(index=False))
    print("\nУчебники на теме «Тригонометрия»:")
    print(compare_textbooks(df, "Тригонометрия").round(2).to_string(index=False))
    print("\nЛучший учебник по темам:")
    print(best_textbook_by_topic(df).round(3).to_string(index=False))
    rec = recommend_hours(ts)
    print("\nЧасы: было -> рекомендуется (топ изменений):")
    print(rec.reindex(rec["delta"].abs().sort_values(ascending=False).index).head(8)
          [["topic", "hours_current", "hours_recommended", "delta"]].to_string(index=False))
    print("Сумма часов:", rec["hours_current"].sum(), "->", rec["hours_recommended"].sum())