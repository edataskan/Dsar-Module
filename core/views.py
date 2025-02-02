from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from .forms import CheckoutForm, CouponForm, CustomLoginForm, DataControllerLoginForm, DataProcessorLoginForm, PublicKeyForm, RefundForm, CustomPasswordChangeForm, AddressForm, TestForm, UserLoginForm, UsernameChangeForm, SignUpForm, DSARForm, PhoneVerificationForm
from .models import CustomUser, DSARRequest, Item, OrderItem, Order, BillingAddress, Payment, Coupon, Refund, Category, Address, City, Country
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.contrib.auth.forms import PasswordChangeForm, UserChangeForm
from django.contrib.auth import update_session_auth_hash, login as auth_login, authenticate, login, logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from social_core.pipeline.partial import partial
from twilio.rest import Client
from django import forms
from datetime import datetime, timedelta
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.functional import SimpleLazyObject
from django.contrib.messages.views import SuccessMessageMixin

import random
import string
import stripe
import gnupg
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

class CustomPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'account/change_password.html'
    form_class = CustomPasswordChangeForm
    success_url = reverse_lazy('core:home')
    success_message = "Your password was successfully updated!"

    def form_invalid(self, form):
        for error in form.non_field_errors():
            messages.error(self.request, error)
        for field in form:
            for error in field.errors:
                messages.error(self.request, error)
        return super().form_invalid(form)

class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False
            }
            return render(self.request, "payment.html", context)
        else:
            messages.warning(
                self.request, "u have not added a billing address")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total() * 100)
        try:
            charge = stripe.Charge.create(
                amount=amount,  
                currency="usd",
                source=token
            )
            
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            
            order.ordered = True
            order.payment = payment
            
            order.ref_code = create_ref_code()
            order.save()

            messages.success(self.request, "Order was successful")
            return redirect("/")

        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.error(self.request, f"{err.get('message')}")
            return redirect("/")

        except stripe.error.RateLimitError as e:
    
            messages.error(self.request, "RateLimitError")
            return redirect("/")

        except stripe.error.InvalidRequestError as e:
            
            messages.error(self.request, "Invalid parameters")
            return redirect("/")

        except stripe.error.AuthenticationError as e:
            
            messages.error(self.request, "Not Authentication")
            return redirect("/")

        except stripe.error.APIConnectionError as e:
            
            messages.error(self.request, "Network Error")
            return redirect("/")

        except stripe.error.StripeError as e:
            
            messages.error(self.request, "Something went wrong")
            return redirect("/")

        except Exception as e:
            
            print(f"Ciddi Hata: {str(e)}")
            messages.error(self.request, "Serious Error occurred")
            return redirect("/")


class HomeView(ListView):
    template_name = "index.html"
    queryset = Item.objects.filter(is_active=True)
    context_object_name = 'items'
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().get(request, *args, **kwargs)

        dsar_request = DSARRequest.objects.filter(user=request.user).last()
        cu = CustomUser.objects.filter(id=request.user.id).first()
        
        public_key = cu.public_key if cu else None  
        

        if dsar_request and dsar_request.approvedbydc and public_key is None:
            messages.warning(request, 'You need to upload your public key.')
            return redirect('core:upload_public_key', request_id=dsar_request.id)

        return super().get(request, *args, **kwargs)

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order")
            return redirect("/")

class ShopView(ListView):
    model = Item
    paginate_by = 6
    template_name = "shop.html"

class ItemDetailView(DetailView):
    model = Item
    template_name = "product-detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_products'] = Item.objects.filter(category=self.object.category).exclude(id=self.object.id)[:8]
        return context


class CategoryView(View):
    def get(self, *args, **kwargs):
        category = Category.objects.get(slug=self.kwargs['slug'])
        item = Item.objects.filter(category=category, is_active=True)
        context = {
            'object_list': item,
            'category_title': category,
            'category_description': category.description,
            'category_image': category.image
        }
        return render(self.request, "category.html", context)
