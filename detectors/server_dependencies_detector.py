from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Set

from ..models import DetectionResult, Evidence
from ..utils import leer_json, buscar_regex_en_archivos


PATRONES_INCLUDES_EXTERNOS = [
    ("require_absoluto_unix", r"""(?:require|include|require_once|include_once)\s*\(?\s*['"]/(?:[^'"]+)['"]\s*\)?"""),
    ("require_absoluto_windows", r"""(?:require|include|require_once|include_once)\s*\(?\s*['"][A-Za-z]:\\(?:[^'"]+)['"]\s*\)?"""),
    ("set_include_path", r"""\bset_include_path\s*\("""),
]

PATRONES_EJECUCION_SISTEMA = [
    ("exec_call", r"""\bexec\s*\("""),
    ("shell_exec_call", r"""\bshell_exec\s*\("""),
    ("system_call", r"""\bsystem\s*\("""),
    ("passthru_call", r"""\bpassthru\s*\("""),
    ("proc_open_call", r"""\bproc_open\s*\("""),
]

PATRONES_BINARIOS_REALES = [
    ("wkhtmltopdf", r"""\b(?:exec|shell_exec|system|passthru|popen|proc_open)\s*\([^)]*?\bwkhtmltopdf\b"""),
    ("java", r"""\b(?:exec|shell_exec|system|passthru|popen|proc_open)\s*\([^)]*?\bjava\b"""),
    ("ghostscript_gs", r"""\b(?:exec|shell_exec|system|passthru|popen|proc_open)\s*\([^)]*?\bgs\b"""),
    ("imagemagick_convert", r"""\b(?:exec|shell_exec|system|passthru|popen|proc_open)\s*\([^)]*?\bconvert\b"""),
    ("curl_bin", r"""\b(?:exec|shell_exec|system|passthru|popen|proc_open)\s*\([^)]*?\bcurl\b"""),
    ("wget_bin", r"""\b(?:exec|shell_exec|system|passthru|popen|proc_open)\s*\([^)]*?\bwget\b"""),
    ("pdftk", r"""\b(?:exec|shell_exec|system|passthru|popen|proc_open)\s*\([^)]*?\bpdftk\b"""),
    ("libreoffice", r"""\b(?:exec|shell_exec|system|passthru|popen|proc_open)\s*\([^)]*?\blibreoffice\b"""),
    ("soffice", r"""\b(?:exec|shell_exec|system|passthru|popen|proc_open)\s*\([^)]*?\bsoffice\b"""),
]

EXTS = {
    ".php", ".blade.php", ".py", ".sh", ".bash", ".zsh", ".ps1", ".bat",
    ".conf", ".ini"
}


def detectar_dependencias_servidor(directorio: Path, archivos: List[Path]) -> DetectionResult:
    evidencias = []
    datos = {
        "extensiones_php": [],
        "composer_platform_reqs": [],
        "include_path_detectado": False,
        "includes_externos": [],
        "binarios_externos": [],
        "activa_comandos_sistema": False,
        "hallazgos_codigo": 0,
        "riesgo_dependencia_servidor": "bajo",
    }

    composer_path = directorio / "composer.json"
    if composer_path.exists():
        composer = leer_json(composer_path)
        if isinstance(composer, dict):
            for bloque in ("require", "require-dev"):
                deps = composer.get(bloque) or {}
                for nombre, version in deps.items():
                    if nombre.startswith("ext-"):
                        datos["extensiones_php"].append({"nombre": nombre, "version": version})
                        evidencias.append(
                            Evidence(
                                tipo="composer",
                                archivo="composer.json",
                                detalle="{}.{} = {}".format(bloque, nombre, version),
                            )
                        )

            include_path = composer.get("include-path")
            if include_path:
                datos["composer_platform_reqs"] = include_path if isinstance(include_path, list) else [include_path]
                evidencias.append(
                    Evidence(
                        tipo="composer",
                        archivo="composer.json",
                        detalle="include-path configurado: {}".format(datos["composer_platform_reqs"]),
                    )
                )

    hallazgos_includes = buscar_regex_en_archivos(
        archivos=archivos,
        directorio_base=directorio,
        patrones=PATRONES_INCLUDES_EXTERNOS,
        extensiones_permitidas=EXTS,
        max_resultados_por_patron=15,
    )

    hallazgos_sistema = buscar_regex_en_archivos(
        archivos=archivos,
        directorio_base=directorio,
        patrones=PATRONES_EJECUCION_SISTEMA,
        extensiones_permitidas=EXTS,
        max_resultados_por_patron=15,
    )

    hallazgos_binarios = buscar_regex_en_archivos(
        archivos=archivos,
        directorio_base=directorio,
        patrones=PATRONES_BINARIOS_REALES,
        extensiones_permitidas=EXTS,
        max_resultados_por_patron=15,
    )

    includes_externos = []
    include_path_detectado = False

    for h in hallazgos_includes:
        if h["patron"] in {"require_absoluto_unix", "require_absoluto_windows"}:
            includes_externos.append(
                {
                    "archivo": h["archivo"],
                    "linea": h["linea"],
                    "texto": h["texto"],
                }
            )
        elif h["patron"] == "set_include_path":
            include_path_detectado = True

        evidencias.append(
            Evidence(
                tipo="codigo",
                archivo=h["archivo"],
                detalle="{} en línea {}: {}".format(h["patron"], h["linea"], h["texto"]),
            )
        )

    binarios = set()
    for h in hallazgos_binarios:
        binarios.add(h["patron"])
        evidencias.append(
            Evidence(
                tipo="codigo",
                archivo=h["archivo"],
                detalle="{} en línea {}: {}".format(h["patron"], h["linea"], h["texto"]),
            )
        )

    for h in hallazgos_sistema:
        evidencias.append(
            Evidence(
                tipo="codigo",
                archivo=h["archivo"],
                detalle="{} en línea {}: {}".format(h["patron"], h["linea"], h["texto"]),
            )
        )

    datos["include_path_detectado"] = include_path_detectado
    datos["includes_externos"] = includes_externos[:20]
    datos["binarios_externos"] = sorted(binarios)
    datos["activa_comandos_sistema"] = len(hallazgos_sistema) > 0
    datos["hallazgos_codigo"] = len(hallazgos_includes) + len(hallazgos_sistema) + len(hallazgos_binarios)

    if datos["includes_externos"] or datos["binarios_externos"]:
        datos["riesgo_dependencia_servidor"] = "alto"
    elif datos["extensiones_php"] or datos["include_path_detectado"] or datos["activa_comandos_sistema"]:
        datos["riesgo_dependencia_servidor"] = "medio"

    detectado = bool(
        datos["extensiones_php"]
        or datos["include_path_detectado"]
        or datos["includes_externos"]
        or datos["binarios_externos"]
        or datos["activa_comandos_sistema"]
    )

    confianza = "alta" if datos["includes_externos"] or datos["binarios_externos"] else "media" if detectado else "baja"

    return DetectionResult(
        nombre="dependencias_servidor",
        detectado=detectado,
        confianza=confianza,
        datos=datos,
        evidencias=evidencias[:30],
    )