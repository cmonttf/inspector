from __future__ import annotations

from pathlib import Path
from typing import List

from ..models import DetectionResult, Evidence
from ..utils import buscar_regex_en_archivos


PATRONES_KENDO_FUERTES = [
    ("cdn_kendo", r"kendo\.cdn\.telerik\.com"),
    ("script_kendo", r"\bkendo(?:\.all|\.aspnetmvc|\.timezones|\.web|\.mobile)?(?:\.min)?\.js\b"),
    ("css_kendo", r"\bkendo(?:\.common|\.default|\.bootstrap|\.material|\.theme)?(?:[-.\w]*)?\.css\b"),
    ("kendo_jquery_plugin", r"\.kendo(?:Grid|DropDownList|ComboBox|DatePicker|DateTimePicker|Editor|Upload|Window|TabStrip|TreeView|Scheduler|Validator|NumericTextBox|AutoComplete|MultiSelect)\s*\("),
    ("kendo_namespace", r"\bkendo\.(?:ui|data|observable|bind|template|destroy)\b"),
    ("kendo_class", r'class\s*=\s*["\'][^"\']*\bk-(?:widget|grid|button|input|dropdown|datepicker|window|tabstrip|treeview)\b[^"\']*["\']'),
]

PATRONES_KENDO_MVVM = [
    (
        "kendo_data_role_widget",
        r'data-role\s*=\s*["\'](?:grid|datepicker|datetimepicker|dropdownlist|combobox|autocomplete|multiselect|numerictextbox|editor|upload|window|tabstrip|treeview|scheduler|validator|listview|chart|calendar|menu|panelbar|tooltip|dialog|drawer|splitter)["\']'
    ),
]

EXTS = {
    ".php", ".blade.php", ".html", ".htm", ".js", ".ts", ".tsx", ".jsx", ".vue", ".cshtml"
}


def detectar_kendo(directorio: Path, archivos: List[Path]) -> DetectionResult:
    hallazgos_fuertes = buscar_regex_en_archivos(
        archivos=archivos,
        directorio_base=directorio,
        patrones=PATRONES_KENDO_FUERTES,
        extensiones_permitidas=EXTS,
        max_resultados_por_patron=10,
    )

    hallazgos_mvvm = buscar_regex_en_archivos(
        archivos=archivos,
        directorio_base=directorio,
        patrones=PATRONES_KENDO_MVVM,
        extensiones_permitidas=EXTS,
        max_resultados_por_patron=10,
    )

    score = 0
    evidencias = []

    for hallazgo in hallazgos_fuertes:
        patron = hallazgo["patron"]

        if patron in {"cdn_kendo", "script_kendo", "css_kendo"}:
            score += 4
        elif patron in {"kendo_jquery_plugin", "kendo_namespace"}:
            score += 5
        elif patron == "kendo_class":
            score += 3

        evidencias.append(
            Evidence(
                tipo="codigo",
                archivo=hallazgo["archivo"],
                detalle="{} en línea {}: {}".format(
                    patron,
                    hallazgo["linea"],
                    hallazgo["texto"],
                ),
            )
        )

    for hallazgo in hallazgos_mvvm:
        score += 2
        evidencias.append(
            Evidence(
                tipo="codigo",
                archivo=hallazgo["archivo"],
                detalle="{} en línea {}: {}".format(
                    hallazgo["patron"],
                    hallazgo["linea"],
                    hallazgo["texto"],
                ),
            )
        )

    tiene_evidencia_fuerte = len(hallazgos_fuertes) > 0
    detectado = tiene_evidencia_fuerte or score >= 6
    confianza = "alta" if tiene_evidencia_fuerte else "media" if detectado else "baja"

    return DetectionResult(
        nombre="kendo",
        detectado=detectado,
        confianza=confianza,
        datos={
            "score": score,
            "cantidad_hallazgos_fuertes": len(hallazgos_fuertes),
            "cantidad_hallazgos_mvvm": len(hallazgos_mvvm),
            "usa_kendo": detectado,
        },
        evidencias=evidencias[:20],
    )