from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Product, Sale, Expense, ConflictLog, SyncEventLog


class SyncApiTests(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="tester", password="pass1234")
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def _push(self, events):
        return self.client.post("/api/sync/push", {"device_id": "device-1", "events": events}, format="json")

    def test_product_create_idempotent(self):
        event_id = uuid4()
        product_id = uuid4()
        payload = {
            "event_id": str(event_id),
            "entity_type": "product",
            "entity_id": str(product_id),
            "operation": "CREATE",
            "payload_json": {"id": str(product_id), "name": "Test", "sell_price": "1000", "version": 1},
        }
        resp1 = self._push([payload])
        resp2 = self._push([payload])
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(resp2.data["results"][0]["status"], "duplicate")

    def test_product_conflict_marks_review(self):
        product = Product.objects.create(name="A", stock_qty=5, version=2)
        event_id = uuid4()
        payload = {
            "event_id": str(event_id),
            "entity_type": "product",
            "entity_id": str(product.id),
            "operation": "UPDATE",
            "payload_json": {"id": str(product.id), "name": "A", "stock_qty": 10, "version": 1},
        }
        resp = self._push([payload])
        product.refresh_from_db()
        self.assertEqual(resp.data["results"][0]["status"], "conflict")
        self.assertTrue(product.needs_review)
        self.assertEqual(ConflictLog.objects.count(), 1)

    def test_sale_append_only(self):
        sale_id = uuid4()
        event_id = uuid4()
        payload = {
            "event_id": str(event_id),
            "entity_type": "sale",
            "entity_id": str(sale_id),
            "operation": "CREATE",
            "payload_json": {
                "id": str(sale_id),
                "sale_datetime": timezone.now().isoformat(),
                "total": "2000",
                "payment_type": "cash",
                "items": [],
            },
        }
        resp = self._push([payload])
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Sale.objects.count(), 1)

    def test_expense_append_only_reject_update(self):
        exp_id = uuid4()
        event_id = uuid4()
        payload = {
            "event_id": str(event_id),
            "entity_type": "expense",
            "entity_id": str(exp_id),
            "operation": "UPDATE",
            "payload_json": {"id": str(exp_id), "amount": "1000"},
        }
        resp = self._push([payload])
        self.assertEqual(resp.data["results"][0]["status"], "ignored")
        self.assertEqual(Expense.objects.count(), 0)

    def test_pull_since(self):
        product = Product.objects.create(name="P", sell_price=Decimal("10"))
        resp = self.client.get("/api/sync/pull", {"since": (timezone.now() - timezone.timedelta(days=1)).isoformat()})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["products"]), 1)