class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:

            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }
            return render(self.request, "checkout.html", context)

        except ObjectDoesNotExist:

            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):

        form = CheckoutForm(self.request.POST or None, country_id=self.request.POST.get('country'))
        print("Form data:", self.request.POST)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                city = form.cleaned_data.get('city')  
                zip_code = form.cleaned_data.get('zip')
                payment_option = form.cleaned_data.get('payment_option')

                if city is None:
                    messages.error(self.request, "Please select a city.")
                    return self.get(*args, **kwargs)  

                billing_address = BillingAddress(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    city=city,  
                    zip_code=zip_code,
                    address_type='B'
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()

                if payment_option == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(self.request, "Invalid payment option selected")
                    return redirect('core:checkout')

            else:
                print(form.errors)  
                messages.error(self.request, "Form is not valid")
                return self.get(*args, **kwargs)  

        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order")
            return redirect("core:order-summary")


def home(request):
     context = {
         'items': Item.objects.all()
     }
     return render(request, "index.html", context)
def products(request):
     context = {
         'items': Item.objects.all()
     }
     return render(request, "product-detail.html", context)

def shop(request):
     context = {
         'items': Item.objects.all()
     }
     return render(request, "shop.html", context)

@login_required(login_url='core:login')
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "Item qty was updated.")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "Item was added to your cart.")
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "Item was added to your cart.")
    return redirect("core:order-summary")

@login_required(login_url='core:login')
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request, "Item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            
            messages.info(request, "Item was not in your cart.")
            return redirect("core:product", slug=slug)
    else:
        
        messages.info(request, "u don't have an active order.")
        return redirect("core:product", slug=slug)
    return redirect("core:product", slug=slug)

@login_required(login_url='core:login')
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item qty was updated.")
            return redirect("core:order-summary")
        else:
            
            messages.info(request, "Item was not in your cart.")
            return redirect("core:product", slug=slug)
    else:
        
        messages.info(request, "u don't have an active order.")
        return redirect("core:product", slug=slug)
    return redirect("core:product", slug=slug)

def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")

class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")

            except ObjectDoesNotExist:
                messages.info(request, "You do not have an active order")
                return redirect("core:checkout")

class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request was received")
                return redirect("core:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist")
                return redirect("core:request-refund")

class CustomPasswordResetView(auth_views.PasswordResetView):
    template_name = 'account/password_reset.html'
    email_template_name = 'account/password_reset_email.html'
    subject_template_name = 'account/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'account/password_reset_done.html'

class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'account/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'account/password_reset_complete.html'

@partial
def complete(*args, **kwargs):
    return redirect('SOCIAL_AUTH_LOGIN_REDIRECT_URL')


@login_required(login_url='core:login')
def profile(request):
    username_form = UsernameChangeForm(instance=request.user)
    address_form = AddressForm()

    if request.method == 'POST':
        if 'username_form' in request.POST:
            username_form = UsernameChangeForm(request.POST, instance=request.user)
            if username_form.is_valid():
                username_form.save()
                print("Username updated successfully")
            else:
                print(f"Username form errors: {username_form.errors}")
        elif 'address_form' in request.POST:
            address_form = AddressForm(request.POST)
            if address_form.is_valid():
                address = address_form.save(commit=False)
                address.user = request.user
                print(f"Saving address: {address}")  
                address.save()
                print("Address saved successfully")
            else:
                print(f"Address form errors: {address_form.errors}")  
    else:
        username_form = UsernameChangeForm(instance=request.user)
        address_form = AddressForm()

    addresses = Address.objects.filter(user=request.user)

    context = {
        'username_form': username_form,
        'address_form': address_form,
        'addresses': addresses,
    }
    return render(request, 'account/profile.html', context)

def add_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            new_address = form.save(commit=False)
            new_address.user = request.user
            new_address.save()
            return redirect('core:profile')
    else:
        form = AddressForm()
    return render(request, 'account/add_address.html', {'form': form})

def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)

    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return redirect('core:profile')  
    else:
        form = AddressForm(instance=address)

    return render(request, 'account/edit_address.html', {'form': form, 'address': address})

def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)
    if request.method == 'POST':
        address.delete()
        return redirect('core:profile')
        
    return render(request, 'account/delete_address.html', {'address': address})



def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            if user.usertype == 'user':
                    return redirect('core:home')
            elif user.usertype == 'data_processor':
                    return redirect('core:dsarrequest')
            elif user.usertype == 'data_controller':
                    return redirect('core:dsarcontrol')
            
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = SignUpForm()

    
    print(f"Request URL: {request.path}")  
    print(f"Form fields: {form.fields}")  
    print(f"Form instance: {form}")       

    return render(request, 'account/signup.html', {'form': form})
    
def test_form_view(request):
    form = TestForm()
    return render(request, 'account/test_form.html', {'form': form})

def test_signup(request):
    form = SignUpForm()
    return render(request, 'account/test_signup.html', {'form': form})

