from django.contrib import admin
from .models import *


class SCDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'time', 'safety')

admin.site.register(TestContent)
admin.site.register(SCSystem)
admin.site.register(SCData, SCDataAdmin)
admin.site.register(SCMember)
admin.site.register(SCKnownPerson)