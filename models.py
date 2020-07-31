from django.db import models
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.template.defaultfilters import slugify 
from django.db.models import Count
from django.utils import timezone 
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage as storage 
from PIL import Image as Photo 
import os
try:
    from io import BytesIO
except:
    raise Exception("Could not import BytesIO")


class Account(models.Model):
    is_private = models.BooleanField(default=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

@receiver(post_save, sender=User)
def create_account(sender, instance, created, **kwargs):
    if created:
        Account.objects.create(user=instance)
    instance.account.save()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='followings', on_delete=models.CASCADE)
    followed = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    followed_at = models.DateTimeField(auto_now_add=True)

class Story(models.Model):
    posted_by = models.ForeignKey(User, related_name='stories', null=True, on_delete=models.CASCADE)
    posted_at = models.DateTimeField(auto_now_add=True, null=True)
    text = models.TextField(max_length=4000, blank=True, null=True)

    def get_images(self):
        return Image.objects.filter(story=self).order_by('-created_at')

    def owner_is_followed(self, instance):
        if Follow.objects.filter(followed=self.posted_by, follower=instance.user).exists():
            return True 
        else:
            return False 

    def __str__(self):
        return self.text 

    def get_total_likes(self):
        return Like.objects.filter(story=self).count()

    def count_all_comments(self):
        return Comment.objects.filter(story=self).count()

    def get_last_comment(self):
        return Comment.objects.filter(story=self).last()

    def get_posted_time(self):
        delta = timezone.now() - self.posted_at 
        minute = 60
        hour = 3600
        day = 86400
        if delta.seconds < minute:
            prefix = 's'
            time = delta.seconds 
        elif delta.seconds > minute  and delta.seconds < hour:
            prefix = 'm'
            time = delta.seconds // minute
        elif delta.seconds >  hour and delta.seconds < day:
            prefix = 'h'
            time = delta.seconds // hour
        return f"{time}{prefix}"


    def is_liked(self, instance):
        if Like.objects.filter(story=self, liker=instance.user).exists():
            return True
        else:
            return False 

class Image(models.Model):
    file = models.ImageField(upload_to='images/')
    thumbnail = models.ImageField(upload_to='thumbs/', blank=True, null=True)
    story = models.ForeignKey(Story, related_name='images', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    

class Like(models.Model):
    liker = models.ForeignKey(User, related_name='user_likes', on_delete=models.CASCADE)
    liked_at = models.DateTimeField(auto_now_add=True)
    story = models.ForeignKey(Story, related_name='likes', on_delete=models.CASCADE)


class Comment(models.Model):
    written_by = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    written_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField(max_length=4000)
    story = models.ForeignKey(Story, related_name='comments', on_delete=models.CASCADE)

    def str(self):
        return self.text 

    def get_written_time(self):
        delta = timezone.now() - self.written_at 
        minute = 60
        hour = 3600
        day = 86400
        if delta.seconds < 60:
            prefix = 's'
            time = delta.seconds 
        elif delta.seconds > minute and delta.seconds < hour:
            prefix = 'm'
            time = delta.seconds // minute
        elif delta.seconds > hour and delta.seconds < day:
            prefix = 'h'
            time = delta.seconds // day
        return f"{time}{prefix}"
