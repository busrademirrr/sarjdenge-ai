"""End-to-End Test for ŞarjDenge AI Web System.

Starts node web/server/index.js, makes live HTTP requests to API endpoints,
tests simulation execution through the Python bridge, and verifies frontend serving.
"""

import json
import subprocess
import sys
import time
import urllib.request
import urllib.error

SERVER_URL = "http://localhost:5000"

def test_e2e():
    print("[E2E] Starting Node.js server...")
    node_proc = subprocess.Popen(
        ["node", "index.js"],
        cwd="web/server",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    time.sleep(2.0)
    
    try:
        # 1. Health check
        print("[E2E] 1. Testing GET /api/health...")
        with urllib.request.urlopen(f"{SERVER_URL}/api/health", timeout=5) as r:
            assert r.status == 200
            data = json.loads(r.read().decode('utf-8'))
            assert data["status"] == "ok"
            print("   -> OK:", data["app"])

        # 2. Scenarios list
        print("[E2E] 2. Testing GET /api/scenarios...")
        with urllib.request.urlopen(f"{SERVER_URL}/api/scenarios", timeout=5) as r:
            assert r.status == 200
            data = json.loads(r.read().decode('utf-8'))
            assert data["success"] is True
            assert len(data["scenarios"]) >= 4
            print(f"   -> OK: {len(data['scenarios'])} scenarios loaded.")

        # 3. Benchmark results
        print("[E2E] 3. Testing GET /api/benchmark-results...")
        with urllib.request.urlopen(f"{SERVER_URL}/api/benchmark-results", timeout=5) as r:
            assert r.status == 200
            data = json.loads(r.read().decode('utf-8'))
            assert data["success"] is True
            assert data["primaryHypothesis"]["desteklendi_mi"] is False
            print("   -> OK: Benchmark results verified. Hypothesis verdict:", data["primaryHypothesis"]["desteklendi_mi"])

        # 4. Interactive Simulation (live Python execution)
        print("[E2E] 4. Testing POST /api/simulate (live python execution)...")
        req_data = json.dumps({"scenarioId": "isyeri_gunduz", "f": 0.5}).encode('utf-8')
        req = urllib.request.Request(
            f"{SERVER_URL}/api/simulate",
            data=req_data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            assert r.status == 200
            data = json.loads(r.read().decode('utf-8'))
            assert data["success"] is True
            sim = data["simulation"]
            assert len(sim["zaman_etiketleri"]) == 96
            assert "fcfs_beyan" in sim["yontem_profilleri"]
            assert "mpc_tahmin_guvenli" in sim["yontem_profilleri"]
            print(f"   -> OK: Simulated {sim['arac_sayisi']} vehicles in {sim['senaryo_id']} at f={sim['f_orani']}")

        # 5. Frontend static serving
        print("[E2E] 5. Testing GET / (React frontend serving)...")
        with urllib.request.urlopen(f"{SERVER_URL}/", timeout=5) as r:
            assert r.status == 200
            html = r.read().decode('utf-8')
            assert '<div id="root">' in html
            print("   -> OK: Frontend HTML served properly.")

        print("\n[E2E] ALL 5 END-TO-END CHECKS PASSED SUCCESSFULLY!")

    finally:
        print("[E2E] Terminating server...")
        node_proc.terminate()
        try:
            node_proc.wait(timeout=3)
        except Exception:
            node_proc.kill()


if __name__ == "__main__":
    test_e2e()
