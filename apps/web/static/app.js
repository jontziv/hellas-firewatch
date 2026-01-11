/* Hellas Firewatch - no build step, vanilla JS */

function ensureDeviceFingerprint() {
  const name = "hf_fp";
  const existing = document.cookie.split(";").map(s => s.trim()).find(s => s.startsWith(name + "="));
  if (existing) return;

  // random string; not PII; used for basic abuse prevention
  const fp = crypto.getRandomValues(new Uint32Array(4)).join("-");
  document.cookie = `${name}=${fp}; path=/; max-age=${60*60*24*365}; samesite=lax`;
}

function fwiClass(bucket) {
  if (bucket >= 4) return "fwi4";
  if (bucket >= 2) return "fwi2";
  return "fwi0";
}

function windArrow(deg) {
  return `<span style="display:inline-block; transform: rotate(${deg}deg);">➤</span> ${deg}°`;
}

async function fetchDetections({ hours, min_confidence }) {
  const url = `/api/detections?hours=${encodeURIComponent(hours)}&min_confidence=${encodeURIComponent(min_confidence)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to load detections (${res.status})`);
  return await res.json();
}

async function fetchMetrics() {
  const res = await fetch(`/api/metrics?window_hours=24`);
  if (!res.ok) return null;
  return await res.json();
}

async function submitVerification(detectionId, verdict, photoFile) {
  const fd = new FormData();
  fd.append("verdict", verdict);
  if (photoFile) fd.append("photo", photoFile);

  const res = await fetch(`/api/detections/${encodeURIComponent(detectionId)}/verify`, {
    method: "POST",
    body: fd
  });

  const payload = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = payload.detail || `Verify failed (${res.status})`;
    throw new Error(msg);
  }
  return payload;
}

function distanceKm(a, b) {
  const R = 6371;
  const toRad = (x) => x * Math.PI / 180;
  const dLat = toRad(b.lat - a.lat);
  const dLon = toRad(b.lon - a.lon);
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);
  const s = Math.sin(dLat/2)**2 + Math.cos(lat1)*Math.cos(lat2)*Math.sin(dLon/2)**2;
  return 2 * R * Math.asin(Math.sqrt(s));
}

function fmtTime(iso) {
  const d = new Date(iso);
  return d.toLocaleString();
}

function createPopupContent(p) {
  const c = p.community || { confirms: 0, denies: 0, unsure: 0 };
  const status = p.status || "unconfirmed";
  const badge =
    `<div class="badge">
      <span class="pill ok">✅ ${c.confirms} confirm</span>
      <span class="pill no">❌ ${c.denies} deny</span>
      <span class="pill maybe">🤷 ${c.unsure} unsure</span>
    </div>`;

  const risk = `<div class="note">Risk: <span class="pill ${fwiClass(p.fwi_bucket)}">FWI ${p.fwi_bucket}</span></div>`;
  const wind = `<div class="note">Wind: ${windArrow(p.wind_dir_deg || 0)}</div>`;

  return `
    <div class="popupTitle">Detection</div>
    ${badge}
    <div class="note">Time: ${fmtTime(p.created_at)}</div>
    <div class="note">Confidence: ${(p.confidence ?? 0).toFixed(2)} | Status: ${status}</div>
    ${risk}
    ${wind}
    <div style="margin-top:10px;">
      <label class="note">Optional photo
        <input type="file" accept="image/*" id="photo_${p.id}" />
      </label>
      <div class="btnRow">
        <button class="btnSmall" data-verify="confirm" data-id="${p.id}">Confirm</button>
        <button class="btnSmall" data-verify="deny" data-id="${p.id}">Deny</button>
        <button class="btnSmall" data-verify="unsure" data-id="${p.id}">Unsure</button>
      </div>
      <div class="note" id="msg_${p.id}" style="margin-top:8px;"></div>
    </div>
  `;
}

function setupMap() {
  const map = L.map("map", { zoomControl: true }).setView([39.0, 22.0], 6);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  const detectionsLayer = L.layerGroup().addTo(map);
  const riskLayer = L.layerGroup().addTo(map);

  return { map, detectionsLayer, riskLayer };
}

function drawRiskOverlay(riskLayer, features) {
  riskLayer.clearLayers();
  features.forEach(f => {
    const p = f.properties;
    const latlng = [f.geometry.coordinates[1], f.geometry.coordinates[0]];
    const bucket = p.fwi_bucket ?? 2;

    // "Risk halo" circle. Later: swap with EFFIS tiles/WMS.
    const radius = 1500 + bucket * 900;
    const cls = fwiClass(bucket);

    L.circle(latlng, { radius, className: cls }).addTo(riskLayer);
  });
}

