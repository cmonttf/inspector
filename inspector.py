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


def inspeccionar_proyecto(directorio: Path) -> dict:
    archivos = obtener_archivos(directorio)

    framework = detectar_framework_php(directorio, archivos)
    php = detectar_php_puro(directorio, archivos)

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