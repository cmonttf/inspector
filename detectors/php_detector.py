from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Dict, Any

from ..models import DetectionResult, Evidence
from ..utils import leer_json


def detectar_php_puro(
    directorio: Path,
    archivos: List[Path],
    framework_detectado: Optional[str] = None,
) -> DetectionResult:
    composer_json = directorio / "composer.json"
    composer_lock = directorio / "composer.lock"

    usa_php = any(
        a.suffix.lower() == ".php" or a.name.lower().endswith(".blade.php")
        for a in archivos
    )

    datos: Dict[str, Any] = {
        "usa_php": usa_php,
        "php_puro": False,
        "framework_detectado": framework_detectado,
        "version_php_requerida": None,
        "platform_php": None,
        "version_php_detectada_por_dependencias": None,
        "composer": composer_json.exists(),
        "composer_lock": composer_lock.exists(),
    }
    evidencias: List[Evidence] = []

    if composer_json.exists():
        composer = leer_json(composer_json)
        if isinstance(composer, dict):
            php_req = (composer.get("require") or {}).get("php")
            if php_req:
                datos["version_php_requerida"] = php_req
                evidencias.append(
                    Evidence(
                        tipo="composer",
                        archivo="composer.json",
                        detalle="require.php = {}".format(php_req),
                    )
                )

            platform_php = ((composer.get("config") or {}).get("platform") or {}).get("php")
            if platform_php:
                datos["platform_php"] = platform_php
                evidencias.append(
                    Evidence(
                        tipo="composer",
                        archivo="composer.json",
                        detalle="config.platform.php = {}".format(platform_php),
                    )
                )

    framework_real = framework_detectado if framework_detectado not in (None, "none") else None
    php_puro = bool(usa_php and framework_real is None)

    datos["php_puro"] = php_puro

    if framework_real:
        evidencias.append(
            Evidence(
                tipo="framework",
                archivo=None,
                detalle="Se detectó framework PHP: {}".format(framework_real),
            )
        )

    return DetectionResult(
        nombre="php_puro",
        detectado=php_puro,
        confianza="alta" if php_puro else "media" if usa_php else "baja",
        datos=datos,
        evidencias=evidencias,
    )