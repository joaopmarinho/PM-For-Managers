"""
data_utils.py — Dynamic One-Hot Encoding transformation.

Given a DataFrame and a list of selected antecedent columns,
produces a binary (bool) one-hot matrix ready for mlxtend's apriori.
Category is ALWAYS included as the fixed consequent column.
"""

import pandas as pd

CATEGORY_COL = "Category"


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Fill NaN / empty strings with 'None' to avoid broken itemsets."""
    df = df.copy()
    df.fillna("None", inplace=True)
    df.replace("", "None", inplace=True)
    return df


def one_hot_encode(df: pd.DataFrame, antecedent_cols: list[str]) -> pd.DataFrame:
    """
    One-hot encode *antecedent_cols* + CATEGORY_COL.

    Returns a boolean DataFrame with columns like  'Activity=Publicar solucao'.
    """
    cols = list(dict.fromkeys(antecedent_cols + [CATEGORY_COL]))  # dedup, ordered
    return pd.get_dummies(df[cols], prefix_sep="=", columns=cols).astype(bool)


def extract_label(items: frozenset, prefix: str) -> str:
    """Return the value part for the first item matching *prefix*=."""
    for item in items:
        if item.startswith(prefix + "="):
            return item.split("=", 1)[1]
    return ""


def get_category_values(df: pd.DataFrame) -> set[str]:
    return {f"{CATEGORY_COL}={v}" for v in df[CATEGORY_COL].unique()}


def get_col_values(df: pd.DataFrame, col: str) -> set[str]:
    return {f"{col}={v}" for v in df[col].unique()}
