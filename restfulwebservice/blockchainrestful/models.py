from django.db import models


class BigBlock(models.Model):
    id = models.CharField
    block_number = models.IntegerField
    signature = models.CharField

    class Meta:
        ordering = ('block_number')