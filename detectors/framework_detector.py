from __future__ import annotations

from pathlib import Path
import re

from inspector.models import DetectionResult, Evidence
from inspector.utils import leer_json, leer_texto


def extraer_version_laravel_desde_lock(directorio: Path) -> str | None:
    lock_path = directorio / "composer.lock"
    lock = leer_json(lock_path)
    if not isinstance(lock, dict):
        return None

    paquetes = (lock.get("packages") or []) + (lock.get("packages-dev") or [])
    for paquete in paquetes:
        if paquete.get("name") == "laravel/framework":
            return paquete.get("version")
    return None


def extraer_version_laravel_desde_vendor(directorio: Path) -> str | None:
    ruta = directorio / "vendor/laravel/framework/src/Illuminate/Foundation/Application.php"
    texto = leer_texto(ruta)
    if not texto:
        return None

    m = re.search(r"VERSION\s*=\s*['\"]([^'\"]+)['\"]", texto)
    return m.group(1) if m else None


def extraer_version_codeigniter(directorio: Path) -> str | None:
    candidatos = [
        directorio / "system/core/CodeIgniter.php",
        directorio / "system/CodeIgniter.php",
        directorio / "vendor/codeigniter4/framework/system/CodeIgniter.php",
    ]
    patron = re.compile(
        r"define\(\s*['\"]CI_VERSION['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)"
        r"|const\s+CI_VERSION\s*=\s*['\"]([^'\"]+)['\"]"
        r"|public\s+const\s+CI_VERSION\s*=\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE,
    )

    for archivo in candidatos:
        texto = leer_texto(archivo)
        if not texto:
            continue
        m = patron.search(texto)
        if m:
            return next((g for g in m.groups() if g), None)
    return None