def load_cities(request):
    country_id = request.GET.get('country')
    if country_id:
        cities = City.objects.filter(country_id=country_id).order_by('name')
    else:
        cities = City.objects.none()

    return JsonResponse(list(cities.values('id', 'name')), safe=False)
def country_view(request):
    countries = Country.objects.all()
    return render(request, 'checkout.html', {'countries': countries})

def city_view(request):
    cities = City.objects.all()
    return render(request, 'checkout.html', {'cities': cities})


def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                print(f"Authenticated user type: {user.usertype}")
                if user.usertype == 'user':
                    return redirect('core:home')
                elif user.usertype == 'data_processor':
                    return redirect('core:dsarrequest')
                elif user.usertype == 'data_controller':
                    return redirect('core:dsarcontrol')
                else:
                    print(f"Unknown user type: {user.usertype}")
                    return redirect('login')  
            else:
                print("Authentication failed: invalid username or password")
                form.add_error(None, 'Invalid username or password')
        else:
            print("Form is not valid")
            print(form.errors)  
    else:
        form = CustomLoginForm()
    return render(request, 'account/login.html', {'form': form})


def generate_verification_code():
    return str(random.randint(100000, 999999))

@login_required(login_url='core:login')
def dsar_module(request):
    if request.method == 'POST':
        form = DSARForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            verification_code = generate_verification_code()
            request.session['verification_code'] = verification_code
            request.session['phone_number'] = phone_number

            try:
                recent_request = DSARRequest.objects.filter(
                    user=request.user,
                    phone_number=phone_number,
                    request_time__gte=timezone.now() - timezone.timedelta(minutes=10)
                ).exists()

                if not recent_request:
                    sms_body = f"Verification code: {verification_code}. Transaction process has started."
                    client.messages.create(
                        body=sms_body,
                        from_='+1 251 255 1032',
                        to=phone_number
                    )
                    messages.success(request, 'Your DSAR request has been received and transaction process has started. Enter the verification code sent to your phone number.')
                    return redirect('core:verify_phone')
                    
                else:
                    messages.info(request, 'You have recently submitted a request with this phone number.')
                    return redirect('core:home')

            except Exception as e:
                messages.error(request, f'Error: {e}')
    else:
        form = DSARForm()

    return render(request, 'account/dsar_module.html', {'form': form})


@login_required(login_url='core:login')
def verify_phone(request):
    if request.method == 'POST':
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            verification_code = form.cleaned_data['verification_code']
            phone_number = request.session.get('phone_number')
            stored_code = request.session.get('verification_code')

            if not phone_number:
                messages.error(request, 'Phone number not found. Please try again.')
                return redirect('core:dsar_module')

            if verification_code == stored_code:
                try:

                    DSARRequest.objects.create(
                        user=request.user,
                        first_name=request.user.first_name,
                        last_name=request.user.last_name,
                        phone_number=phone_number,
                        sms_sent=True
                    )
                    
                    messages.success(request, 'The first stage operations have been completed. It was sent to the data controller for approval by the system.')
                    
                    
                    return redirect('core:home')  

                except Exception as e:
                    messages.error(request, f'Error: {e}')
            else:
                messages.error(request, 'Invalid Verification Code')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = PhoneVerificationForm()

    return render(request, 'account/verify_phone.html', {'form': form})

from django.db import connection

def disable_safe_updates():
    with connection.cursor() as cursor:
        cursor.execute("SET SQL_SAFE_UPDATES = 0;")

def enable_safe_updates():
    with connection.cursor() as cursor:
        cursor.execute("SET SQL_SAFE_UPDATES = 1;")


