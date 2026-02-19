import requests
import re
import time
from django.core.management.base import BaseCommand
from requests.auth import HTTPDigestAuth
from core.models import Client, Attendance

class Command(BaseCommand):
    def handle(self, *args, **options):
        url = "http://192.168.1.26/ISAPI/Event/notification/alertStream"
        auth = HTTPDigestAuth('admin', 'TU_PASSWORD')

        print("Escuchando eventos de la lectora...")

        while True:
            try:
                response = requests.get(url, auth=auth, stream=True, timeout=None)
                for line in response.iter_lines():
                    if line:
                        decoded = line.decode('utf-8', errors='ignore')
                        
                        # FILTRO TÉCNICO: Solo procesar si la fecha es de HOY
                        if '"employeeNoString":"8"' in decoded or '"employeeNoString":"00000008"' in decoded:
                            print("\n🎯 CAPTURADO ID 8")
                            print(f"RAW DATA: {decoded}") # Esto nos dirá la FECHA y el TIPO de evento
                            self.registrar_y_mostrar("8")
                            
            except Exception as e:
                print(f"Error de conexión: {e}. Reintentando en 5 segundos...")
                time.sleep(5)

    def registrar_asistencia(self, client_id):
        try:
            # Busca al cliente por el ID obtenido de la lectora
            cliente = Client.objects.get(id=client_id)
            
            # Crea el registro en la tabla Attendance
            Attendance.objects.create(client=cliente)
            
            print(f"ASISTENCIA REGISTRADA: Cliente ID {client_id} - {cliente.first_name}")
        except Client.DoesNotExist:
            print(f"ERROR: El ID {client_id} no existe en la base de datos.")
        except Exception as e:
            print(f"ERROR al registrar: {e}")