"""
DropCore entry point.
Run: python run.py
Dashboard: http://localhost:8888/dashboard
"""
from dropcore import create_app

app = create_app()

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  DropCore — AI-Powered Dropshipping Platform")
    print("=" * 55)
    print("  Dashboard:  http://localhost:8888/dashboard")
    print("  Products:   http://localhost:8888/dashboard/products")
    print("  Orders:     http://localhost:8888/dashboard/orders")
    print("  Agents:     http://localhost:8888/dashboard/agents")
    print("  API:        http://localhost:8888/api/health")
    print("=" * 55)
    print("  7 agents scheduled and running in background")
    print("  Demo mode: ON (set DEMO_MODE=false for live APIs)")
    print("=" * 55 + "\n")
    app.run(host="0.0.0.0", port=8888, debug=False)
