from django.contrib.auth.forms import  UserCreationForm
from .models import Clients


class ClientsForm(UserCreationForm):
    class Meta:
        model = Clients
        fields = ['username','password1','password2','client_short','role_type']
