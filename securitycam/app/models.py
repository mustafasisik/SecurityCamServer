from django.contrib.auth.models import User
from django.db import models


class TestContent(models.Model):
    text = models.TextField()
    image = models.FileField(null=True, blank=True)

    def __str__(self):
        return self.text


class SCSystem(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, default="System Name")
    code = models.CharField(max_length=20)
    security_percent = models.IntegerField(default=40)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-id']


class SCData(models.Model):
    system = models.ForeignKey(SCSystem, on_delete=models.SET_NULL, blank=True, null=True)
    text = models.CharField(max_length=100)
    image = models.FileField(null=True, blank=True)
    time = models.DateTimeField(auto_now_add=True)
    safety = models.CharField(max_length=50)
    suspicious = models.CharField(max_length=50, default="0")
    is_regular = models.BooleanField(default=True)

    def __str__(self):
        return self.text


class SCMember(models.Model):
    system = models.ForeignKey(SCSystem, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    MEMBER_TYPES = [(0, "Member"), (1, "Host")]
    type = models.IntegerField(choices=MEMBER_TYPES, default=0)
    is_selected = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        ordering = ['-id']


class SCKnownPerson(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    data = models.ForeignKey(SCData, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name



