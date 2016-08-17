from django.contrib.auth.models import User
from rest_framework import serializers

from blockchainrestful.models import BigBlock


class BigBlockSerializer(serializers.ModelSerializer):

    class Meta:
        model = BigBlock
        fields = ('block_id', 'block_number', 'signature', 'votes')


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username',)