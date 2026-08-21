import os
from typing import Optional, List, Dict, Any
import requests

class PerezBoostApiClient:
    """
    Cliente HTTP SDK para consumir la API REST centralizada de PerezBoost Pro.
    Permite a la aplicación Desktop, portal web y scripts interactuar con el Backend.
    """
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.current_user: Optional[Dict[str, Any]] = None

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    # =========================================================================
    # 1. AUTENTICACIÓN
    # =========================================================================
    def login(self, username: str, password: str) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/login"
        resp = self.session.post(url, json={"username": username, "password": password}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        self.token = data.get("access_token")
        self.current_user = {"name": data.get("name"), "role": data.get("role")}
        return data

    def get_me(self) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/me"
        resp = self.session.get(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        self.current_user = resp.json()
        return self.current_user

    # =========================================================================
    # 2. PEDIDOS
    # =========================================================================
    def obtener_pedidos(self, estado: Optional[str] = None, booster: Optional[str] = None, mes: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/pedidos"
        params = {}
        if estado: params["estado"] = estado
        if booster: params["booster"] = booster
        if mes: params["mes"] = mes
        resp = self.session.get(url, headers=self._get_headers(), params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def obtener_pedidos_activos(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/pedidos/activos"
        resp = self.session.get(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def obtener_pedido(self, id_pedido: int) -> Dict[str, Any]:
        url = f"{self.base_url}/pedidos/{id_pedido}"
        resp = self.session.get(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def crear_pedido(self, booster_id: Optional[int], booster_nombre: str, id_cuenta: int, user_pass: str, elo_inicial: str, fecha_limite: str) -> Dict[str, Any]:
        url = f"{self.base_url}/pedidos"
        payload = {
            "booster_id": booster_id,
            "booster_nombre": booster_nombre,
            "id_cuenta": id_cuenta,
            "user_pass": user_pass,
            "elo_inicial": elo_inicial,
            "fecha_limite": str(fecha_limite)
        }
        resp = self.session.post(url, headers=self._get_headers(), json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def finalizar_pedido(self, id_pedido: int, elo_final: str, wr: float, pago_cliente: float, pago_booster: float, ajuste_valor: float = 0.0, bote_pedido: float = 0.0, bote_wr: float = 0.0, cuenta_ranking: int = 1) -> Dict[str, Any]:
        url = f"{self.base_url}/pedidos/{id_pedido}/finalizar"
        payload = {
            "elo_final": elo_final,
            "wr": wr,
            "pago_cliente": pago_cliente,
            "pago_booster": pago_booster,
            "ajuste_valor": ajuste_valor,
            "bote_pedido": bote_pedido,
            "bote_wr": bote_wr,
            "cuenta_ranking": cuenta_ranking
        }
        resp = self.session.post(url, headers=self._get_headers(), json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def actualizar_estado_pedido(self, id_pedido: int, datos: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/pedidos/{id_pedido}/estado"
        resp = self.session.patch(url, headers=self._get_headers(), json=datos, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def actualizar_opgg_pedido(self, id_pedido: int, opgg: str) -> Dict[str, Any]:
        url = f"{self.base_url}/pedidos/{id_pedido}/opgg"
        resp = self.session.patch(url, headers=self._get_headers(), json={"opgg": opgg}, timeout=10)
        resp.raise_for_status()
        return resp.json()

    # =========================================================================
    # 3. INVENTARIO DE CUENTAS
    # =========================================================================
    def obtener_inventario(self, elo: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/inventario"
        params = {"elo": elo} if elo else {}
        resp = self.session.get(url, headers=self._get_headers(), params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def obtener_elos_en_stock(self) -> List[str]:
        url = f"{self.base_url}/inventario/elos"
        resp = self.session.get(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def agregar_cuenta_inventario(self, user_pass: str, elo_tipo: str, descripcion: str = "FRESH") -> Dict[str, Any]:
        url = f"{self.base_url}/inventario"
        payload = {"user_pass": user_pass, "elo_tipo": elo_tipo, "descripcion": descripcion}
        resp = self.session.post(url, headers=self._get_headers(), json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def agregar_lote_inventario(self, cuentas: List[str], elo_tipo: str, descripcion: str = "FRESH") -> Dict[str, Any]:
        url = f"{self.base_url}/inventario/lote"
        payload = {"cuentas": cuentas, "elo_tipo": elo_tipo, "descripcion": descripcion}
        resp = self.session.post(url, headers=self._get_headers(), json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def eliminar_cuenta_inventario(self, id_cuenta: int) -> Dict[str, Any]:
        url = f"{self.base_url}/inventario/{id_cuenta}"
        resp = self.session.delete(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    # =========================================================================
    # 4. BOOSTERS Y STAFF
    # =========================================================================
    def obtener_boosters(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/boosters"
        resp = self.session.get(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def crear_booster(self, nombre: str, binance: str = "", discord_id: str = "", password: str = "1234", en_ranking: int = 1) -> Dict[str, Any]:
        url = f"{self.base_url}/boosters"
        payload = {"nombre": nombre, "binance": binance, "discord_id": discord_id, "password": password, "en_ranking": en_ranking}
        resp = self.session.post(url, headers=self._get_headers(), json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def actualizar_booster(self, id_booster: int, datos: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/boosters/{id_booster}"
        resp = self.session.put(url, headers=self._get_headers(), json=datos, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def toggle_ranking_booster(self, id_booster: int) -> Dict[str, Any]:
        url = f"{self.base_url}/boosters/{id_booster}/toggle-ranking"
        resp = self.session.patch(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def eliminar_booster(self, id_booster: int) -> Dict[str, Any]:
        url = f"{self.base_url}/boosters/{id_booster}"
        resp = self.session.delete(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    # =========================================================================
    # 5. RANKING Y LEADERBOARD
    # =========================================================================
    def obtener_ranking(self, mes: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/ranking"
        params = {"mes": mes} if mes else {}
        resp = self.session.get(url, headers=self._get_headers(), params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    # =========================================================================
    # 6. FINANZAS Y LIQUIDACIONES
    # =========================================================================
    def obtener_resumen_financiero(self, mes: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/finanzas/resumen"
        params = {"mes": mes} if mes else {}
        resp = self.session.get(url, headers=self._get_headers(), params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def obtener_saldos_pendientes(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/finanzas/saldos-pendientes"
        resp = self.session.get(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def liquidar_booster(self, booster_nombre: str) -> Dict[str, Any]:
        url = f"{self.base_url}/finanzas/liquidar/{booster_nombre}"
        resp = self.session.post(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    # =========================================================================
    # 7. TARIFAS DE PRECIOS
    # =========================================================================
    def obtener_tarifas(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/tarifas"
        resp = self.session.get(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def crear_tarifa(self, division: str, precio_cliente: float, margen_perez: float, puntos: int = 2) -> Dict[str, Any]:
        url = f"{self.base_url}/tarifas"
        payload = {"division": division, "precio_cliente": precio_cliente, "margen_perez": margen_perez, "puntos": puntos}
        resp = self.session.post(url, headers=self._get_headers(), json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def actualizar_tarifa(self, division: str, precio_cliente: Optional[float] = None, margen_perez: Optional[float] = None, puntos: Optional[int] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/tarifas/{division}"
        payload = {}
        if precio_cliente is not None: payload["precio_cliente"] = precio_cliente
        if margen_perez is not None: payload["margen_perez"] = margen_perez
        if puntos is not None: payload["puntos"] = puntos
        resp = self.session.put(url, headers=self._get_headers(), json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def eliminar_tarifa(self, division: str) -> Dict[str, Any]:
        url = f"{self.base_url}/tarifas/{division}"
        resp = self.session.delete(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    # =========================================================================
    # 8. WALLET BINANCE
    # =========================================================================
    def obtener_balance_wallet(self) -> Dict[str, Any]:
        url = f"{self.base_url}/wallet/balance"
        resp = self.session.get(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def obtener_transacciones_wallet(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/wallet/transacciones"
        resp = self.session.get(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def registrar_transaccion_wallet(self, tipo: str, categoria: str, monto: float, descripcion: str = "") -> Dict[str, Any]:
        url = f"{self.base_url}/wallet/transacciones"
        payload = {"tipo": tipo, "categoria": categoria, "monto": monto, "descripcion": descripcion}
        resp = self.session.post(url, headers=self._get_headers(), json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def eliminar_transaccion_wallet(self, id_transaccion: int) -> Dict[str, Any]:
        url = f"{self.base_url}/wallet/transacciones/{id_transaccion}"
        resp = self.session.delete(url, headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

# Instancia singleton lista para usar en la aplicación
api_client = PerezBoostApiClient()
