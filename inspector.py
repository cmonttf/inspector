from __future__ import annotations

from pathlib import Path

from inspector.detectors import (
    detectar_php_puro,
    detectar_framework_php,
    detectar_kendo,
    detectar_dependencias_servidor,
    detectar_oci_deprecado,
)
from inspector.utils import obtener_archivos


def _resolver_directorio_inspeccion(directorio: Path) -> Path:
    if not directorio.exists() or not directorio.is_dir():
        return directorio

    candidatos = [directorio]
    for subdir in sorted(directorio.iterdir(), key=lambda p: p.name):
        if subdir.is_dir() and (subdir / "composer.json").exists():
            candidatos.append(subdir)

    for candidato in candidatos:
        composer_json = candidato / "composer.json"
        if composer_json.exists():
            try:
                import json
                composer = json.loads(composer_json.read_text(encoding="utf-8"))
            except Exception:
                composer = {}
            if isinstance(composer, dict):
                name = composer.get("name")
                if isinstance(name, str) and name in {"codeigniter/framework", "codeigniter4/framework"}:
                    return candidato

    for candidato in candidatos:
        if (candidato / "application" / "config" / "config.php").exists():
            return candidato
        if (candidato / "system" / "core" / "CodeIgniter.php").exists():
            return candidato
        if (candidato / "public" / "application" / "config" / "config.php").exists():
            return candidato
        if (candidato / "public" / "system" / "core" / "CodeIgniter.php").exists():
            return candidato

    return directorio


def inspeccionar_proyecto(directorio: Path) -> dict:
    directorio_inspeccion = _resolver_directorio_inspeccion(directorio)
    archivos = obtener_archivos(directorio_inspeccion)

    framework = detectar_framework_php(directorio_inspeccion, archivos)
    php = detectar_php_puro(directorio_inspeccion, archivos)

    framework_name = framework.datos.get("framework")
    usa_php = php.datos.get("usa_php", False)

    framework_detectado = framework_name not in (None, "none")
    php_puro = bool(usa_php and not framework_detectado)

    kendo = detectar_kendo(directorio, archivos)
    dependencias = detectar_dependencias_servidor(directorio, archivos)
    oci_deprecado = detectar_oci_deprecado(directorio, archivos)

    php_dict = php.to_dict()
    php_dict["nombre"] = "php_puro"
    php_dict["detectado"] = php_puro
    php_dict["datos"]["php_puro"] = php_puro
    php_dict["datos"]["framework_detectado"] = framework_name if framework_detectado else None

    return {
        "proyecto": str(directorio.resolve()),
        "archivos_analizados": len(archivos),
        "resumen": {
            "lenguaje_backend": "php" if usa_php else None,
            "framework_backend": framework_name if framework_detectado else None,
            "php_puro": php_puro,
        },
        "detectores": {
            "php_puro": php_dict,
            "framework_php": framework.to_dict(),
            "kendo": kendo.to_dict(),
            "dependencias_servidor": dependencias.to_dict(),
            "oci_deprecado": oci_deprecado.to_dict(),
        },
    }