@login_required(login_url='core:login')
def second_verify(request):
    form = PhoneVerificationForm(request.POST or None)
    print(f'Request method: {request.method}')
    user = request.user
    dsar_request = DSARRequest.objects.filter(user=user).latest('request_time')
    if request.method == 'POST':
        if form.is_valid():
            verification_code = form.cleaned_data['verification_code']
            phone_number = request.session.get('phone_number')
            second_verification_code = request.session.get('second_verification_code')

            print(f'Phone number in POST: {phone_number}')
            print(f'Second verification code in POST: {second_verification_code}')

            if not phone_number:
                messages.error(request, 'Phone number not found. Please try again.')
                return redirect('core:dsar_module')

            if verification_code == second_verification_code:
                messages.success(request, 'Verification code accepted.\nThe confirmation process for the data submission phase is completed.\nThe data will be sent to the e-mail address you have provided.')
                dsar_request.sms_sentt =True
                print(f'if sms sentt {dsar_request.sms_sentt} {dsar_request.request_time}')
                return redirect('core:home')

            try:
                verification_check = client.verify.services(verify_service_sid).verification_checks.create(
                    to=phone_number, code=verification_code
                )

                if verification_check.status == 'approved':
                    messages.success(request, 'The confirmation process for the data submission phase is completed.\nThe data will be sent to the e-mail address you have provided.')
                    user = request.user
                    dsar_request.sms_sentt =True
                    dsar_request.save()
                    print(f'try {dsar_request.sms_sentt}')
                    with transaction.atomic():
                        disable_safe_updates()
                        latest_dsar_request = DSARRequest.objects.filter(user=user).latest('request_time')
                        latest_dsar_request.verified = True
                        latest_dsar_request.save()
                        enable_safe_updates()

                    return redirect('core:home')
                else:
                    messages.error(request, 'Invalid Verification Code')
            except Exception as e:
                messages.error(request, f'Error: {e}')
    else:
        phone_number = request.session.get('phone_number')
        

        print(f'Phone number in GET: {phone_number}')
       
        if phone_number:
            if not dsar_request.sms_sentt:
                try:
                    second_verification_code = str(random.randint(100000, 999999))
                    custom_message = f'First stage operations have been completed. Verification code is: {second_verification_code}'

                    message = client.messages.create(
                        body=custom_message,
                        from_='+1 251 255 1032',
                        to=phone_number
                    )

                    print(f'SMS sent. SID: {message.sid}')
                    
                    request.session['second_verification_code'] = second_verification_code

                    print('SMS sent successfully')
                    dsar_request.sms_sentt = True
                    dsar_request.save()
                    print(f'if sms sentt {dsar_request.sms_sentt} {dsar_request.request_time}')
                except Exception as e:
                    messages.error(request, f'Error: {e}')
            else:
                print('SMS already sent, skipping SMS sending.')
                return redirect('core:home')
        
    return render(request, 'account/second_verify.html', {'form': form})

@login_required(login_url='core:login')
def dsarrequest_view(request):
    dsar_time = timezone.now() - timedelta(days=30)
    dsar_requests = DSARRequest.objects.filter(
        request_time__gte=dsar_time
    ).distinct()
    
    return render(request, 'account/dsarrequest.html', {'dsar_requests': dsar_requests})


@login_required(login_url='core:login')
def approve_dsarrequest(request, request_id):
    dsar_request = get_object_or_404(DSARRequest, id=request_id)
    dsar_request.approved = True

    dsar_request.save()
    messages.success(request, f'{dsar_request.first_name} {dsar_request.last_name} has been approved.')
    return redirect('core:dsarrequest')

@login_required(login_url='core:login')
def check_dsar_request_status(request):
    user = request.user

    try:
        dsar_request = DSARRequest.objects.filter(user=user).latest('request_time')
        approved = dsar_request.approved
        verified = dsar_request.verified
        sms_sent = dsar_request.sms_sent
        sms_sentt = dsar_request.sms_sentt
        
        print(f'sms sent {sms_sent}')
        print(f'sms sentt {sms_sentt} {dsar_request.first_name}')
        print(f'app {approved}')
        print(f'veri {verified}')
    except DSARRequest.DoesNotExist:
        approved = False
        verified = False
    except DSARRequest.MultipleObjectsReturned:
        dsar_request = DSARRequest.objects.filter(user=user).latest('request_time')
        approved = dsar_request.approved
        verified = dsar_request.verified
        sms_sent = dsar_request.sms_sent
        sms_sentt = dsar_request.sms_sentt
        print(f'approved: {approved}, verified: {verified}')

    
    
    if approved and not verified and not sms_sentt and sms_sent :
        if sms_sentt:
            # SMS has already been sent, do not redirect to second_verify
            return JsonResponse({'approved': True, 'verified': False, 'sms_sentt': True})
        
        request.session['dsar_status_checked'] = True
        return JsonResponse({'approved': True, 'verified': False, 'sms_sentt': False})
    
    return JsonResponse({'approved': False, 'verified': False, 'sms_sentt': False})

    
@login_required(login_url='core:login')
def dsarcontrol_view(request):

    #dsar_requests = DSARRequest.objects.filter(request_time__gte=timezone.now() - timedelta(hours=24))
    dsar_requests = DSARRequest.objects.all()
    return render(request, 'account/dsarcontrol.html', {'dsar_requests': dsar_requests})


from .utils import decrypt_message, encrypt_message  