def detectar_framework_php(directorio: Path, archivos: list[Path]) -> DetectionResult:
    composer_json = directorio / "composer.json"
    composer = leer_json(composer_json) if composer_json.exists() else {}
    require = (composer or {}).get("require", {}) if isinstance(composer, dict) else {}

    score = {
        "laravel": 0,
        "codeigniter3": 0,
        "codeigniter4": 0,
    }
    evidencias = []
    datos = {
        "framework": None,
        "framework_detectado": False,
        "php_puro": False,
        "version_requerida": None,
        "version_instalada": None,
        "score": score.copy(),
    }

    if "laravel/framework" in require:
        score["laravel"] += 5
        datos["version_requerida"] = require["laravel/framework"]
        evidencias.append(Evidence("framework", "composer.json", "require laravel/framework"))

    if (directorio / "artisan").exists():
        score["laravel"] += 5
        evidencias.append(Evidence("archivo", "artisan", "archivo artisan encontrado"))

    if (directorio / "bootstrap/app.php").exists():
        score["laravel"] += 2
        evidencias.append(Evidence("archivo", "bootstrap/app.php", "bootstrap de Laravel encontrado"))

    if (directorio / "routes").exists():
        score["laravel"] += 1
        evidencias.append(Evidence("directorio", "routes", "directorio routes encontrado"))

    if "codeigniter4/framework" in require:
        score["codeigniter4"] += 5
        datos["version_requerida"] = require["codeigniter4/framework"]
        evidencias.append(Evidence("framework", "composer.json", "require codeigniter4/framework"))

    if (directorio / "spark").exists():
        score["codeigniter4"] += 5
        evidencias.append(Evidence("archivo", "spark", "archivo spark encontrado"))

    if (directorio / "app/Config").exists():
        score["codeigniter4"] += 2
        evidencias.append(Evidence("directorio", "app/Config", "estructura de CI4 encontrada"))

    if (directorio / "system/core/CodeIgniter.php").exists():
        score["codeigniter3"] += 5
        evidencias.append(Evidence("archivo", "system/core/CodeIgniter.php", "núcleo de CI3 encontrado"))

    if (directorio / "application/config/config.php").exists():
        score["codeigniter3"] += 3
        evidencias.append(Evidence("archivo", "application/config/config.php", "estructura de CI3 encontrada"))

    datos["score"] = score.copy()
    mejor = max(score, key=score.get)

    hay_php = any(
        a.suffix.lower() == ".php" or a.name.lower().endswith(".blade.php")
        for a in archivos
    )

    if score[mejor] == 0:
        datos["framework"] = "none"
        datos["framework_detectado"] = False
        datos["php_puro"] = bool(hay_php)
        return DetectionResult(
            nombre="framework_php",
            detectado=hay_php,
            confianza="media" if hay_php else "baja",
            datos=datos,
            evidencias=evidencias,
        )

    datos["framework_detectado"] = True
    datos["php_puro"] = False

    if mejor == "laravel":
        datos["framework"] = "laravel"
        datos["version_instalada"] = (
            extraer_version_laravel_desde_lock(directorio)
            or extraer_version_laravel_desde_vendor(directorio)
        )
    elif mejor == "codeigniter3":
        datos["framework"] = "codeigniter3"
        datos["version_instalada"] = extraer_version_codeigniter(directorio)
    elif mejor == "codeigniter4":
        datos["framework"] = "codeigniter4"
        datos["version_instalada"] = extraer_version_codeigniter(directorio)

    confianza = "alta" if score[mejor] >= 5 else "media"

    return DetectionResult(
        nombre="framework_php",
        detectado=True,
        confianza=confianza,
        datos=datos,
        evidencias=evidencias,
    )
    composer_json = directorio / "composer.json"
    composer = leer_json(composer_json) if composer_json.exists() else {}
    require = (composer or {}).get("require", {}) if isinstance(composer, dict) else {}

    score = {
        "laravel": 0,
        "codeigniter3": 0,
        "codeigniter4": 0,
    }
    evidencias: list[Evidence] = []
    datos: dict = {
        "framework": None,
        "version_requerida": None,
        "version_instalada": None,
        "score": score.copy(),
    }

    if "laravel/framework" in require:
        score["laravel"] += 5
        datos["version_requerida"] = require["laravel/framework"]
        evidencias.append(Evidence("framework", "composer.json", "require laravel/framework"))

    if (directorio / "artisan").exists():
        score["laravel"] += 5
        evidencias.append(Evidence("archivo", "artisan", "archivo artisan encontrado"))

    if (directorio / "bootstrap/app.php").exists():
        score["laravel"] += 2
        evidencias.append(Evidence("archivo", "bootstrap/app.php", "bootstrap de Laravel encontrado"))

    if (directorio / "routes").exists():
        score["laravel"] += 1
        evidencias.append(Evidence("directorio", "routes", "directorio routes encontrado"))

    if "codeigniter4/framework" in require:
        score["codeigniter4"] += 5
        datos["version_requerida"] = require["codeigniter4/framework"]
        evidencias.append(Evidence("framework", "composer.json", "require codeigniter4/framework"))

    if (directorio / "spark").exists():
        score["codeigniter4"] += 5
        evidencias.append(Evidence("archivo", "spark", "archivo spark encontrado"))

    if (directorio / "app/Config").exists():
        score["codeigniter4"] += 2
        evidencias.append(Evidence("directorio", "app/Config", "estructura de CI4 encontrada"))

    ci3_core = directorio / "system/core/CodeIgniter.php"
    if ci3_core.exists():
        score["codeigniter3"] += 5
        evidencias.append(Evidence("archivo", "system/core/CodeIgniter.php", "núcleo de CI3 encontrado"))

    if (directorio / "application/config/config.php").exists():
        score["codeigniter3"] += 3
        evidencias.append(Evidence("archivo", "application/config/config.php", "estructura de CI3 encontrada"))

    datos["score"] = score.copy()
    mejor = max(score, key=score.get)

    hay_php = any(
        a.suffix.lower() == ".php" or a.name.lower().endswith(".blade.php")
        for a in archivos
    )

    if score[mejor] == 0:
        datos["framework"] = "php_puro" if hay_php else None
        return DetectionResult(
            nombre="framework_php",
            detectado=hay_php,
            confianza="media" if hay_php else "baja",
            datos=datos,
            evidencias=evidencias,
        )

    if mejor == "laravel":
        datos["framework"] = "laravel"
        datos["version_instalada"] = (
            extraer_version_laravel_desde_lock(directorio)
            or extraer_version_laravel_desde_vendor(directorio)
        )
    elif mejor == "codeigniter3":
        datos["framework"] = "codeigniter3"
        datos["version_instalada"] = extraer_version_codeigniter(directorio)
    elif mejor == "codeigniter4":
        datos["framework"] = "codeigniter4"
        datos["version_instalada"] = extraer_version_codeigniter(directorio)

    confianza = "alta" if score[mejor] >= 5 else "media"

    return DetectionResult(
        nombre="framework_php",
        detectado=True,
        confianza=confianza,
        datos=datos,
        evidencias=evidencias,
    )