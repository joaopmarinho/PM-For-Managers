"""
miner.py — Apriori engine + Definição 18 (Likert) scoring.

Public API
----------
run_apriori(df, antecedent_cols, min_support, min_confidence)
    → dict with keys: "rules_df", "scored_df", "itemsets_count", "rules_count"
"""

import warnings

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

from engine.data_utils import (
    CATEGORY_COL,
    extract_label,
    get_category_values,
    get_col_values,
    one_hot_encode,
    prepare_dataframe,
)

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────
# Definição 18 — Likert weight tables
# ──────────────────────────────────────────────────────────────────
W_ATT: dict[str, int] = {
    "Activity": 1,
    "Resource": 1,
    "Data Object": 3,
    "Operation": 1,
    "Category": 5,
}

W_VAL: dict[str, int] = {
    # Category values → severity
    "Illegal activity": 5,
    "Illegal data access": 5,
    "Prohibited activity": 5,
    "Prohibited data access": 5,
    "Ignored mandatory activity": 3,
    "Ignored mandatory data access": 3,
    "Unexpected activity": 2,
    "Unexpected data access": 2,
    # Data Object values
    "Codigo": 4,
    "Requisito": 4,
    "PF": 2,
}

DEFAULT_W_ATT = 1
DEFAULT_W_VAL = 1


def _parse_item(item: str) -> tuple[str, str]:
    """Split 'Attribute=Value' → (attribute, value)."""
    if "=" in item:
        attr, val = item.split("=", 1)
        return attr, val
    return "", item


def _relevance_def18(row: pd.Series) -> int:
    """
    Definição 18:
        rel(raf) = Σ_{x∈X}(w_att(x) + w_val(x))  +  (w_att(y) + w_val(y))
    """
    total = 0
    for item in list(row["antecedents"]) + list(row["consequents"]):
        attr, val = _parse_item(item)
        total += W_ATT.get(attr, DEFAULT_W_ATT) + W_VAL.get(val, DEFAULT_W_VAL)
    return total


# ──────────────────────────────────────────────────────────────────
# Main mining function
# ──────────────────────────────────────────────────────────────────

def run_apriori(
    df: pd.DataFrame,
    antecedent_cols: list[str],
    min_support: float = 0.05,
    min_confidence: float = 0.8,
) -> dict:
    """
    Mine association rules where antecedents come from *antecedent_cols*
    and the consequent is always the Category column.

    Returns
    -------
    dict:
        itemsets_count  — number of frequent itemsets
        rules_count     — total rules before filtering
        rules_df        — filtered rules DataFrame (raw mlxtend output)
        scored_df       — human-readable table with Likert relevance score
    """
    if not antecedent_cols:
        raise ValueError("Selecione ao menos uma coluna antecedente.")

    df = prepare_dataframe(df)
    oh = one_hot_encode(df, antecedent_cols)

    freq = apriori(oh, min_support=min_support, use_colnames=True)
    if freq.empty:
        return {
            "itemsets_count": 0,
            "rules_count": 0,
            "rules_df": pd.DataFrame(),
            "scored_df": pd.DataFrame(),
        }

    rules = association_rules(freq, metric="confidence", min_threshold=min_confidence)

    cat_values = get_category_values(df)
    ant_value_sets = [get_col_values(df, c) for c in antecedent_cols]

    def _valid_antecedent(items: frozenset) -> bool:
        """At least one item from each selected column."""
        return all(bool(items & s) for s in ant_value_sets)

    mask = rules["antecedents"].apply(_valid_antecedent) & rules["consequents"].apply(
        lambda x: x.issubset(cat_values) and len(x) > 0
    )
    filtered = rules[mask].copy()

    if filtered.empty:
        return {
            "itemsets_count": len(freq),
            "rules_count": len(rules),
            "rules_df": filtered,
            "scored_df": pd.DataFrame(),
        }

    # ── Score with Definição 18 ──────────────────────────────────
    filtered["relevance"] = filtered.apply(_relevance_def18, axis=1)
    filtered.sort_values("relevance", ascending=False, inplace=True)

    # Build human-readable labels
    ant_labels: list[str] = []
    for _, row in filtered.iterrows():
        parts = []
        for col in antecedent_cols:
            val = extract_label(row["antecedents"], col)
            if val:
                parts.append(f"{col}: {val}")
        ant_labels.append(" | ".join(parts))

    scored = pd.DataFrame(
        {
            "Antecedentes": ant_labels,
            "Categoria da Anomalia": filtered["consequents"].apply(
                lambda x: extract_label(x, CATEGORY_COL)
            ),
            "Suporte": filtered["support"].round(4),
            "Confiança": filtered["confidence"].round(4),
            "Relevância (rel)": filtered["relevance"].astype(int),
        }
    ).reset_index(drop=True)

    return {
        "itemsets_count": len(freq),
        "rules_count": len(rules),
        "rules_df": filtered.reset_index(drop=True),
        "scored_df": scored,
    }
