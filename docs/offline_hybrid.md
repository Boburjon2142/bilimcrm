# Offline Hybrid MVP

## Quick overview
- Offline UI: `/offline/products/`, `/offline/sales/`, `/offline/expenses/`, `/offline/status/`
- Sync API: `POST /api/sync/push`, `GET /api/sync/pull?since=...`
- Auth: `POST /api/auth/token/` (JWT access)

## Commands
```bash
python manage.py migrate
python manage.py runserver
```

If you use static collection in production:
```bash
python manage.py collectstatic
```

## How to test offline
1) Open `/offline/status/`, login with username/password to get token.
2) Open `/offline/products/` and add products.
3) Open `/offline/sales/` and add a sale.
4) In Chrome DevTools > Network > Offline, repeat steps above.
5) Turn Online back on and click "Hozir sync".

## Manual test scenarios (frontend)
1) Offline create Product -> outbox pending -> online sync -> product appears in server DB.
2) Offline create Sale -> online sync -> sale appears in admin.
3) Offline create Expense -> online sync -> expense appears in admin.

## Backend test targets
- Sync idempotency for duplicate event_id
- Product version conflict with stock_qty change
- Sales append-only behavior
- Expense update rejection
- Pull endpoint returns changes since timestamp
