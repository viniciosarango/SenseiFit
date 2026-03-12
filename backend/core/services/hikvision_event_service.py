import hashlib
import json
from typing import Any, Dict, Optional


def build_hikvision_event_fingerprint(
    *,
    hikvision_person_id: Optional[str] = None,
    device_id: Optional[str] = None,
    occurred_at: Optional[str] = None,
    direction: Optional[str] = None,
    event_type: Optional[str] = None,
    raw_payload: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Genera un fingerprint estable para un evento de acceso Hikvision.

    Prioridad:
    1. Si existe un external event id real en el futuro, podremos usarlo aparte.
    2. Mientras tanto, construimos una huella reproducible con campos clave.
    3. Si faltan campos, usamos también el payload serializado.
    """

    normalized_payload = json.dumps(
        raw_payload or {},
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )

    base_parts = [
        (hikvision_person_id or "").strip(),
        (device_id or "").strip(),
        (occurred_at or "").strip(),
        (direction or "").strip().upper(),
        (event_type or "").strip().upper(),
        normalized_payload,
    ]

    base_string = "|".join(base_parts)

    return hashlib.sha256(base_string.encode("utf-8")).hexdigest()