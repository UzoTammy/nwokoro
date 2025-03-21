from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from djmoney.models.fields import MoneyField

# Create your models here.
class CustomAccountManager(BaseUserManager):
    def create_user(self, email, username, date_of_birth, password=None, **extra_fields):
        if not email:
            ValueError(_("You must provide a valid email"))

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, date_of_birth=date_of_birth, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, date_of_birth, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
                
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True") 
        
        return self.create_user(email=email, username=username, date_of_birth=date_of_birth, password=password, **extra_fields)
    
class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(verbose_name='email', max_length=50, unique=True)
    date_of_birth = models.DateField()
    points = models.IntegerField(default=0)
    date_joined = models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    last_login = models.DateTimeField(verbose_name='last login', auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    preferences = models.JSONField(default=dict)
    
    
    objects = CustomAccountManager()
    
    def __str__(self):
        return f"{self.username}: {self.points} points"
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'date_of_birth']

    def deposit(self, points, description=None):
        """
        Deposit points to the user's account and create a transaction record.
        """
        if points <= 0:
            raise ValidationError("Deposit amount must be greater than zero.")
        self.points += points
        self.save()

        # Create a transaction record
        Transaction.objects.create(user=self, transaction_type="Deposit", amount=points,
                                   description=description or 'Points deposited to account')

    def withdraw(self, points, description=None):
        """
        Withdraw points in multiples of 10,000 and create a transaction record.
        """
        if points <= 0:
            raise ValidationError("Withdrawal points must be greater than zero.")
        if points % 10000 != 0:
            raise ValidationError("Withdrawal points must be in multiples of 10,000.")
        if points > self.points:
            raise ValidationError("Insufficient points for withdrawal.")

        self.points -= points
        self.save()

        # Create a transaction record
        Transaction.objects.create(
            user=self,
            transaction_type="Withdrawal",
            amount=-points,
            description=description or 'Points withdrawn from account')
     
class Preference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preference')
    savings_holders = models.JSONField(default=list)
    investment_holders = models.JSONField(default=list)
    fixed_asset_holders = models.JSONField(default=list)
    stock_holders = models.JSONField(default=list)
    business_holders = models.JSONField(default=list)


    def __str__(self):
        return f'{self.user.username} preference'
       
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ("Deposit", "Deposit"),
        ("Withdrawal", "Withdrawal"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.IntegerField()  # Can be positive (Deposit) or negative (Withdrawal)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type}: {self.amount} points on {self.timestamp}"

