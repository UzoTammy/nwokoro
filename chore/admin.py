from django.contrib import admin
from .models import Work, AssignWork, JobRegister, FinishedWork, BonusPoint

# Register your models here.
admin.site.register(Work)
admin.site.register(AssignWork)
admin.site.register(JobRegister)
admin.site.register(FinishedWork)
admin.site.register(BonusPoint)