function drawDetections(detectionsLayer, features) {
  detectionsLayer.clearLayers();

  features.forEach(f => {
    const p = f.properties;
    const latlng = [f.geometry.coordinates[1], f.geometry.coordinates[0]];

    const marker = L.circleMarker(latlng, { radius: 9, weight: 2 });
    marker.bindPopup(createPopupContent(p), { maxWidth: 320 });

    marker.on("popupopen", () => {
      const popupEl = marker.getPopup().getElement();
      if (!popupEl) return;

      popupEl.querySelectorAll("button[data-verify]").forEach(btn => {
        btn.addEventListener("click", async () => {
          const verdict = btn.getAttribute("data-verify");
          const id = btn.getAttribute("data-id");
          const msg = popupEl.querySelector(`#msg_${CSS.escape(id)}`);

          const input = popupEl.querySelector(`#photo_${CSS.escape(id)}`);
          const photoFile = (input && input.files && input.files[0]) ? input.files[0] : null;

          try {
            btn.disabled = true;
            if (msg) msg.textContent = "Submitting…";
            const out = await submitVerification(id, verdict, photoFile);
            if (msg) msg.textContent = `Saved. Status: ${out.status}.`;

            // Refresh map to reflect acceptance/dismissal.
            window.__hf_refresh && window.__hf_refresh();
          } catch (e) {
            if (msg) msg.textContent = (e && e.message) ? e.message : "Error";
          } finally {
            btn.disabled = false;
          }
        });
      });
    });

    marker.addTo(detectionsLayer);
  });
}

async function main() {
  ensureDeviceFingerprint();

  const { detectionsLayer, riskLayer } = setupMap();

  const confInput = document.getElementById("confidence");
  const confValue = document.getElementById("confValue");
  const hoursSel = document.getElementById("hours");
  const refreshBtn = document.getElementById("refresh");
  const metricsEl = document.getElementById("metrics");
  const nearbyStatus = document.getElementById("nearbyStatus");
  const locateBtn = document.getElementById("locate");

  confValue.textContent = Number(confInput.value).toFixed(2);
  confInput.addEventListener("input", () => confValue.textContent = Number(confInput.value).toFixed(2));

  async function refreshAll() {
    const hours = Number(hoursSel.value);
    const min_confidence = Number(confInput.value);

    const fc = await fetchDetections({ hours, min_confidence });
    const feats = fc.features || [];

    drawRiskOverlay(riskLayer, feats);
    drawDetections(detectionsLayer, feats);

    if (window.__hf_user_loc) {
      const user = window.__hf_user_loc;
      const nearby = feats
        .map(f => ({
          d: distanceKm(user, { lat: f.geometry.coordinates[1], lon: f.geometry.coordinates[0] })
        }))
        .filter(x => x.d <= 15)
        .sort((a,b) => a.d - b.d);

      if (nearby.length) {
        nearbyStatus.textContent = `Nearby detections: ${nearby.length} (closest ${nearby[0].d.toFixed(1)} km). Click the point to verify.`;
      } else {
        nearbyStatus.textContent = "No detections within 15 km.";
      }
    }

    const m = await fetchMetrics();
    if (m) {
      metricsEl.innerHTML = `
        <div class="note">North-star: <b>${m.north_star_pct.toFixed(1)}%</b></div>
        <div class="note">False-alarm rate: <b>${(m.false_alarm_rate*100).toFixed(1)}%</b></div>
        <div class="note">Abuse block rate: <b>${(m.abuse_block_rate*100).toFixed(1)}%</b></div>
        <div class="note">Detections: ${m.totals.detections} | Accepted: ${m.totals.accepted} | Dismissed: ${m.totals.dismissed}</div>
      `;
    } else {
      metricsEl.textContent = "Unavailable";
    }
  }

  window.__hf_refresh = refreshAll;

  refreshBtn.addEventListener("click", refreshAll);
  await refreshAll();

  locateBtn.addEventListener("click", () => {
    if (!navigator.geolocation) {
      nearbyStatus.textContent = "Geolocation not supported.";
      return;
    }
    nearbyStatus.textContent = "Requesting location…";
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        window.__hf_user_loc = { lat: pos.coords.latitude, lon: pos.coords.longitude };
        nearbyStatus.textContent = "Location enabled. Refreshing…";
        refreshAll();
      },
      () => nearbyStatus.textContent = "Location permission denied.",
      { enableHighAccuracy: false, timeout: 8000 }
    );
  });
}

main().catch((e) => {
  console.error(e);
  alert("App failed to start: " + (e.message || e));
});
