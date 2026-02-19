import requests
from requests.auth import HTTPDigestAuth

# Datos confirmados
url = "http://192.168.1.26/ISAPI/AccessControl/UserInfo/Modify?format=json"
auth = HTTPDigestAuth("admin", "Hik98765")

# Datos de Maria Lara
# Queremos que entre hasta el 1 de Junio de 2026
payload = {
    "UserInfo": {
        "employeeNo": "11510184",
        "Valid": {
            "enable": True,
            "beginTime": "2026-01-01T00:00:00",
            "endTime": "2026-06-01T23:59:59"
        }
    }
}

r = requests.put(url, json=payload, auth=auth, timeout=10)

print(f"Estado: {r.status_code}")
print(f"Respuesta: {r.text}")