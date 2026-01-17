function uuid() {
  if (crypto.randomUUID) return crypto.randomUUID();
  return `id-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function setStatus(text) {
  document.querySelectorAll("#offline-status").forEach((el) => {
    el.textContent = text;
  });
}

function formatTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("uz-UZ", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit" });
}

async function renderProducts() {
  const list = document.getElementById("product-list");
  if (!list) return;
  const products = await listEntities("products");
  list.innerHTML = "";
  products.forEach((p) => {
    const row = document.createElement("div");
    row.className = "grid grid-cols-6 gap-2 px-4 py-2 items-center";
    row.innerHTML = `
      <div class="col-span-2">
        <input class="w-full rounded border border-slate-200 px-2 py-1 text-sm" value="${p.name || ""}" data-field="name">
      </div>
      <div><input class="w-full rounded border border-slate-200 px-2 py-1 text-sm" value="${p.barcode || ""}" data-field="barcode"></div>
      <div><input class="w-full rounded border border-slate-200 px-2 py-1 text-sm" value="${p.buy_price || 0}" data-field="buy_price"></div>
      <div><input class="w-full rounded border border-slate-200 px-2 py-1 text-sm" value="${p.sell_price || 0}" data-field="sell_price"></div>
      <div class="flex items-center gap-2">
        <input class="w-full rounded border border-slate-200 px-2 py-1 text-sm" value="${p.stock_qty || 0}" data-field="stock_qty">
        <button class="rounded bg-slate-100 px-2 py-1 text-xs" data-action="save">Saqlash</button>
      </div>
    `;
    row.addEventListener("click", async (event) => {
      if (!event.target.dataset.action) return;
      const inputs = row.querySelectorAll("input[data-field]");
      inputs.forEach((input) => {
        p[input.dataset.field] = input.value;
      });
      p.version = (p.version || 1) + 1;
      p.updated_at = new Date().toISOString();
      await upsertEntity("products", p);
      await addOutboxEvent({
        event_id: uuid(),
        entity_type: "product",
        entity_id: p.id,
        operation: "UPDATE",
        payload_json: p,
        device_id: getDeviceId(),
        created_at: new Date().toISOString(),
        status: "PENDING",
        retry_count: 0,
      });
    });
    list.appendChild(row);
  });
}

async function renderSales() {
  const list = document.getElementById("sale-list");
  if (!list) return;
  const sales = await listEntities("sales");
  const products = await listEntities("products");
  const productMap = Object.fromEntries(products.map((p) => [p.id, p]));
  list.innerHTML = "";
  sales.forEach((s) => {
    const item = (s.items || [])[0] || {};
    const product = productMap[item.product] || {};
    const row = document.createElement("div");
    row.className = "grid grid-cols-5 gap-2 px-4 py-2 items-center";
    row.innerHTML = `
      <div>${formatTime(s.sale_datetime)}</div>
      <div>${product.name || "-"}</div>
      <div>${item.quantity || 0}</div>
      <div>${s.total || 0}</div>
      <div>${s.payment_type || "cash"}</div>
    `;
    list.appendChild(row);
  });
}

async function renderExpenses() {
  const list = document.getElementById("expense-list");
  if (!list) return;
  const expenses = await listEntities("expenses");
  list.innerHTML = "";
  expenses.forEach((e) => {
    const row = document.createElement("div");
    row.className = "grid grid-cols-4 gap-2 px-4 py-2 items-center";
    row.innerHTML = `
      <div>${formatTime(e.expense_datetime)}</div>
      <div>${e.category || "-"}</div>
      <div>${e.amount || 0}</div>
      <div class="text-slate-500">${e.note || ""}</div>
    `;
    list.appendChild(row);
  });
}

async function setupForms() {
  const productForm = document.getElementById("product-form");
  if (productForm) {
    productForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(productForm);
      const item = {
        id: uuid(),
        name: formData.get("name"),
        barcode: formData.get("barcode"),
        buy_price: Number(formData.get("buy_price") || 0),
        sell_price: Number(formData.get("sell_price") || 0),
        stock_qty: Number(formData.get("stock_qty") || 0),
        version: 1,
        updated_at: new Date().toISOString(),
      };
      await upsertEntity("products", item);
      await addOutboxEvent({
        event_id: uuid(),
        entity_type: "product",
        entity_id: item.id,
        operation: "CREATE",
        payload_json: item,
        device_id: getDeviceId(),
        created_at: new Date().toISOString(),
        status: "PENDING",
        retry_count: 0,
      });
      productForm.reset();
      renderProducts();
    });
  }

  const saleForm = document.getElementById("sale-form");
  if (saleForm) {
    const productSelect = saleForm.querySelector("select[name=product_id]");
    const products = await listEntities("products");
    productSelect.innerHTML = '<option value="">Mahsulot</option>';
    products.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = p.name;
      productSelect.appendChild(opt);
    });
    saleForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(saleForm);
      const quantity = Number(formData.get("quantity") || 1);
      const price = Number(formData.get("price") || 0);
      const total = quantity * price;
      const sale = {
        id: uuid(),
        sale_datetime: new Date().toISOString(),
        total,
        payment_type: formData.get("payment_type"),
        seller: formData.get("seller"),
        version: 1,
        updated_at: new Date().toISOString(),
        items: [
          {
            id: uuid(),
            product: formData.get("product_id"),
            quantity,
            price,
          },
        ],
      };
      await upsertEntity("sales", sale);
      await addOutboxEvent({
        event_id: uuid(),
        entity_type: "sale",
        entity_id: sale.id,
        operation: "CREATE",
        payload_json: sale,
        device_id: getDeviceId(),
        created_at: new Date().toISOString(),
        status: "PENDING",
        retry_count: 0,
      });
      saleForm.reset();
      renderSales();
    });
  }

  const expenseForm = document.getElementById("expense-form");
  if (expenseForm) {
    expenseForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(expenseForm);
      const expense = {
        id: uuid(),
        expense_datetime: new Date().toISOString(),
        category: formData.get("category"),
        amount: Number(formData.get("amount") || 0),
        note: formData.get("note"),
        version: 1,
        updated_at: new Date().toISOString(),
      };
      await upsertEntity("expenses", expense);
      await addOutboxEvent({
        event_id: uuid(),
        entity_type: "expense",
        entity_id: expense.id,
        operation: "CREATE",
        payload_json: expense,
        device_id: getDeviceId(),
        created_at: new Date().toISOString(),
        status: "PENDING",
        retry_count: 0,
      });
      expenseForm.reset();
      renderExpenses();
    });
  }
}

async function updateSyncStatus() {
  const pending = document.getElementById("sync-pending");
  const sent = document.getElementById("sync-sent");
  const failed = document.getElementById("sync-failed");
  const last = document.getElementById("sync-last");
  const outbox = await listOutbox();
  const lastSync = await getMeta("last_sync");
  if (pending) pending.textContent = outbox.filter((e) => e.status === "PENDING").length;
  if (sent) sent.textContent = outbox.filter((e) => e.status === "SENT").length;
  if (failed) failed.textContent = outbox.filter((e) => e.status === "FAILED").length;
  if (last) last.textContent = lastSync ? new Date(lastSync).toLocaleString() : "-";
}

async function setupStatusPage() {
  const form = document.getElementById("auth-form");
  const authStatus = document.getElementById("auth-status");
  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      try {
        await fetchToken(formData.get("username"), formData.get("password"));
        authStatus.textContent = "Token saqlandi";
      } catch (err) {
        authStatus.textContent = "Token olinmadi";
      }
    });
  }
  const syncBtn = document.getElementById("sync-now");
  if (syncBtn) {
    syncBtn.addEventListener("click", async () => {
      await runSync();
      updateSyncStatus();
    });
  }
  updateSyncStatus();
}

function updateOnlineStatus() {
  setStatus(navigator.onLine ? "Online" : "Offline");
}

document.addEventListener("DOMContentLoaded", async () => {
  updateOnlineStatus();
  window.addEventListener("online", updateOnlineStatus);
  window.addEventListener("offline", updateOnlineStatus);
  await setupForms();
  await renderProducts();
  await renderSales();
  await renderExpenses();
  await setupStatusPage();
  setInterval(() => {
    if (navigator.onLine) runSync().then(updateSyncStatus);
  }, 15000);
});
