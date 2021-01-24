from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.forms import ModelForm
from .models import Customer, Seller, Course
from django import forms

class CustomerForm(ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        exclude = ['user']


class CreateUserForm(UserCreationForm):
    group = forms.CharField(max_length=100)
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'group']


class SellerForm(ModelForm):
    class Meta:
        model = Seller
        fields = '__all__'
        exclude = ['user']

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(SellerForm, self).__init__(*args, **kwargs)


class AddCourseForm(ModelForm):
    class Meta:
        model = Course
        fields = '__all__'
        exclude = ['seller','tags', 'date_created']

        def __init__(self, user, *args, **kwargs):
            super(AddCourseForm, self).__init__(*args, **kwargs)

            self.fields['seller'] = forms.ChoiceField(
                choices=[(o.id, str(o)) for o in Course.objects.filter(user=user)]
            )
