from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import json
import re
import subprocess


def obtener_extension(archivo: Path) -> str:
    nombre = archivo.name.lower()

    especiales = [
        ".blade.php",
        ".d.ts",
        ".test.js",
        ".spec.js",
        ".test.ts",
        ".spec.ts",
        ".module.css",
        ".module.scss",
    ]

    for ext in especiales:
        if nombre.endswith(ext):
            return ext

    if nombre == ".env" or nombre.startswith(".env."):
        return ".env"

    if nombre in {".gitignore", ".gitattributes"}:
        return nombre

    return archivo.suffix.lower()


def obtener_archivos(directorio: Path) -> List[Path]:
    if (directorio / ".git").exists():
        try:
            resultado = subprocess.run(
                [
                    "git",
                    "-C",
                    str(directorio),
                    "ls-files",
                    "--cached",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            archivos = [
                directorio / archivo
                for archivo in resultado.stdout.splitlines()
                if (directorio / archivo).is_file()
            ]
            
            # Remover duplicados manteniendo el orden
            vistos = set()
            resultado_unico = []
            for archivo in archivos:
                path_str = str(archivo)
                if path_str not in vistos:
                    vistos.add(path_str)
                    resultado_unico.append(archivo)
            
            return resultado_unico
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    return [f for f in directorio.rglob("*") if f.is_file()]


def leer_texto(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def leer_json(path: Path) -> Optional[Union[Dict[str, Any], List[Any]]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def relativizar(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except Exception:
        return str(path)


def buscar_regex_en_archivos(
    archivos: List[Path],
    directorio_base: Path,
    patrones: List[tuple],
    extensiones_permitidas: Optional[set] = None,
    max_resultados_por_patron: int = 20,
) -> List[Dict[str, Any]]:
    hallazgos = []

    for archivo in archivos:
        ext = obtener_extension(archivo)
        if extensiones_permitidas and ext not in extensiones_permitidas:
            continue

        texto = leer_texto(archivo)
        if not texto:
            continue

        for nombre_patron, patron in patrones:
            coincidencias = list(re.finditer(patron, texto, re.IGNORECASE | re.MULTILINE))
            for match in coincidencias[:max_resultados_por_patron]:
                linea = texto.count("\n", 0, match.start()) + 1
                snippet = texto[max(0, match.start() - 80): match.end() + 80].replace("\n", " ")
                hallazgos.append(
                    {
                        "patron": nombre_patron,
                        "archivo": relativizar(archivo, directorio_base),
                        "linea": linea,
                        "texto": snippet.strip(),
                    }
                )

    return hallazgos