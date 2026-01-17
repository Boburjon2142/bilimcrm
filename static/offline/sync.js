const TOKEN_KEY = "offline_token";
const DEVICE_KEY = "offline_device_id";

function getDeviceId() {
  let id = localStorage.getItem(DEVICE_KEY);
  if (!id) {
    id = crypto.randomUUID ? crypto.randomUUID() : `dev-${Date.now()}`;
    localStorage.setItem(DEVICE_KEY, id);
  }
  return id;
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

function parseJwt(token) {
  try {
    const payload = token.split(".")[1];
    const decoded = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decoded);
  } catch (err) {
    return null;
  }
}

function tokenExpired(token) {
  const payload = parseJwt(token);
  if (!payload || !payload.exp) return true;
  return Date.now() >= payload.exp * 1000;
}

async function fetchToken(username, password) {
  const response = await fetch("/api/auth/token/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    throw new Error("Token error");
  }
  const data = await response.json();
  if (data.access) {
    setToken(data.access);
  }
  return data;
}

async function pushOutbox() {
  const token = getToken();
  if (!token || tokenExpired(token)) {
    return { ok: false, reason: "token" };
  }
  const events = (await listOutbox()).filter((e) => e.status === "PENDING");
  if (!events.length) return { ok: true, count: 0 };
  const payload = {
    device_id: getDeviceId(),
    events: events.map((event) => ({
      event_id: event.event_id,
      entity_type: event.entity_type,
      entity_id: event.entity_id,
      operation: event.operation,
      payload_json: event.payload_json,
    })),
  };

  const response = await fetch("/api/sync/push", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    return { ok: false, reason: "network" };
  }
  const data = await response.json();
  for (const item of data.results || []) {
    if (item.status === "applied" || item.status === "duplicate") {
      await updateOutboxStatus(item.event_id, "SENT", 0);
    } else {
      const current = events.find((e) => e.event_id === item.event_id);
      const retries = current ? (current.retry_count || 0) + 1 : 1;
      await updateOutboxStatus(item.event_id, "FAILED", retries);
    }
  }
  await setMeta("last_sync", data.server_time || new Date().toISOString());
  return { ok: true, count: events.length };
}

async function pullChanges() {
  const token = getToken();
  if (!token || tokenExpired(token)) {
    return { ok: false, reason: "token" };
  }
  const since = (await getMeta("last_sync")) || "";
  const response = await fetch(`/api/sync/pull?since=${encodeURIComponent(since)}`, {
    headers: { "Authorization": `Bearer ${token}` },
  });
  if (!response.ok) return { ok: false, reason: "network" };
  const data = await response.json();
  for (const product of data.products || []) {
    await upsertEntity("products", product);
  }
  for (const customer of data.customers || []) {
    await upsertEntity("customers", customer);
  }
  for (const sale of data.sales || []) {
    await upsertEntity("sales", sale);
  }
  for (const expense of data.expenses || []) {
    await upsertEntity("expenses", expense);
  }
  await setMeta("last_sync", data.server_time || new Date().toISOString());
  return { ok: true };
}

async function runSync() {
  const push = await pushOutbox();
  if (!push.ok) return push;
  return pullChanges();
}
