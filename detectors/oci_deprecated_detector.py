from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

from ..models import DetectionResult, Evidence
from ..utils import buscar_regex_en_archivos


OCI_DEPRECATED_PATTERNS = [
    ("ocilogon", r"\bocilogon\s*\("),
    ("ocinlogon", r"\bocinlogon\s*\("),
    ("ociplogon", r"\bociplogon\s*\("),
    ("ociparse", r"\bociparse\s*\("),
    ("ociexecute", r"\bociexecute\s*\("),
    ("ocifetch", r"\bocifetch\s*\("),
    ("ocifetchstatement", r"\bocifetchstatement\s*\("),
    ("ocifetchinto", r"\bocifetchinto\s*\("),
    ("ociresult", r"\bociresult\s*\("),
    ("ocinumcols", r"\bocinumcols\s*\("),
    ("ocicolumnname", r"\bocicolumnname\s*\("),
    ("ocicolumnsize", r"\bocicolumnsize\s*\("),
    ("ocicolumnscale", r"\bocicolumnscale\s*\("),
    ("ocicolumnprecision", r"\bocicolumnprecision\s*\("),
    ("ocicolumntype", r"\bocicolumntype\s*\("),
    ("ocicolumntyperaw", r"\bocicolumntyperaw\s*\("),
    ("ocifreestatement", r"\bocifreestatement\s*\("),
    ("ocierror", r"\bocierror\s*\("),
    ("ocicancel", r"\bocicancel\s*\("),
    ("ocicommit", r"\bocicommit\s*\("),
    ("ocirollback", r"\bocirollback\s*\("),
    ("ocinewcursor", r"\bocinewcursor\s*\("),
    ("ocinewdescriptor", r"\bocinewdescriptor\s*\("),
    ("ocinewcollection", r"\bocinewcollection\s*\("),
    ("ocibindbyname", r"\bocibindbyname\s*\("),
    ("ocidefinebyname", r"\bocidefinebyname\s*\("),
    ("ocisavelob", r"\bocisavelob\s*\("),
    ("ocisavelobfile", r"\bocisavelobfile\s*\("),
    ("ociloadlob", r"\bociloadlob\s*\("),
    ("ociwritelobtofile", r"\bociwritelobtofile\s*\("),
    ("ocisetprefetch", r"\bocisetprefetch\s*\("),
]

OCI_REPLACEMENTS = {
    "ocilogon": "oci_connect",
    "ocinlogon": "oci_new_connect",
    "ociplogon": "oci_pconnect",
    "ociparse": "oci_parse",
    "ociexecute": "oci_execute",
    "ocifetch": "oci_fetch",
    "ocifetchstatement": "oci_fetch_all",
    "ocifetchinto": "oci_fetch_array / oci_fetch_assoc / oci_fetch_row / oci_fetch_object",
    "ociresult": "oci_result",
    "ocinumcols": "oci_num_fields",
    "ocicolumnname": "oci_field_name",
    "ocicolumnsize": "oci_field_size",
    "ocicolumnscale": "oci_field_scale",
    "ocicolumnprecision": "oci_field_precision",
    "ocicolumntype": "oci_field_type",
    "ocicolumntyperaw": "oci_field_type_raw",
    "ocifreestatement": "oci_free_statement",
    "ocierror": "oci_error",
    "ocicancel": "oci_cancel",
    "ocicommit": "oci_commit",
    "ocirollback": "oci_rollback",
    "ocinewcursor": "oci_new_cursor",
    "ocinewdescriptor": "oci_new_descriptor",
    "ocinewcollection": "oci_new_collection",
    "ocibindbyname": "oci_bind_by_name",
    "ocidefinebyname": "oci_define_by_name",
    "ocisavelob": "oci_lob->save",
    "ocisavelobfile": "oci_lob->import",
    "ociloadlob": "oci_lob->load",
    "ociwritelobtofile": "oci_lob->export",
    "ocisetprefetch": "oci_set_prefetch",
}

EXTS = {".php", ".blade.php", ".inc", ".phtml"}


def detectar_oci_deprecado(directorio: Path, archivos: List[Path]) -> DetectionResult:
    hallazgos = buscar_regex_en_archivos(
        archivos=archivos,
        directorio_base=directorio,
        patrones=OCI_DEPRECATED_PATTERNS,
        extensiones_permitidas=EXTS,
        max_resultados_por_patron=50,
    )

    evidencias = []
    resumen: Dict[str, int] = {}

    for h in hallazgos:
        metodo = h["patron"]
        resumen[metodo] = resumen.get(metodo, 0) + 1
        reemplazo = OCI_REPLACEMENTS.get(metodo, "sin reemplazo definido")

        evidencias.append(
            Evidence(
                tipo="codigo",
                archivo=h["archivo"],
                detalle="{} en línea {} -> usar {}. Fragmento: {}".format(
                    metodo,
                    h["linea"],
                    reemplazo,
                    h["texto"],
                ),
            )
        )

    total = len(hallazgos)
    detectado = total > 0
    confianza = "alta" if total > 0 else "baja"

    return DetectionResult(
        nombre="oci_deprecado",
        detectado=detectado,
        confianza=confianza,
        datos={
            "total_hallazgos": total,
            "metodos_detectados": resumen,
            "usa_oci_deprecado": detectado,
        },
        evidencias=evidencias[:50],
    )