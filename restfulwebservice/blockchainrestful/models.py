from django.db import models


class BigBlock(models.Model):
    id = models.CharField
    block_number = models.CharField
    signature = models.CharField