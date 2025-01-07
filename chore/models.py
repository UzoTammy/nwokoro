from django.db import models
from account.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

class Work(models.Model):
    name = models.CharField(max_length=50)
    point = models.PositiveIntegerField()
    description = models.TextField()
    kind = models.CharField(max_length=15, default='regular') #regular, occassional, one-time
    
    def __str__(self):
        return self.name

class JobRegister(models.Model):
    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE)
    duration = models.PositiveSmallIntegerField()
    
    def __str__(self):
        return self.work
 
class AssignWork(models.Model):
    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    assigned = models.ForeignKey(User, on_delete=models.CASCADE)
    schedule = models.DateTimeField(auto_now_add=timezone.now) # not editable and not modifiable
    end_time = models.DateTimeField(default=timezone.now)
    source = models.CharField(max_length=20, default='delegated') # delegated, scheduled, initiated
    # status = models.BooleanField(default=True) # active is True, Done/Cancelled is False
    state = models.CharField(max_length=10, default='active') # active, repeat, done & cancel

    def is_expired(self):
        if self.end_time > timezone.now():
            return False # end time is yet to come
        return True

class FinishedWork(models.Model):
    worker = models.ForeignKey(User, on_delete=models.CASCADE)
    work = models.CharField(max_length=50)
    base_point = models.IntegerField()
    bonus_point = models.IntegerField()
    scheduled_time = models.DateTimeField()
    end_time = models.DateTimeField()
    finished_time = models.DateTimeField()
    state = models.CharField(max_length=10) #done, cancel
    reason = models.CharField(max_length=20) #expired, not committed, 
    rating = models.FloatField(default=0.7)

    def __str__(self):
        return f'Finished Work({self.work})'
    
    def points(self):
        return self.base_point + self.bonus_point
    
    def clean(self):
        """Ensure cancelled jobs do not get rated"""
        super().clean()  # Call parent clean method
        if self.state == 'cancel' and self.rating > 0.0:
            raise ValidationError({'rating': 'A cancelled job cannot get a rating'})

    def save(self, *args, **kwargs):
        """Call clean before saving."""
        self.clean()
        super().save(*args, **kwargs)
     
class InitiateWork(models.Model):
    worker = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    description = models.TextField()
    point = models.PositiveIntegerField(default=0)
    approved = models.BooleanField(default=False)

class BonusPoint(models.Model):
    title = models.CharField(max_length=30)
    active = models.BooleanField(default=False)
    bonus_value = models.FloatField(default=0.0)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField()

    # class Meta:
        # """Why the constraiant? To ensure that no more than one
        # instance is active at the same time"""
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=['active'], 
        #         condition=models.Q(active=True), 
        #         name='unique_active_record'
        #     ),
        # ]
        
    def __str__(self):
        return self.title
    
    def clean(self):
        """Enforce end_date > start_date."""
        super().clean()  # Call parent clean method
        if self.end_time <= self.start_time:
            raise ValidationError({'end_time': 'The end time must be ahead of the start time.'})
        
    def save(self, *args, **kwargs):
        """Call clean before saving."""
        self.clean()
        
        # if self.active:
        #     # Check if there are any other records with is_active=True
        #     if BonusPoint.objects.filter(active=True).exclude(pk=self.pk).exists():
        #         raise ValidationError("Only one record can have 'active=True' at a time.")
        super().save(*args, **kwargs)



