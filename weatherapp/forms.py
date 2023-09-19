from django.contrib.auth.forms import  UserCreationForm, UserChangeForm
from .models import Clients


class ClientsForm(UserCreationForm):
    class Meta:
        model = Clients
        fields = ['username','email','password1','password2','client_short','role_type']

class ClientChangeForm(UserChangeForm):
    class Meta:
        model = Clients
        fields = ['username','email','client_short','role_type']
