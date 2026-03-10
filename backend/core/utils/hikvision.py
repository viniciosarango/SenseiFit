import requests
from requests.auth import HTTPDigestAuth
import logging
from django.conf import settings


# Extraemos la configuración del diccionario que pusiste en settings.py
_config = settings.HIKVISION_CONFIG
HIK_USER = _config.get('USER')
HIK_PASS = _config.get('PASS')
HIK_TIMEOUT = _config.get('TIMEOUT', 10)


# Configuración de la lectora (Luego los moveremos a settings.py)
HIK_URL = f"http://{_config.get('IP')}/ISAPI/AccessControl/UserInfo/Modify?format=json"

logger = logging.getLogger(__name__)

def sync_hikvision_async(membership):

    if not membership.start_date or not membership.end_date:
        return False, "Membresía sin fechas, no se sincroniza aún"
    
    client = membership.client
    
    full_name = f"{client.first_name} {client.last_name}"[:32] # Límite de la lectora
    employee_no = str(client.hikvision_id)

    client_email = getattr(client, 'email', '') or ''
    client_phone = getattr(client, 'phone', '') or ''
    
    # Formateo de fechas a ISO8601 (YYYY-MM-DDT00:00:00)
    begin_time = f"{membership.start_date.isoformat()}T00:00:00"
    end_time = f"{membership.end_date.isoformat()}T23:59:59"

    payload = {
        "UserInfo": {
            "employeeNo": employee_no,
            "name": full_name,
            "userType": "normal",
            "email": client_email,      
            "phoneNumber": client_phone,
            "Valid": {
                "enable": True,
                "beginTime": begin_time,
                "endTime": end_time,
                "timeType": "local"
            }
        }
    }

    try:

        print("HIK_SYNC_START", flush=True)
        print(f"HIK_EMPLOYEE_NO={employee_no}", flush=True)
        print(f"HIK_BEGIN={begin_time}", flush=True)
        print(f"HIK_END={end_time}", flush=True)
        print(f"HIK_PAYLOAD={payload}", flush=True)

        response = requests.put(
            HIK_URL, 
            json=payload, 
            auth=HTTPDigestAuth(HIK_USER, HIK_PASS), 
            timeout=HIK_TIMEOUT
        )

        print(f"HIK_STATUS={response.status_code}", flush=True)
        print(f"HIK_RESPONSE={response.text}", flush=True)
        
        if response.status_code == 200:
            result = response.json()
            # statusCode 1 significa éxito total en Hikvision
            if result.get("statusCode") == 1:
                return True, "Sincronización exitosa"
            return False, f"Error Hik: {result.get('statusString')}"
        
        return False, f"Error de red: {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "La lectora tardó demasiado en responder (Timeout). Verifique si está saturada."
    
    except requests.exceptions.ConnectionError:
        return False, "No hay conexión con la lectora. ¿Está encendida y conectada al router?"
    
    except requests.exceptions.RequestException as e:
        return False, f"Error de red: {str(e)}"
    
    except Exception as e:
        return False, f"Error inesperado en el sistema: {str(e)}"
    

def revoke_hikvision_access(membership):
    """
    Cierra inmediatamente el acceso del cliente en Hikvision
    al cancelar una membresía.
    """
    client = membership.client

    employee_no = str(client.hikvision_id)

    payload = {
        "UserInfo": {
            "employeeNo": employee_no,
            "name": f"{client.first_name} {client.last_name}"[:32],
            "userType": "normal",
            "email": getattr(client, "email", "") or "",
            "phoneNumber": getattr(client, "phone", "") or "",
            "Valid": {
                "enable": True,
                "beginTime": "2020-01-01T00:00:00",
                "endTime": "2020-01-01T23:59:59",
                "timeType": "local"
            }
        }
    }

    try:
        print("HIK_REVOKE_START", flush=True)
        print(f"HIK_REVOKE_EMPLOYEE_NO={employee_no}", flush=True)
        print(f"HIK_REVOKE_PAYLOAD={payload}", flush=True)        

        response = requests.put(
            HIK_URL,
            json=payload,
            auth=HTTPDigestAuth(HIK_USER, HIK_PASS),
            timeout=HIK_TIMEOUT
        )

        print(f"HIK_REVOKE_STATUS={response.status_code}", flush=True)
        print(f"HIK_REVOKE_RESPONSE={response.text}", flush=True)

        if response.status_code == 200:
            return True, "Acceso revocado en Hikvision"
        return False, f"Error Hikvision: {response.status_code}"

    except Exception as e:
        return False, f"Error al revocar acceso: {str(e)}"
