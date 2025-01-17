from django.db import models
from account.models import User

# Create your models here.
class Reward(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    point = models.PositiveIntegerField()
    reason = models.TextField()
    category = models.CharField(max_length=50, default='Behaviour')
    timestamp = models.DateTimeField(auto_now_add=True)
    issued_by = models.CharField(max_length=30)

    def __str__(self):
        return f'Reward: {self.user} {self.point} {self.timestamp}'
    
