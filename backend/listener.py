import requests

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

class HikvisionHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        raw_body = self.rfile.read(content_length).decode(errors="ignore")

        # 1. Buscar el JSON dentro del multipart
        start = raw_body.find('{')
        end = raw_body.rfind('}') + 1

        if start == -1 or end == -1:
            self._ok()
            return

        try:
            data = json.loads(raw_body[start:end])
        except Exception:
            self._ok()
            return

        event = data.get("AccessControllerEvent", {})
        sub_event = event.get("subEventType")

        # 2. FILTRO CLAVE
        if sub_event != 38:
            # Ruido: ignoramos
            self._ok()
            return

        # 3. Evento válido
        employee_no = event.get("employeeNoString")

        print("\n🎯 EVENTO DE ASISTENCIA DETECTADO")
        print(f"Client ID (employeeNoString): {employee_no}")

        payload = {
            "hikvision_id": employee_no,
            "method": "FINGERPRINT",
            "source": "hikvision",
        }

        try:
            response = requests.post(
                "http://127.0.0.1:8000/attendance/webhook/",
                json=payload,
                timeout=3,
            )
            print(f"➡️ Enviado a Django | Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Error enviando a Django: {e}")

        print("================================\n")
        self._ok()


    def _ok(self):
        self.send_response(200)
        self.end_headers()


def run():
    server = HTTPServer(("0.0.0.0", 9000), HikvisionHandler)
    print("🎧 Listener Hikvision activo (filtrando subEventType=38)")
    server.serve_forever()


if __name__ == "__main__":
    run()
