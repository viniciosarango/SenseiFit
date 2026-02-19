import requests
from requests.auth import HTTPDigestAuth

# CONFIGURACIÓN (Cámbialo por los datos de tu gym)
IP_LECTOR = "192.168.1.100"  # La IP que tenga el lector en tu red
USER = "admin"               # Usuario del lector
PASS = "TuContraseña"        # Contraseña del lector

def probar_conexion():
    # Este endpoint nos devuelve la info del modelo y versión
    url = f"http://{IP_LECTOR}/ISAPI/System/deviceInfo"
    
    try:
        print(f"Intentando conectar a {IP_LECTOR}...")
        
        # Hikvision usa autenticación Digest (es más segura que la básica)
        response = requests.get(
            url, 
            auth=HTTPDigestAuth(USER, PASS), 
            timeout=5
        )
        
        if response.status_code == 200:
            print("¡ÉXITO! El lector respondió correctamente.")
            print("Datos del dispositivo:")
            print(response.text) # Verás un XML con el modelo y serie
        else:
            print(f"Error: El lector respondió con código {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: No se pudo encontrar el lector. ¿Están en la misma red?")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    probar_conexion()