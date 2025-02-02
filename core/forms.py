from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from django.contrib.auth.forms import PasswordChangeForm, UserChangeForm, AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from .models import Address, Country, City, CustomUser
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'PayPal')
)



class CheckoutForm(forms.Form):
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': '1234 Main St',
        'class': 'form-control'
    }))
    apartment_address = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Apartment or suite',
        'class': 'form-control'
    }))
    country = forms.ModelChoiceField(queryset=Country.objects.all(), widget=forms.Select(attrs={
        'class': 'custom-select d-block w-100',
        'id': 'country-select'
    }), empty_label='(select country)')
    city = forms.ModelChoiceField(queryset=City.objects.none(), widget=forms.Select(attrs={
        'class': 'custom-select d-block w-100',
        'id': 'city-select'
    }), empty_label='(select city)')
    zip = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    same_shipping_address = forms.BooleanField(required=False)
    save_info = forms.BooleanField(required=False)
    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=[('P', 'PayPal'), ('S', 'Stripe')])
    
    def __init__(self, *args, **kwargs):
        country_id = kwargs.pop('country_id', None)
        super().__init__(*args, **kwargs)
        if country_id:
            self.fields['city'].queryset = City.objects.filter(country_id=country_id).order_by('name')
        else:
            self.fields['city'].queryset = City.objects.none()


class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code'
    }))


class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 4
    }))
    email = forms.EmailField()

    from django import forms
from .models import Payment

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['stripe_charge_id', 'amount', 'user']

    def clean_stripe_charge_id(self):
        stripe_charge_id = self.cleaned_data.get('stripe_charge_id')
        if not stripe_charge_id.isdigit():
            raise forms.ValidationError('Stripe charge ID must contain only digits.')
        return stripe_charge_id
    


class CustomPasswordChangeForm(PasswordChangeForm):
    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get("old_password")
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")
        
        
        
        return cleaned_data

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    usertype = forms.ChoiceField(choices=CustomUser.USER_TYPE_CHOICES)

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'usertype', 'password1', 'password2')

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    usertype = forms.ChoiceField(choices=CustomUser.USER_TYPE_CHOICES, required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'usertype', 'password1', 'password2')


class TestForm(forms.Form):
    usertype = forms.ChoiceField(choices=[('user', 'User'), ('data_processor', 'Data Processor')])
           
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['street_address', 'city', 'country', 'state', 'zip_code']

    country = forms.ModelChoiceField(queryset=Country.objects.all(), empty_label="Select Country")
    city = forms.ModelChoiceField(queryset=City.objects.all(), empty_label="Select City")

    def __init__(self, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        self.fields['country'].queryset = Country.objects.all()
        self.fields['city'].queryset = City.objects.all()
        
class UsernameChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']
        labels = {
            'username': 'New Username'
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

class DSARForm(forms.Form):
    phone_number = forms.CharField(max_length=15)


from django import forms

class PhoneVerificationForm(forms.Form):
    digit1 = forms.CharField(max_length=1, required=False, widget=forms.NumberInput(attrs={'maxlength': '1'}))
    digit2 = forms.CharField(max_length=1, required=False, widget=forms.NumberInput(attrs={'maxlength': '1'}))
    digit3 = forms.CharField(max_length=1, required=False, widget=forms.NumberInput(attrs={'maxlength': '1'}))
    digit4 = forms.CharField(max_length=1, required=False, widget=forms.NumberInput(attrs={'maxlength': '1'}))
    digit5 = forms.CharField(max_length=1, required=False, widget=forms.NumberInput(attrs={'maxlength': '1'}))
    digit6 = forms.CharField(max_length=1, required=False, widget=forms.NumberInput(attrs={'maxlength': '1'}))

    def clean(self):
        cleaned_data = super().clean()
        digits = [
            cleaned_data.get('digit1', ''),
            cleaned_data.get('digit2', ''),
            cleaned_data.get('digit3', ''),
            cleaned_data.get('digit4', ''),
            cleaned_data.get('digit5', ''),
            cleaned_data.get('digit6', '')
        ]
        verification_code = ''.join(digits)
        cleaned_data['verification_code'] = verification_code
        return cleaned_data


class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class DataProcessorLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)   

class DataControllerLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)  

CustomUser = get_user_model()

class CustomLoginForm(forms.Form):
    username = forms.CharField(max_length=254, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)


class PublicKeyForm(forms.Form):
    public_key = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['asc'])],
        required=True)