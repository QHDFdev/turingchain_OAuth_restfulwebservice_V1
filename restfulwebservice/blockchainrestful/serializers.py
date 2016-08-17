from django.contrib.auth.models import User
from rest_framework import serializers

from blockchainrestful.models import BigBlock


class BigBlockSerializer(serializers.ModelSerializer):
    id = serializers.CharField

    class Meta:
        model = BigBlock
        fields = ('block_number', 'signature')


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username',)