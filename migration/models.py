from django.db import models

class LegacyOrder(models.Model):
    external_id = models.CharField(max_length=100, unique=True)
    raw_data = models.JSONField()
    migrated = models.BooleanField(default=False)

    def __str__(self):
        return self.external_id

class Order(models.Model):
    customer_email = models.EmailField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    external_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.customer_email}"

class OrderLine(models.Model):
    order = models.ForeignKey(Order, related_name='lines', on_delete=models.CASCADE)
    sku = models.CharField(max_length=50)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.sku} x {self.quantity}"
