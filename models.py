from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class Evidence:
    tipo: str
    archivo: Optional[str]
    detalle: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DetectionResult:
    nombre: str
    detectado: bool
    confianza: str = "baja"
    datos: Dict[str, Any] = field(default_factory=dict)
    evidencias: List[Evidence] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nombre": self.nombre,
            "detectado": self.detectado,
            "confianza": self.confianza,
            "datos": self.datos,
            "evidencias": [e.to_dict() for e in self.evidencias],
        }