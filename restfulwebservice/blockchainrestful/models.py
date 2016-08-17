from django.db import models


class VoteDetail(models.Model):
    previous_block = models.CharField
    timestamp = models.CharField
    voting_for_block = models.CharField
    invalid_reason = models.CharField
    is_block_valid = models.BooleanField


class Vote(models.Model):
    signature = models.CharField
    node_pubkey = models.CharField
    vote = models.OneToOneField(VoteDetail)


class BigBlock(models.Model):
    block_id = models.CharField
    block_number = models.IntegerField
    signature = models.CharField
    votes = models.ManyToManyField(Vote)