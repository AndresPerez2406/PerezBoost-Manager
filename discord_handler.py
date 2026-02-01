import requests
from datetime import datetime
import threading

COLOR_SUCCESS = 5763719   # Verde
COLOR_INFO = 3447003      # Azul
COLOR_WARNING = 16776960  # Amarillo
COLOR_DANGER = 15158332   # Rojo

class DiscordNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def _enviar_async(self, payload):
        """Envía la petición en un hilo separado para no congelar la GUI."""
        try:
            if not self.webhook_url or self.webhook_url.strip() == "":
                return
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code not in [200, 204]:
                print(f"Discord devolvió error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Error enviando a Discord: {e}")

    def enviar_notificacion(self, titulo, descripcion, color=COLOR_INFO, campos=None):
        """
        Envía un Embed profesional a Discord v9.0.
        :param titulo: Título del mensaje.
        :param descripcion: Texto descriptivo debajo del título.
        :param color: Color lateral del embed.
        :param campos: Lista de dicts [{'name': '...', 'value': '...', 'inline': True}]
        """
        if not self.webhook_url or self.webhook_url.strip() == "": 
            return

        embed = {
            "title": str(titulo),
            "description": str(descripcion),
            "color": color,
            "footer": {
                "text": f"PerezBoost Manager V9.0 • {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                "icon_url": "https://cdn-icons-png.flaticon.com/512/6126/6126343.png"
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        if campos:

            for campo in campos:
                campo['value'] = str(campo.get('value', ''))
                campo['name'] = str(campo.get('name', ''))
            embed["fields"] = campos

        payload = {
            "username": "PerezBoost Bot V9.0",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/6126/6126343.png",
            "embeds": [embed]
        }

        hilo = threading.Thread(target=self._enviar_async, args=(payload,))
        hilo.daemon = True
        hilo.start()