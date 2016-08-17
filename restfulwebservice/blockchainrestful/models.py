from django.db import models


class BigBlock(models.Model):
    block_id = models.CharField
    block_number = models.IntegerField
    signature = models.CharField