@login_required(login_url='core:login')
def approve_dsarcontrol(request, request_id):
    dsar_request = get_object_or_404(DSARRequest, id=request_id)
    aa = dsar_request.user.id
    add = get_object_or_404(BillingAddress, id=aa)
    dsar_request.approvedbydc = True
    dsar_request.save()

    user_data = dsar_request.user
    user_public_key = user_data.public_key

    if user_public_key is None:
        messages.error(request, 'Kullanıcının public key bilgisi mevcut değil.')
        return redirect('core:dsarcontrol')

    else :
        cu = get_object_or_404(CustomUser, id=aa)

        subject = 'Your Data Has Been Encrypted and Sent Securely'
        message = f"""
        Encrypted Data Notification

        Dear {dsar_request.first_name} {dsar_request.last_name},

        Your data request has been successfully processed and encrypted. Below are the details of your data:

        Your First Name: {dsar_request.first_name}
        Your Last Name: {dsar_request.last_name}
        Your Password: {cu.password}
        Your Last Login: {cu.last_login}
        Your Email: {cu.email}
        Your Public Key: {cu.public_key}
        Your Data Request Time: {dsar_request.request_time.strftime('%B %d, %Y, %I:%M %p')}
        Your Street Address: {add.street_address}
        Your Apartment Address: {add.apartment_address}
                    
        The data has been encrypted and sent securely. If you have any questions or need further assistance, please feel free to contact us.

        Best regards,
        DSAR Module Team
        """
        print(f'Rendered Message: {message}')


        try:
            encrypted_message = encrypt_message(message, dsar_request.email, user_public_key)
        except ValueError as e:
            messages.error(request, f'Mesaj şifrelenemedi: {e}')
            return redirect('core:dsarcontrol')

        email = EmailMessage(
            subject,
            encrypted_message,
            'dsarmodule@gmail.com',
            [dsar_request.user.email]
        )
        email.content_subtype = 'plain'  

        email.send()
        messages.success(request, f'{dsar_request.first_name} {dsar_request.last_name} kullanıcısına e-posta gönderildi.')
        return redirect('core:dsarcontrol')


@login_required(login_url='core:login')
def send_encrypted_email(request, request_id):
    dsar_request = get_object_or_404(DSARRequest, id=request_id)
    aa = dsar_request.user.id
    add = get_object_or_404(BillingAddress, id=aa)
    cu = get_object_or_404(CustomUser, id=aa)

    subject = 'Your Data Has Been Encrypted and Sent Securely'
    message = f"""
    Encrypted Data Notification

    Dear {dsar_request.first_name} {dsar_request.last_name},

    Your data request has been successfully processed and encrypted. Below are the details of your data:

    Your First Name: {dsar_request.first_name}
    Your Last Name: {dsar_request.last_name}
    Your Password: {cu.password}
    Your Last Login: {cu.last_login}
    Your Email: {cu.email}
    Your Public Key: {cu.public_key}
    Your Data Request Time: {dsar_request.request_time.strftime('%B %d, %Y, %I:%M %p')}
    Your Street Address: {add.street_address}
    Your Apartment Address: {add.apartment_address}
                
    The data has been encrypted and sent securely. If you have any questions or need further assistance, please feel free to contact us.

    Best regards,
    DSAR Module Team
    """

    print(f'Message to encrypt: {message}')
    print(f'Rendered Message: {message}')
    public_key = dsar_request.user.public_key
    if not public_key:
        messages.error(request, 'Kullanıcının PGP anahtarı bulunamadı.')
        return redirect('core:dsarcontrol')

    gpg = gnupg.GPG(gpgbinary='C:\\Program Files (x86)\\GnuPG\\bin\\gpg.exe')
    
    
    import_result = gpg.import_keys(public_key)
    print(f'Import Result: {import_result}')

    keys = gpg.list_keys()
    print(f'Imported Keys: {keys}')

    if not import_result.count:
        messages.error(request, 'Kullanıcının PGP anahtarı geçersiz.')
        return redirect('core:dsarcontrol')

    encrypted_data = gpg.encrypt(message, dsar_request.user.email)
    print(f'Encryption Status: {encrypted_data.status}')
    print(f'Encrypted Message: {str(encrypted_data)}')
    print(f'Error Message: {encrypted_data.stderr}')

    if not encrypted_data.ok:
        messages.error(request, f'Mesaj şifrelenemedi: {encrypted_data.stderr}')
        return redirect('core:dsarcontrol')

    encrypted_message = str(encrypted_data)

    email = EmailMessage(
        subject,
        encrypted_message,
        'dsarmodule@gmail.com', 
        [dsar_request.user.email] 
    )
    email.content_subtype = 'plain'

    try:
        email.send()
        messages.success(request, f'{dsar_request.first_name} {dsar_request.last_name} kullanıcısına şifreli e-posta gönderildi.')
    except Exception as e:
        messages.error(request, f'E-posta gönderim hatası: {e}')

    return redirect('core:dsarcontrol')


