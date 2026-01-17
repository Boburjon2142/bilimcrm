const DB_NAME = "offline-crm";
const DB_VERSION = 1;

function dbInit() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains("products")) {
        db.createObjectStore("products", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("sales")) {
        db.createObjectStore("sales", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("expenses")) {
        db.createObjectStore("expenses", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("customers")) {
        db.createObjectStore("customers", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("outbox")) {
        db.createObjectStore("outbox", { keyPath: "event_id" });
      }
      if (!db.objectStoreNames.contains("meta")) {
        db.createObjectStore("meta", { keyPath: "key" });
      }
    };
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

async function withStore(storeName, mode, callback) {
  const db = await dbInit();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, mode);
    const store = tx.objectStore(storeName);
    const result = callback(store);
    tx.oncomplete = () => resolve(result);
    tx.onerror = () => reject(tx.error);
  });
}

function upsertEntity(storeName, value) {
  return withStore(storeName, "readwrite", (store) => store.put(value));
}

function deleteEntity(storeName, id) {
  return withStore(storeName, "readwrite", (store) => store.delete(id));
}

function listEntities(storeName) {
  return withStore(storeName, "readonly", (store) => {
    return new Promise((resolve, reject) => {
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error);
    });
  });
}

function getEntity(storeName, id) {
  return withStore(storeName, "readonly", (store) => {
    return new Promise((resolve, reject) => {
      const req = store.get(id);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error);
    });
  });
}

function setMeta(key, value) {
  return withStore("meta", "readwrite", (store) => store.put({ key, value }));
}

function getMeta(key) {
  return withStore("meta", "readonly", (store) => {
    return new Promise((resolve, reject) => {
      const req = store.get(key);
      req.onsuccess = () => resolve(req.result ? req.result.value : null);
      req.onerror = () => reject(req.error);
    });
  });
}

function listOutbox() {
  return listEntities("outbox");
}

function addOutboxEvent(event) {
  return upsertEntity("outbox", event);
}

function updateOutboxStatus(event_id, status, retry_count) {
  return withStore("outbox", "readwrite", (store) => {
    return new Promise((resolve, reject) => {
      const req = store.get(event_id);
      req.onsuccess = () => {
        const item = req.result;
        if (!item) return resolve();
        item.status = status;
        item.retry_count = retry_count;
        store.put(item);
        resolve();
      };
      req.onerror = () => reject(req.error);
    });
  });
}

function clearOutbox(event_id) {
  return deleteEntity("outbox", event_id);
}
