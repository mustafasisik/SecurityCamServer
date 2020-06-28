from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'last_login', 'date_joined']


class SCSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SCSystem
        fields = '__all__'


class SCMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = SCMember
        fields = '__all__'


class SCKnownPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = SCKnownPerson
        fields = '__all__'


class SCDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SCData
        fields = '__all__'

