#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

from .contador import generar_resultado_contado, imprimir_resultados_contado
from .inspector import inspeccionar_proyecto


COMANDOS = {"count", "inspect"}


def validar_directorio(ruta: str) -> Path:
    carpeta = Path(ruta)

    if not carpeta.exists():
        print("Error: la carpeta '{}' no existe.".format(carpeta), file=sys.stderr)
        sys.exit(1)

    if not carpeta.is_dir():
        print("Error: '{}' no es un directorio.".format(carpeta), file=sys.stderr)
        sys.exit(1)

    return carpeta


def imprimir_bloque(nombre: str, data: dict) -> None:
    print("\n{}".format(nombre))
    print("-" * len(nombre))
    print("Detectado : {}".format("Sí" if data["detectado"] else "No"))
    print("Confianza : {}".format(data["confianza"]))

    if data["datos"]:
        print("Datos:")
        for clave, valor in data["datos"].items():
            print("  - {}: {}".format(clave, valor))

    if data["evidencias"]:
        print("Evidencias:")
        for evidencia in data["evidencias"][:10]:
            archivo = evidencia["archivo"] or "-"
            print("  - [{}] {}: {}".format(
                evidencia["tipo"],
                archivo,
                evidencia["detalle"],
            ))


def comando_count(carpeta: Path, as_json: bool = False) -> None:
    resultado = generar_resultado_contado(carpeta)

    if as_json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return

    imprimir_resultados_contado(resultado)


def comando_inspect(carpeta: Path, as_json: bool = False) -> None:
    resultado = inspeccionar_proyecto(carpeta)

    if as_json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return

    print("=" * 72)
    print("Proyecto           : {}".format(resultado["proyecto"]))
    print("Archivos analizados: {}".format(resultado["archivos_analizados"]))
    print("=" * 72)

    for nombre, data in resultado["detectores"].items():
        imprimir_bloque(nombre, data)

    print("\n" + "=" * 72)


def comando_all(carpeta: Path, as_json: bool = False) -> None:
    resultado_count = generar_resultado_contado(carpeta)
    resultado_inspect = inspeccionar_proyecto(carpeta)

    if as_json:
        print(json.dumps(
            {
                "count": resultado_count,
                "inspect": resultado_inspect,
            },
            ensure_ascii=False,
            indent=2,
        ))
        return

    imprimir_resultados_contado(resultado_count)

    print("\n")
    print("#" * 72)

    print("=" * 72)
    print("Proyecto           : {}".format(resultado_inspect["proyecto"]))
    print("Archivos analizados: {}".format(resultado_inspect["archivos_analizados"]))
    print("=" * 72)

    for nombre, data in resultado_inspect["detectores"].items():
        imprimir_bloque(nombre, data)

    print("\n" + "=" * 72)


def main() -> None:
    argv = sys.argv[1:]

    if argv and argv[0] not in COMANDOS and not argv[0].startswith("-"):
        parser = argparse.ArgumentParser(
            description="Cuenta archivos e inspecciona proyectos."
        )
        parser.add_argument("carpeta", help="Ruta del proyecto")
        parser.add_argument("--json", action="store_true", help="Salida en JSON")
        args = parser.parse_args(argv)

        carpeta = validar_directorio(args.carpeta)
        comando_all(carpeta, as_json=args.json)
        return

    parser = argparse.ArgumentParser(
        description="Herramienta para contar archivos e inspeccionar proyectos."
    )
    subparsers = parser.add_subparsers(dest="comando")

    parser_count = subparsers.add_parser(
        "count",
        help="Cuenta archivos válidos por extensión",
    )
    parser_count.add_argument("carpeta", help="Ruta del proyecto")
    parser_count.add_argument("--json", action="store_true", help="Salida en JSON")

    parser_inspect = subparsers.add_parser(
        "inspect",
        help="Detecta stack, framework, Kendo y dependencias del servidor",
    )
    parser_inspect.add_argument("carpeta", help="Ruta del proyecto")
    parser_inspect.add_argument("--json", action="store_true", help="Salida en JSON")

    args = parser.parse_args(argv)

    if args.comando == "count":
        carpeta = validar_directorio(args.carpeta)
        comando_count(carpeta, as_json=args.json)
        return

    if args.comando == "inspect":
        carpeta = validar_directorio(args.carpeta)
        comando_inspect(carpeta, as_json=args.json)
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()