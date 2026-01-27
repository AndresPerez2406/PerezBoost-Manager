import requests
from datetime import datetime
import threading

COLOR_SUCCESS = 5763719 
COLOR_INFO = 3447003   
COLOR_WARNING = 16776960 
COLOR_DANGER = 15158332  

class DiscordNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def _enviar_async(self, payload):
        """Envía la petición en un hilo separado para no congelar la GUI."""
        try:
            if not self.webhook_url: return
            requests.post(self.webhook_url, json=payload)
        except Exception as e:
            print(f"Error enviando a Discord: {e}")

    def enviar_notificacion(self, titulo, descripcion, color=COLOR_INFO, campos=None):
        """
        Envía un Embed bonito a Discord.
        :param campos: Lista de dicts [{'name': '...', 'value': '...', 'inline': True}]
        """
        if not self.webhook_url: return

        embed = {
            "title": titulo,
            "description": descripcion,
            "color": color,
            "footer": {
                "text": f"PerezBoost Manager V8.5 • {datetime.now().strftime('%H:%M')}"
            }
        }

        if campos:
            embed["fields"] = campos

        payload = {
            "username": "PerezBoost Bot",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/6126/6126343.png",
            "embeds": [embed]
        }

        hilo = threading.Thread(target=self._enviar_async, args=(payload,))
        hilo.start()