from django.db import models
from django.utils import timezone

class Block(models.Model):
    index = models.PositiveIntegerField()
    timestamp = models.DateTimeField(default=timezone.now)
    data = models.JSONField()
    previous_hash = models.CharField(max_length=64)
    hash = models.CharField(max_length=64)
    nonce = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['index']

    def __str__(self):
        return f"Block {self.index} - {self.hash[:10]}"

class Ledger(models.Model):
    transaction_id = models.CharField(max_length=64)
    pii_data = models.JSONField()
    hash = models.CharField(max_length=64)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Ledger Entry {self.transaction_id}"
