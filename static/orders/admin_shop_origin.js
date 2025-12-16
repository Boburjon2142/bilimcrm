// Leaflet map for selecting shop origin in DeliverySettings admin
(function () {
  function initMap() {
    if (typeof L === "undefined") return;
    const latInput = document.getElementById("id_shop_lat");
    const lngInput = document.getElementById("id_shop_lng");
    if (!latInput || !lngInput) return;

    // Create container after lng input
    const wrapper = document.createElement("div");
    wrapper.id = "shop-origin-map";
    wrapper.style.height = "260px";
    wrapper.style.marginTop = "8px";
    wrapper.style.border = "1px solid #dfe5ef";
    wrapper.style.borderRadius = "8px";
    wrapper.style.overflow = "hidden";

    // Hide raw inputs but keep them in DOM
    if (latInput.parentElement) latInput.parentElement.style.display = "none";
    if (lngInput.parentElement) lngInput.parentElement.style.display = "none";

    // Place map after lng input container if possible
    const target = lngInput.parentElement || lngInput;
    if (target && target.parentElement) {
      target.parentElement.appendChild(wrapper);
    } else {
      document.body.appendChild(wrapper);
    }

    const startLat = parseFloat(latInput.value) || 41.2995;
    const startLng = parseFloat(lngInput.value) || 69.2401;

    const map = L.map("shop-origin-map").setView([startLat, startLng], 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap",
    }).addTo(map);

    const marker = L.marker([startLat, startLng]).addTo(map);

    function updateInputs(lat, lng) {
      latInput.value = lat.toFixed(6);
      lngInput.value = lng.toFixed(6);
    }

    map.on("click", function (e) {
      const lat = e.latlng.lat;
      const lng = e.latlng.lng;
      marker.setLatLng([lat, lng]);
      updateInputs(lat, lng);
    });

    function syncFromInputs() {
      const lat = parseFloat(latInput.value);
      const lng = parseFloat(lngInput.value);
      if (!isFinite(lat) || !isFinite(lng)) return;
      marker.setLatLng([lat, lng]);
      map.setView([lat, lng], map.getZoom());
    }

    latInput.addEventListener("change", syncFromInputs);
    lngInput.addEventListener("change", syncFromInputs);
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Leaflet may load async; poll a bit
    let tries = 0;
    const timer = setInterval(function () {
      tries += 1;
      if (typeof L !== "undefined") {
        clearInterval(timer);
        initMap();
      }
      if (tries > 20) clearInterval(timer);
    }, 100);
  });
})();
