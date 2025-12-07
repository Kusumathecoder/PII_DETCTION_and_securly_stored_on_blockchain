from django.db import models
from django.utils import timezone

class Document(models.Model):
    original_file = models.FileField(upload_to='documents/')
    redacted_file = models.FileField(upload_to='redacted/', null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    filename = models.CharField(max_length=255, blank=True)
    detections = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.filename or self.original_file.name} ({self.uploaded_at.isoformat()})"


class LedgerBlock(models.Model):
    index = models.IntegerField()
    timestamp = models.DateTimeField(default=timezone.now)
    data = models.JSONField()  # store PII hash + type
    hash = models.CharField(max_length=256)
    previous_hash = models.CharField(max_length=256)

    def __str__(self):
        return f"Block {self.index} - {self.hash[:10]}..."
