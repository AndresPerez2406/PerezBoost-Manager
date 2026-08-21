import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

from core.api_client import api_client

def mostrar_menu():
    print("\n" + "="*60)
    print("🚀 PEREZBOOST PRO — PANEL DE PRUEBAS DE LA FASE 2 (API CLIENT)")
    print("="*60)
    print("1. 🔐 Iniciar Sesión (Login JWT como Admin)")
    print("2. 🎮 Ver Pedidos Activos (En progreso)")
    print("3. 📦 Ver Inventario de Cuentas en Stock")
    print("4. 🏆 Ver Leaderboard / Ranking del Mes")
    print("5. 📊 Ver Resumen Financiero (Mi Neto / Ventas)")
    print("6. 💰 Ver Balance de Billetera Binance")
    print("7. 👥 Ver Lista de Boosters / Staff")
    print("0. 🚪 Salir")
    print("="*60)

def main():
    print("Iniciando conexión con el Backend API...")
    try:
        # Login automático inicial
        api_client.login("admin", "1234")
        print("✅ Conectado y autenticado como: Administrador (Token JWT activo)")
    except Exception as e:
        print(f"⚠️ Error conectando al backend en http://127.0.0.1:8000: {e}")
        print("Asegúrate de que el backend esté corriendo con: python run_api.py")
        return

    while True:
        mostrar_menu()
        opcion = input("👉 Selecciona una opción (0-7): ").strip()
        
        if opcion == "1":
            u = input("Usuario [admin]: ").strip() or "admin"
            p = input("Contraseña [1234]: ").strip() or "1234"
            try:
                res = api_client.login(u, p)
                print(f"\n✅ Login Exitoso! Usuario: {res['name']} | Rol: {res['role']}")
                print(f"🔑 Token JWT: {api_client.token[:30]}...")
            except Exception as e:
                print(f"\n❌ Error en login: {e}")

        elif opcion == "2":
            try:
                activos = api_client.obtener_pedidos_activos()
                print(f"\n🎮 PEDIDOS ACTIVOS EN CURSO ({len(activos)}):")
                print("-" * 75)
                for p in activos:
                    print(f"• ID #{p['id']:<3} | Booster: {p['booster_nombre']:<15} | Cuenta: {p['user_pass']:<20} | Límite: {p['fecha_limite']}")
                print("-" * 75)
            except Exception as e:
                print(f"❌ Error: {e}")

        elif opcion == "3":
            try:
                inv = api_client.obtener_inventario()
                print(f"\n📦 INVENTARIO DE CUENTAS EN STOCK ({len(inv)}):")
                print("-" * 65)
                for c in inv:
                    print(f"• ID #{c['id']:<3} | Tipo: {c['elo_tipo']:<15} | Cuenta: {c['user_pass']:<25}")
                print("-" * 65)
            except Exception as e:
                print(f"❌ Error: {e}")

        elif opcion == "4":
            try:
                rank = api_client.obtener_ranking()
                print(f"\n🏆 RANKING DEL MES ({rank.get('mes')}):")
                print(f"💰 Bote Total: ${rank.get('bote_total')} | Meta 15 Pedidos: {'✅ Cumplida' if rank.get('meta_cumplida') else '⏳ En progreso'}")
                print("-" * 60)
                leaderboard = rank.get("ranking", [])
                if not leaderboard:
                    print("  No hay boosters clasificados este mes aún.")
                else:
                    for item in leaderboard:
                        print(f"#{item['rango']} | {item['booster_nombre']:<15} | Terminados: {item['terminados']} | Score: {item['score']} pts")
                print("-" * 60)
            except Exception as e:
                print(f"❌ Error: {e}")

        elif opcion == "5":
            try:
                fin = api_client.obtener_resumen_financiero()
                print(f"\n📊 RESUMEN FINANCIERO GLOBAL:")
                print("-" * 45)
                print(f"• Pedidos Completados : {fin.get('pedidos_completados')}")
                print(f"• Mi Neto Real        : ${fin.get('mi_neto'):.2f}")
                print(f"• Pago a Staff        : ${fin.get('pago_staff'):.2f}")
                print(f"• Bote Ranking        : ${fin.get('bote_ranking'):.2f}")
                print(f"• Ventas Totales      : ${fin.get('ventas_totales'):.2f}")
                print(f"• Velocidad Media     : {fin.get('velocidad_media_dias')} días")
                print("-" * 45)
            except Exception as e:
                print(f"❌ Error: {e}")

        elif opcion == "6":
            try:
                w = api_client.obtener_balance_wallet()
                print(f"\n💰 BALANCE EN BILLETERA BINANCE:")
                print("-" * 45)
                print(f"• Saldo Neto Perez    : ${w.get('saldo_neto'):.2f}")
                print(f"• Saldo Bote Ranking  : ${w.get('saldo_bote'):.2f}")
                print(f"• Total en Binance    : ${w.get('total_binance'):.2f}")
                print("-" * 45)
            except Exception as e:
                print(f"❌ Error: {e}")

        elif opcion == "7":
            try:
                boosters = api_client.obtener_boosters()
                print(f"\n👥 LISTA DE BOOSTERS Y STAFF ({len(boosters)}):")
                print("-" * 55)
                for b in boosters:
                    rank_status = "🏆 En Ranking" if b.get('en_ranking') == 1 else "⚪ Fuera de Ranking"
                    print(f"• #{b['id']:<2} {b['nombre']:<15} | Binance: {b.get('binance') or 'N/A':<12} | {rank_status}")
                print("-" * 55)
            except Exception as e:
                print(f"❌ Error: {e}")

        elif opcion == "0":
            print("\n👋 ¡Hasta luego!")
            break
        else:
            print("⚠️ Opción no válida. Ingresa un número del 0 al 7.")

if __name__ == "__main__":
    main()
