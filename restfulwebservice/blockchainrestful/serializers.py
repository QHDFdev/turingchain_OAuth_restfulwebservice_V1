from django.contrib.auth.models import User
from rest_framework import serializers

from blockchainrestful.models import BigBlock


class BigBlockSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = BigBlock
        fields = ('url', 'id', 'block_number', 'signature')


class UserSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = User
        fields = ('url', 'username')