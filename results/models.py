# from typing import Collection
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, User

class LogMessage(models.Model):
    message = models.CharField(max_length=300)
    log_date = models.DateTimeField("date logged")

    def __str__(self):
        """Returns a string representation of a message."""
        date = timezone.localtime(self.log_date)
        return f"'{self.message}' logged on {date.strftime('%A, %d %B, %Y at %X')}"

class UploadedImage(models.Model):
    mongoid = models.CharField(max_length=50)
    added = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    filename = models.ImageField(default='/images/default.png', upload_to='images')
    isactive = models.BooleanField(default=False)

    def __str__(self):
        return self.mongoid

# class CollectionField(models.Model):
#     type_options = [
#         ('string', 'Text'),
#         ('integer', 'Number'),
#         ('boolean', 'Boolean'),
#         ('timestamp', 'Date')
#     ]
#     name = models.CharField(max_length=60, unique=True, error_messages={ 'unique' : 'Please pick a unique name for this field'})
#     type = models.CharField(max_length=9, choices=type_options, default='string')
#     max_length = models.IntegerField(null=True, blank=True, default=0, error_messages={ 'data_type' : 'Please provide a numeric value only' })
#     required = models.BooleanField(default=False)
#     index = models.BooleanField(default=True)
#     translate_key = models.BooleanField(default=True)
#     translate_val = models.BooleanField(default=True)
#     last_indexed = models.DateTimeField(auto_now_add=True, null=False, blank=False)
#     last_dropped = models.DateTimeField(auto_now_add=False, null=True, blank=True)
#     last_modified = models.DateTimeField(auto_now=True, null=False, blank=False)

#     def __str__(self):
#         return self.name, self.type, self.max_length, self.required, self.index, self.translate_key, self.translate_val

# class Indexed(models.Model):
#     field = models.ForeignKey(CollectionField, on_delete=models.CASCADE)
#     index_time = models.DateTimeField(auto_now_add=True, null=False, blank=False)

# class Dropped(models.Model):
#     field=models.ForeignKey(CollectionField, on_delete=models.CASCADE)
#     drop_time = models.DateTimeField(auto_now_add=True, null=False, blank=False)

# class CollectionModel(models.Model):
#     name = models.CharField(max_length=60, unique=True, error_messages={ 
#         'unique' : 'Your collection needs a unique name',
#         'required' : 'Your collection needs a unique name'
#     })
#     schema = models.ManyToManyField(CollectionField, null=True, blank=True)

#     def __str__(self):
#         return self.name, self.schema

# class UploadDataFileModel(models.Model):
#     name = models.CharField(max_length=60)
#     size = models.PositiveIntegerField
#     file = models.FileField(upload_to="media", null=True, blank=True)
#     collection = models.OneToOneField(CollectionModel, on_delete=models.CASCADE, default='data')

# class User(AbstractUser):
#     username = models.CharField(unique=True, max_length=256, blank=True)
#     email = models.EmailField(('email address'), unique=True)
#     full_name = models.CharField(max_length=256, blank=True)
#     bio = models.TextField(blank=True)
#     tagline = models.TextField(blank=True)
#     picture = models.ImageField(upload_to='images', blank=True)
        
#     def __str__(self):
#         return self.username


class CustomUser(AbstractUser):
    username = models.CharField(unique=True, max_length=256, blank=True)
    email = models.EmailField(('email address'), unique=True)
    full_name = models.CharField(max_length=256, blank=True)
    bio = models.TextField(blank=True)
    tagline = models.TextField(blank=True)
    picture = models.ImageField(upload_to='images', blank=True)
    
    def __str__(self):
        return self.username

# class CustomUser():

#     def create_user(self, email, password, **extra_fields):
#         email = self.normalize_email(email)
#         user = self.model(email=email, **extra_fields)
#         user.set_password(password)
#         user.save()