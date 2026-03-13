import json
import re
import time
import requests

from django.conf import settings
from django.core.management.base import BaseCommand
from requests.auth import HTTPDigestAuth


class Command(BaseCommand):
    help = "Escucha eventos de Hikvision y los reenvía al webhook de SenseiFit"

    def handle(self, *args, **options):
        hik = settings.HIKVISION_CONFIG

        hik_ip = hik.get("IP")
        hik_user = hik.get("USER")
        hik_pass = hik.get("PASS")
        hik_timeout = hik.get("TIMEOUT", 10)

        forward_url = getattr(settings, "ATTENDANCE_FORWARD_URL", "")
        webhook_key = getattr(settings, "ATTENDANCE_WEBHOOK_KEY", "")

        if not hik_ip or not hik_user or not hik_pass:
            self.stdout.write(self.style.ERROR("Falta configurar HIKVISION_CONFIG"))
            return

        if not forward_url:
            self.stdout.write(self.style.ERROR("Falta ATTENDANCE_FORWARD_URL en settings"))
            return

        if not webhook_key:
            self.stdout.write(self.style.ERROR("Falta ATTENDANCE_WEBHOOK_KEY en settings"))
            return

        stream_url = f"http://{hik_ip}/ISAPI/Event/notification/alertStream"

        self.stdout.write(self.style.SUCCESS("Escuchando eventos de la lectora..."))
        self.stdout.write(f"HIK Stream: {stream_url}")
        self.stdout.write(f"Forward URL: {forward_url}")

        recent_events = {}
        dedupe_seconds = 8

        while True:
            try:
                response = requests.get(
                    stream_url,
                    auth=HTTPDigestAuth(hik_user, hik_pass),
                    stream=True,
                    timeout=None,
                )
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line:
                        continue

                    decoded = line.decode("utf-8", errors="ignore")

                    if "employeeNoString" not in decoded:
                        continue

                    # if "11511263" not in decoded:
                    #     continue

                    payload = self._build_payload(decoded)
                    if not payload:
                        continue

                    hikvision_id = payload.get("hikvision_id")
                    now_ts = time.time()

                    last_seen = recent_events.get(hikvision_id)
                    if last_seen and (now_ts - last_seen) < dedupe_seconds:
                        continue

                    recent_events[hikvision_id] = now_ts

                    self.stdout.write(f"Evento detectado: {payload}")

                    try:
                        forward_response = requests.post(
                            forward_url,
                            json=payload,
                            headers={
                                "Content-Type": "application/json",
                                "X-API-KEY": webhook_key,
                            },
                            timeout=hik_timeout,
                        )

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Reenviado -> {forward_response.status_code} {forward_response.text}"
                            )
                        )
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error reenviando al webhook: {e}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error de conexión al stream Hikvision: {e}"))
                self.stdout.write("Reintentando en 5 segundos...")
                time.sleep(5)

    def _build_payload(self, decoded: str):
        employee_match = re.search(r'"employeeNoString"\s*:\s*"([^"]+)"', decoded)
        if not employee_match:
            return None

        hikvision_id = employee_match.group(1).strip()

        event_time_match = re.search(r'"dateTime"\s*:\s*"([^"]+)"', decoded)
        occurred_at = event_time_match.group(1).strip() if event_time_match else time.strftime("%Y-%m-%dT%H:%M:%S")

        major_match = re.search(r'"major"\s*:\s*(\d+)', decoded)
        minor_match = re.search(r'"minor"\s*:\s*(\d+)', decoded)

        major = major_match.group(1) if major_match else ""
        minor = minor_match.group(1) if minor_match else ""

        return {
            "hikvision_id": hikvision_id,
            "method": "FINGERPRINT",
            "source": "hikvision_listener",
            "device_id": "HIKVISION-STREAM",
            "device_name": "Lector Hikvision",
            "occurred_at": occurred_at,
            "direction": "ENTRY",
            "event_type": f"MAJOR_{major}_MINOR_{minor}" if major or minor else "ACCESS",
            "raw_event": decoded,
        }