import base64
import json
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

secret = subprocess.check_output([
    "kubectl", "get", "secret", "obs-grafana",
    "-n", "monitoring",
    "-o", "jsonpath={.data.admin-password}"
], text=True)

password = base64.b64decode(secret).decode()

Path("evidence/screenshots").mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(
        viewport={"width": 1600, "height": 1400},
        device_scale_factor=1
    )

    response = context.request.post(
        "http://127.0.0.1:3000/login",
        data={"user": "admin", "password": password}
    )
    if response.status != 200:
        raise RuntimeError("Grafana login failed")

    # Wait for the dashboard sidecar to provision our dashboard.
    for attempt in range(60):
        dashboard = context.request.get(
            "http://127.0.0.1:3000/api/dashboards/uid/logistics-overview"
        )
        if dashboard.status == 200:
            break
        time.sleep(2)
    else:
        raise RuntimeError("Logistics dashboard was not provisioned")

    page = context.new_page()
    page.goto(
        "http://127.0.0.1:3000/d/logistics-overview"
        "?from=now-15m&to=now&kiosk",
        wait_until="domcontentloaded"
    )
    page.get_by_text("Request rate", exact=True).first.wait_for(
        state="visible", timeout=60000
    )

    # Allow panel queries and graphs to finish rendering.
    page.wait_for_timeout(20000)
    page.screenshot(
        path="evidence/screenshots/03-grafana-dashboard.png",
        full_page=True
    )

    print("Grafana screenshot captured. Review the image for panel data.")
    browser.close()
