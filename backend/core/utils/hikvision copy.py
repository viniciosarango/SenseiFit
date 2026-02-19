import requests
from requests.auth import HTTPDigestAuth
import json

# Configuración confirmada de Dorians Gym
HIK_CONFIG = {
    "IP": "192.168.1.26",
    "USER": "admin",
    "PASS": "Hik98765", # La clave que acabas de validar
}

def sync_client_expiration(external_id, end_date):
    """
    Envía la fecha de vencimiento al lector Hikvision usando JSON.
    """
    # Formateamos la fecha: 2026-06-01T23:59:59
    expiry_str = f"{end_date.strftime('%Y-%m-%d')}T23:59:59"
    
    url = f"http://{HIK_CONFIG['IP']}/ISAPI/AccessControl/UserInfo/Modify?format=json"
    
    payload = {
        "UserInfo": {
            "employeeNo": str(external_id),
            "Valid": {
                "enable": True,
                "beginTime": "2026-01-01T00:00:00",
                "endTime": expiry_str
            }
        }
    }

    try:
        response = requests.put(
            url,
            auth=HTTPDigestAuth(HIK_CONFIG['USER'], HIK_CONFIG['PASS']),
            json=payload,
            timeout=10
        )
        
        # Si el lector devuelve statusCode 1, es un éxito total
        if response.status_code == 200:
            return True, "Sincronización exitosa"
        else:
            return False, f"Error del lector: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, f"Error de conexión: {str(e)}"