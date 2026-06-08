from __future__ import annotations

from io import StringIO
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from api.core import DVF_CSV_PATH, construire_where_dvf, lire_sql, verifier_cle_api


router = APIRouter()


@router.get("/dvf/filtres")
def get_filtres_dvf(_: None = Depends(verifier_cle_api)) -> dict:
    stats = lire_sql(
        """
        SELECT
            MIN(annee_vente)::INTEGER AS annee_min,
            MAX(annee_vente)::INTEGER AS annee_max,
            MIN(valeur_fonciere)::FLOAT AS prix_min,
            MAX(valeur_fonciere)::FLOAT AS prix_max,
            MIN(prix_m2)::FLOAT AS prix_m2_min,
            MAX(prix_m2)::FLOAT AS prix_m2_max,
            MIN(surface_reelle_bati)::FLOAT AS surface_min,
            MAX(surface_reelle_bati)::FLOAT AS surface_max
        FROM dvf_paris_appartements;
        """
    ).iloc[0].to_dict()
    arrondissements = lire_sql(
        "SELECT DISTINCT arrondissement FROM dvf_paris_appartements ORDER BY arrondissement;"
    )["arrondissement"].astype(int).tolist()
    pieces = lire_sql(
        """
        SELECT DISTINCT nombre_pieces_principales
        FROM dvf_paris_appartements
        ORDER BY nombre_pieces_principales;
        """
    )["nombre_pieces_principales"].astype(int).tolist()
    return {**stats, "arrondissements": arrondissements, "pieces": pieces}


@router.get("/dvf/points")
def get_dvf_points(
    _: None = Depends(verifier_cle_api),
    arrondissement: Optional[int] = None,
    annee_vente: Optional[int] = None,
    annee_min: Optional[int] = None,
    annee_max: Optional[int] = None,
    mois_vente: Optional[int] = None,
    prix_min: Optional[float] = None,
    prix_max: Optional[float] = None,
    prix_m2_min: Optional[float] = None,
    prix_m2_max: Optional[float] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    nombre_pieces: Optional[int] = None,
    code_postal: Optional[str] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    limit: int = Query(800, ge=1, le=2000),
) -> dict:
    """Retourne un jeu de points léger pour l'affichage cartographique."""
    where, params = construire_where_dvf(
        arrondissement=arrondissement,
        annee_vente=annee_vente,
        annee_min=annee_min,
        annee_max=annee_max,
        mois_vente=mois_vente,
        prix_min=prix_min,
        prix_max=prix_max,
        prix_m2_min=prix_m2_min,
        prix_m2_max=prix_m2_max,
        surface_min=surface_min,
        surface_max=surface_max,
        nombre_pieces=nombre_pieces,
        code_postal=code_postal,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
    )
    df = lire_sql(
        f"""
        SELECT
            date_mutation::DATE::TEXT AS date_mutation,
            arrondissement,
            valeur_fonciere,
            prix_m2,
            surface_reelle_bati,
            nombre_pieces_principales,
            longitude,
            latitude
        FROM dvf_paris_appartements
        WHERE {where}
          AND longitude IS NOT NULL
          AND latitude IS NOT NULL
        ORDER BY date_mutation DESC, id_mutation DESC
        LIMIT :limit;
        """,
        {**params, "limit": limit},
    )
    return {
        "nombre_resultats": len(df),
        "limite": limit,
        "data": df.to_dict(orient="records"),
    }


@router.get("/dvf/export.csv")
def export_dvf_csv(
    _: None = Depends(verifier_cle_api),
    arrondissement: Optional[int] = None,
    annee_vente: Optional[int] = None,
    annee_min: Optional[int] = None,
    annee_max: Optional[int] = None,
    mois_vente: Optional[int] = None,
    prix_min: Optional[float] = None,
    prix_max: Optional[float] = None,
    prix_m2_min: Optional[float] = None,
    prix_m2_max: Optional[float] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    nombre_pieces: Optional[int] = None,
    code_postal: Optional[str] = None,
) -> Response:
    aucun_filtre = all(
        valeur is None
        for valeur in [
            arrondissement,
            annee_vente,
            annee_min,
            annee_max,
            mois_vente,
            prix_min,
            prix_max,
            prix_m2_min,
            prix_m2_max,
            surface_min,
            surface_max,
            nombre_pieces,
            code_postal,
        ]
    )
    if aucun_filtre and DVF_CSV_PATH.exists():
        return Response(
            DVF_CSV_PATH.read_text(encoding="utf-8"),
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    'attachment; filename="dvf_paris_clean_2021_2025.csv"'
                )
            },
        )

    where, params = construire_where_dvf(
        arrondissement=arrondissement,
        annee_vente=annee_vente,
        annee_min=annee_min,
        annee_max=annee_max,
        mois_vente=mois_vente,
        prix_min=prix_min,
        prix_max=prix_max,
        prix_m2_min=prix_m2_min,
        prix_m2_max=prix_m2_max,
        surface_min=surface_min,
        surface_max=surface_max,
        nombre_pieces=nombre_pieces,
        code_postal=code_postal,
    )
    df = lire_sql(
        f"""
        SELECT
            id_mutation,
            date_mutation,
            annee_vente,
            mois_vente,
            valeur_fonciere,
            prix_m2,
            surface_reelle_bati,
            nombre_pieces_principales,
            type_local,
            code_postal,
            arrondissement,
            nom_commune,
            adresse_nom_voie,
            longitude,
            latitude
        FROM dvf_paris_appartements
        WHERE {where}
        ORDER BY date_mutation DESC, id_mutation DESC;
        """,
        params,
    )
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    return Response(
        buffer.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                'attachment; filename="dvf_paris_clean_2021_2025_filtre.csv"'
            )
        },
    )
