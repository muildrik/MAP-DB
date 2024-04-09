from django.forms import ModelForm
from results.models import LogMessage, UploadedImage, CustomUser
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm

class LogMessageForm(ModelForm):
    class Meta:
        model = LogMessage
        fields = ("message",)   # NOTE: the trailing comma is required

class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = ('username', 'email')

class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = CustomUser
        fields = ('username', 'email')

class ImageUploadForm(ModelForm):
    class Meta:
        model = UploadedImage
        fields = ("mongoid", "filename", "isactive", )

# class UploadDataFileForm(ModelForm):
#     class Meta: 
#         model = UploadDataFileModel
#         fields = '__all__'

# class CollectionForm(ModelForm):
#     class Meta: 
#         model = CollectionModel
#         fields = '__all__'
    
# class UploadFileForm(forms.Form):
    