@login_required(login_url='core:login')
def upload_public_key(request, request_id):
    dsar_request = get_object_or_404(DSARRequest, id=request_id)
    aa = dsar_request.user_id
    
    print('f{user.email}')
    add = get_object_or_404(BillingAddress, id=aa)
    cu= get_object_or_404(CustomUser, id=aa)

    if request.method == 'POST':
        form = PublicKeyForm(request.POST, request.FILES)
        if form.is_valid():
            public_key_file = request.FILES.get('public_key')
            if public_key_file:
                public_key_data = public_key_file.read().decode('utf-8')

                user = request.user
                user.public_key = public_key_data
                user.save()

                messages.success(request, 'Public key uploaded successfully.')

                
                subject = 'Your Data Has Been Encrypted and Sent Securely'
    
                message = f"""
                Encrypted Data Notification

                Dear {dsar_request.first_name} {dsar_request.last_name},

                Your data request has been successfully processed and encrypted. Below are the details of your data:

                Your First Name: {dsar_request.first_name}
                Your Last Name: {dsar_request.last_name}
                Your Password: {cu.password}
                Your Last Login: {cu.last_login}
                Your Email: {cu.email}
                Your Public Key: {cu.pk}
                Your Data Request Time: {dsar_request.request_time.strftime('%B %d, %Y, %I:%M %p')}
                Your Street Address: {add.street_address}
                Your Apartment Address: {add.apartment_address}
                

                The data has been encrypted and sent securely. If you have any questions or need further assistance, please feel free to contact us.

                Best regards,
                DSAR Module Team
                """

                gpg = gnupg.GPG(gpgbinary='C:\\Program Files (x86)\\GnuPG\\bin\\gpg.exe')

               
                import_result = gpg.import_keys(public_key_data)
                print(f'Import Result: {import_result}')

                
                keys = gpg.list_keys()
                print(f'Imported Keys: {keys}')

                if not import_result.count:
                    messages.error(request, 'Kullanıcının PGP anahtarı geçersiz.')
                    return redirect('core:home')

            
                encrypted_data = gpg.encrypt(message, user.email)
                print(f'Encryption Status: {encrypted_data.status}')
                print(f'Encrypted Message: {str(encrypted_data)}')

                if not encrypted_data.ok:
                    messages.error(request, f'Mesaj şifrelenemedi: {encrypted_data.stderr}')
                    return redirect('core:home')

                encrypted_message = str(encrypted_data)

                email = EmailMessage(
                    subject,
                    encrypted_message,  
                    'dsarmodule@gmail.com',  
                    [user.email]  
                )
                email.content_subtype = 'plain'  

                try:
                    email.send()
                    messages.success(request, f'{dsar_request.first_name} {dsar_request.last_name} kullanıcısına şifreli e-posta gönderildi.')
                except Exception as e:
                    messages.error(request, f'E-posta gönderim hatası: {e}')

                return redirect('core:home')
                
            else:
                messages.error(request, 'No file uploaded.')
        else:
            print(f'Form Errors: {form.errors}')
    else:
        form = PublicKeyForm()

    return render(request, 'upload_public_key.html', {'form': form})


@login_required(login_url='core:login')
def check_approval_and_upload_key(request, request_id):
    dsar_request = get_object_or_404(DSARRequest, id=request_id)
    user = request.user

    if dsar_request.approvedbydc and not user.public_key:
        if request.method == 'POST':
            form = PublicKeyForm(request.POST, request.FILES)
            if form.is_valid():
                public_key_file = request.FILES['public_key']
                public_key_data = public_key_file.read().decode('utf-8')

                user.public_key = public_key_data
                user.save()

                messages.success(request, 'PGP anahtarınız başarıyla yüklendi.')
                return redirect('core:home')
        else:
            form = PublicKeyForm()
        return render(request, 'upload_public_key.html', {'form': form})
    else:
        messages.error(request, 'DSAR talebiniz onaylanmamış veya zaten bir public key mevcut.')
        return redirect('core:home')


def inform(request):
    return render(request, 'inform.html')

def logout_view(request):
    return render(request, 'account/logout.html')