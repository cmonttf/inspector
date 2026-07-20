from __future__ import annotations

from pathlib import Path
from typing import List

from ..models import DetectionResult, Evidence
from ..utils import buscar_regex_en_archivos


PATRONES_JS = [
    ("npm_kendo", r"@progress/kendo"),
    ("cdn_kendo", r"kendo\.cdn\.telerik\.com"),
    ("script_kendo", r"\bkendo(?:\.all|\.aspnetmvc|\.timezones|\.web|\.mobile)?(?:\.min)?\.js\b"),
    ("kendo_plugin", r"\.kendo(?:Grid|DropDownList|ComboBox|DatePicker|DateTimePicker|Editor|Upload|Window|TabStrip|TreeView|Scheduler|Validator|NumericTextBox|AutoComplete|MultiSelect)\s*\("),
    ("kendo_namespace", r"\bkendo\.(?:ui|data|observable|bind|template|destroy|version)\b"),
]

PATRONES_ASSETS = [
    ("css_kendo", r"\bkendo(?:\.common|\.default|\.bootstrap|\.material|\.theme)?(?:[-.\w]*)?\.css\b"),
]

PATRONES_MVVM = [
    (
        "kendo_data_role",
        r'data-role\s*=\s*["\'](?:grid|datepicker|datetimepicker|dropdownlist|combobox|autocomplete|multiselect|numerictextbox|editor|upload|window|tabstrip|treeview|scheduler|validator|listview|chart|calendar|menu|panelbar|tooltip|dialog|drawer|splitter)["\']'
    ),
]

PATRONES_CSS = [
    (
        "kendo_class",
        r'class\s*=\s*["\'][^"\']*\bk-(?:widget|grid|button|input|dropdown|datepicker|window|tabstrip|treeview|textbox|menu|toolbar|calendar)\b[^"\']*["\']'
    ),
]

EXTS = {
    ".php",
    ".blade.php",
    ".html",
    ".htm",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".vue",
    ".cshtml",
}


def detectar_kendo(directorio: Path, archivos: List[Path]) -> DetectionResult:

    js = buscar_regex_en_archivos(
        archivos,
        directorio,
        PATRONES_JS,
        EXTS,
        10,
    )

    assets = buscar_regex_en_archivos(
        archivos,
        directorio,
        PATRONES_ASSETS,
        EXTS,
        10,
    )

    mvvm = buscar_regex_en_archivos(
        archivos,
        directorio,
        PATRONES_MVVM,
        EXTS,
        10,
    )

    css = buscar_regex_en_archivos(
        archivos,
        directorio,
        PATRONES_CSS,
        EXTS,
        20,
    )

    score = (
        len(js) * 10 +
        len(assets) * 8 +
        len(mvvm) * 6 +
        len(css) * 1
    )

    tiene_js = len(js) > 0
    tiene_assets = len(assets) > 0
    tiene_mvvm = len(mvvm) > 0
    tiene_css = len(css) > 0

    if tiene_js:
        detectado = True
        confianza = "alta"

    elif tiene_assets and tiene_css:
        detectado = True
        confianza = "alta"

    elif tiene_assets:
        detectado = True
        confianza = "media"

    elif tiene_mvvm and tiene_css:
        detectado = True
        confianza = "media"

    elif len(css) >= 10:
        detectado = True
        confianza = "media"

    elif tiene_css:
        detectado = False
        confianza = "baja"

    else:
        detectado = False
        confianza = "baja"

    evidencias = []

    for grupo in (js, assets, mvvm, css):
        for h in grupo:
            evidencias.append(
                Evidence(
                    tipo="codigo",
                    archivo=h["archivo"],
                    detalle=f'{h["patron"]} en línea {h["linea"]}: {h["texto"]}',
                )
            )

    return DetectionResult(
        nombre="kendo",
        detectado=detectado,
        confianza=confianza,
        datos={
            "score": score,
            "usa_kendo": detectado,

            "javascript": len(js),
            "assets": len(assets),
            "mvvm": len(mvvm),
            "clases_css": len(css),

            "hallazgos_fuertes": len(js) + len(assets),
        },
        evidencias=evidencias[:20],
    )