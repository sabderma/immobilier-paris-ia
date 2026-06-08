from __future__ import annotations

from typing import Any

import pandas as pd


def formater_entier(valeur: float | int | None) -> str:
    if valeur is None or pd.isna(valeur):
        return "—"
    return f"{int(round(valeur)):,}".replace(",", " ")


def formater_euros(valeur: float | int | None) -> str:
    if valeur is None or pd.isna(valeur):
        return "—"
    return f"{formater_entier(valeur)} €"


def formater_decimal(valeur: float | int | None, suffixe: str = "") -> str:
    if valeur is None or pd.isna(valeur):
        return "—"
    return f"{float(valeur):.1f}".replace(".", ",") + suffixe


def formater_date(valeur: Any | None) -> str:
    if valeur is None or pd.isna(valeur):
        return "—"
    date = pd.to_datetime(valeur, errors="coerce")
    if pd.isna(date):
        return "—"
    return date.strftime("%d/%m/%Y")
