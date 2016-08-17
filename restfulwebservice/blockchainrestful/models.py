from django.db import models


class BigBlock(models.Model):
    block_number = models.IntegerField
    signature = models.CharField
    id = models.CharField