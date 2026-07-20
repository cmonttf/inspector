from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, Any, Tuple
import subprocess

from .utils import obtener_archivos, obtener_extension


EXTENSIONES_VALIDAS = {
    ".php",
    ".blade.php",
    ".html",
    ".htm",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".vue",
    ".py",
    ".java",
    ".kt",
    ".kts",
    ".cs",
    ".vb",
    ".go",
    ".rs",
    ".rb",
    ".swift",
    ".c",
    ".cpp",
    ".cc",
    ".cxx",
    ".h",
    ".hpp",
    ".sql",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".ini",
    ".conf",
    ".toml",
    ".env",
    ".gitignore",
    ".gitattributes",
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".bat",
    ".md",
    ".txt",
    ".rst",
}


def debe_excluirse(archivo: Path) -> bool:
    """
    Determina si un archivo debe excluirse del conteo porque es:
    - Librería de terceros
    - Archivo minificado/compilado
    - Asset generado automáticamente
    - Tests o archivos de prueba
    """
    ruta_relativa = str(archivo).lower()
    nombre = archivo.name.lower()
    
    # Patrones de exclusión: archivos minificados y librerías de terceros
    patrones_excluir = [
        # Minificados y compilados
        ".min.js", ".min.css", ".min.map", ".min.html",
        ".pack.js", ".pack.css", ".full.js",
        
        # Vendor y librerías principales
        "node_modules/", "vendor/", "/vendor/", "bower_components/",
        "jquery-easyui/", "jquery-ui/", "bootstrap/", "semantic/",
        "assets/jquery", "assets/bootstrap", "assets/semantic",
        "lib/jquery", "lib/bootstrap", "lib/semantic",
        
        # Librerías específicas versionadas
        "media_1/",  # DataTables src
        "datatables",
        "flexigrid",
        "jsdatepick",
        "kendo",
        
        # Tests y Specs
        "/test/", "/tests/", "/spec/", "/specs/",
        "/testing/", "/unit_testing/",
        "test_", "tests_",
        ".test.js", ".spec.js", ".test.css", ".spec.css",
        
        # Compilados/Generados
        "/dist/", "/build/", "/out/", "/.next/", "/.nuxt/",
        "/coverage/", "/.coverage",
        
        # Maps y sourcemaps
        ".map.js", ".map.css",
    ]
    
    for patron in patrones_excluir:
        if patron in ruta_relativa:
            return True
    
    # Excluir archivos de mapas
    if nombre.endswith(".map"):
        return True
    
    return False


def es_archivo_texto(archivo: Path) -> bool:
    """Verifica si un archivo es de texto usando el comando 'file'."""
    try:
        resultado = subprocess.run(
            ["file", "--mime-type", str(archivo)],
            capture_output=True,
            text=True,
            timeout=1,
        )
        mime_type = resultado.stdout.split(": ")[1].strip() if ": " in resultado.stdout else ""
        return mime_type.startswith("text/") or mime_type in {"application/json", "application/xml"}
    except Exception:
        # Si hay error al verificar, asumir que es texto si la extensión es válida
        return True


def contar_archivos(directorio: Path) -> Tuple[int, Counter]:
    extensiones = Counter()
    total = 0

    for archivo in obtener_archivos(directorio):
        # Excluir archivos que son librerías o compilados
        if debe_excluirse(archivo):
            continue
        
        extension = obtener_extension(archivo)

        if extension not in EXTENSIONES_VALIDAS:
            continue

        # Validar que sea archivo de texto
        if not es_archivo_texto(archivo):
            continue

        total += 1
        extensiones[extension] += 1

    return total, extensiones


def generar_resultado_contado(directorio: Path) -> Dict[str, Any]:
    total, extensiones = contar_archivos(directorio)

    detalle = []
    for ext, cantidad in sorted(extensiones.items(), key=lambda x: (-x[1], x[0])):
        porcentaje = cantidad * 100 / total if total else 0
        detalle.append(
            {
                "extension": ext,
                "cantidad": cantidad,
                "porcentaje": round(porcentaje, 2),
            }
        )

    return {
        "proyecto": str(directorio.resolve()),
        "total_archivos": total,
        "extensiones": detalle,
    }


def imprimir_resultados_contado(resultado: Dict[str, Any]) -> None:
    print("=" * 65)
    print("Proyecto :", resultado["proyecto"])
    print("=" * 65)

    total = resultado["total_archivos"]
    extensiones = resultado["extensiones"]

    if total == 0:
        print("\nNo se encontraron archivos válidos.")
        return

    ancho = max(len(item["extension"]) for item in extensiones)

    print("\nArchivos por extensión\n")

    for item in extensiones:
        print(
            "{:<{}} : {:>6} archivos ({:6.2f}%)".format(
                item["extension"],
                ancho,
                item["cantidad"],
                item["porcentaje"],
            )
        )

    print("\n" + "-" * 65)
    print("TOTAL DE ARCHIVOS :", total)
    print("=" * 65)