from django.db import models

# Create your models here.

class Config(models.Model):
    activate_registration = models.BooleanField(default=False)
    
    
class StudentProfile(models.Model):
    first_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=7)
    email = models.EmailField()
    age = models.PositiveSmallIntegerField()
    age_status = models.CharField(max_length=10)

    def __str__(self) -> str:
        return f'{self.last_name} {self.middle_name if self.middle_name != "__NA__" else " "} {self.first_name}'