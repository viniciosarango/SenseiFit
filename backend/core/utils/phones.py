import re

def normalize_ec_phone(value: str) -> str:
    """
    Acepta: +593991122310 | 593991122310 | 0991122310 | 991122310
    Devuelve: +593991122310 (E.164 EC) o "" si no se puede.
    """
    if not value:
        return ""

    s = str(value).strip()
    s = s.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    s = s.replace("+", "")

    # solo dígitos
    if not re.fullmatch(r"\d+", s):
        return ""

    # 099xxxxxxx -> 59399xxxxxxx
    if s.startswith("0") and len(s) == 10:
        s = "593" + s[1:]

    # 593xxxxxxxxx
    if s.startswith("593") and len(s) == 12:
        return "+" + s

    # 9 dígitos (sin 0) -> asumimos móvil EC (99xxxxxxx)
    if len(s) == 9:
        return "+593" + s

    return ""