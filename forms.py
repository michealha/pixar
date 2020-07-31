from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User 
from accounts.models import Story, Image, Profile
import PIL

class SignUpForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={'placeholder': 'Username'}
        )
    )
    email = forms.CharField(
        widget=forms.EmailInput(
            attrs={'placeholder': 'Email'}
        )
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Password'}
        )
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Confirm password'}
        )
    )

    class Meta:
        model = User 
        fields = ['username', 'email', 'password1', 'password2']


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={'placeholder': 'Username'}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Password'}
        )
    )

class ChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Old password'}
        )
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'placeholder': 'New password'}
        )
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Confirm new password'}
        )
    )
    field_order = ['old_password', 'new_password1', 'new_password2']


class StoryForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.TextInput(
            attrs={'rows': 1}
        )
    )
    class Meta:
        model = Story 
        fields = ('text', )

class ImageForm(forms.ModelForm):
    file = forms.FileField()
    class Meta:
        model = Image 
        fields = ('file', )

class PhotoForm(forms.ModelForm):
    file = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={'multiple': True}
        )
    )
    class Meta:
        model = Image 
        fields = ('file', )


class ProfilePhotoForm(forms.ModelForm):
    x = forms.FloatField(widget=forms.HiddenInput())
    y = forms.FloatField(widget=forms.HiddenInput())
    width = forms.FloatField(widget=forms.HiddenInput())
    height = forms.FloatField(widget=forms.HiddenInput())

    class Meta:
        model = Profile 
        fields = ('avatar', 'x', 'y', 'width', 'height', )

    def save(self):
        photo = super(ProfilePhotoForm, self).save()
        x = self.cleaned_data.get('x')
        y = self.cleaned_data.get('y')
        w = self.cleaned_data.get('width')
        h = self.cleaned_data.get('height')

        image = PIL.Image.open(photo.avatar)
        cropped_image = image.crop((x, y, w+x, y+h))
        resized_image = cropped_image.resize((200, 200), PIL.Image.ANTIALIAS)
        resized_image.save(photo.avatar.path)

        return photo 