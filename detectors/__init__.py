from .php_detector import detectar_php_puro
from .framework_detector import detectar_framework_php
from .kendo_detector import detectar_kendo
from .server_dependencies_detector import detectar_dependencias_servidor
from .oci_deprecated_detector import detectar_oci_deprecado

__all__ = [
    "detectar_php_puro",
    "detectar_framework_php",
    "detectar_kendo",
    "detectar_dependencias_servidor",
    "detectar_oci_deprecado",
]