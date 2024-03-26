"""
Database models.
"""
import uuid
import os

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


def policy_image_file_path(instance, filename):
    """Generate file path for new policy image."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'policy', filename)


class UserManager(BaseUserManager):
    """Manager for Users."""

    def create_user(self, email, password=None, **extra_field):
        """Create, save and return a new user."""
        if not email:
            raise ValueError('User must have an email address.')
        user = self.model(email=self.normalize_email(email), **extra_field)
        # One-way password hashing
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extrafield):
        """Create and return a new superuser"""
        user = self.create_user(email, password, **extrafield)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the System."""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    objects = UserManager()

    # Field used for authentication
    USERNAME_FIELD = 'email'


class Company(models.Model):
    """Company in the System."""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)


class Tag(models.Model):
    """Tag for filtering policies."""

    CLAIM_STATUS_CHOICES = [
        ('RAISED', 'Raised'),
        ('IN_PROGRESS', 'In Progress'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]

    claim_status = models.CharField(
        max_length=15,
        choices=CLAIM_STATUS_CHOICES,
        default='RAISED',)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.get_claim_status_display()


class Policy(models.Model):
    """Policy object."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    POLICY_CHOICES = [
        ('None', "None"),
        ('VEHICLE', 'Vehicle'),
        ('EMPLOYMENT', 'Employment'),
        ('HEALTH', 'Health'),
        ('TRAVEL', 'Travel'),
    ]

    title = models.CharField(
        max_length=15,
        choices=POLICY_CHOICES,
        default='None',)
    policy_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False, unique=True)
    description = models.TextField(blank=True)
    startDate = models.DateField()
    endDate = models.DateField()
    premiumAmt = models.DecimalField(max_digits=6, decimal_places=2)
    sumAssured = models.DecimalField(max_digits=10, decimal_places=2)
    claimedAmt = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        """Ovride save method to generate a new UUID for policy_id"""
        if not self.policy_id:
            self.policy_id = uuid.uuid4()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Policy No.:{self.policy_id}"

    def clean(self):
        """Validate claimedAmt and endDate."""
        if self.claimedAmt > self.sumAssured:
            raise ValidationError(
                {'claimedAmt': 'Claimed amount cannot exceed sum assured.'})

        if self.endDate <= self.startDate:
            raise ValidationError(
                {'endDate': 'End date must be greater than start date.'})


class Claim(models.Model):
    """Claim for policies."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        default=1
    )
    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
    )

    claim_id = models.CharField(max_length=50, unique=True, editable=False)
    claimedAmt = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)])
    description = models.TextField(blank=True)

    image = models.ImageField(
        null=True,
        upload_to=policy_image_file_path
    )
    tags = models.ManyToManyField('Tag')

    def save(self, *args, **kwargs):

        if not self.claim_id:
            self.claim_id = f"{self.policy.policy_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Claim for Policy {self.id} by User {self.user.email}"
