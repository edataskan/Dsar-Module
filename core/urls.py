from django.urls import path
from .views import (
    CustomPasswordChangeView,
    CustomPasswordResetCompleteView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetDoneView,
    CustomPasswordResetView,
    ItemDetailView,
    HomeView,
    add_address,
    add_to_cart,
    check_approval_and_upload_key,
    delete_address,
    dsarcontrol_view,
    dsarrequest_view,
    edit_address,
    load_cities,
    login_view,
    logout_view,
    remove_from_cart,
    ShopView,
    OrderSummaryView,
    remove_single_item_from_cart,
    CheckoutView,
    PaymentView,
    AddCouponView,
    RequestRefundView,
    CategoryView,
    profile,
    second_verify,
    signup,
    test_form_view,
    test_signup,
    
)
from core import views

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('category/<slug:slug>/', CategoryView.as_view(), name='category'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('add_coupon/', AddCouponView.as_view(), name='add-coupon'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('shop/', ShopView.as_view(), name='shop'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('remove-item-from-cart/<slug>/', remove_single_item_from_cart,
         name='remove-single-item-from-cart'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('request-refund/', RequestRefundView.as_view(), name='request-refund'),
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('change-password/', CustomPasswordChangeView.as_view(), name='change_password'),
    path('profile/', views.profile, name='profile'),
    path('add_address/', views.add_address, name='add_address'),
    path('edit_address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('delete_address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('ajax/load-cities/', views.load_cities, name='ajax_load_cities'),
    path('signup/', signup, name='signup'),
    path('dsar-module/', views.dsar_module, name='dsar_module'),
    path('verify-phone/', views.verify_phone, name='verify_phone'),
    path('second-verify/', second_verify, name='second_verify'),
    path('test-signup/', test_signup, name='test_signup'),
    path('test-form/', test_form_view, name='test_form_view'),
    path('login/', login_view, name='login'), 
    path('dsarrequest/', views.dsarrequest_view, name='dsarrequest'),
    path('dsarcontrol/', views.dsarcontrol_view, name='dsarcontrol'),
    path('dsarrequest/approve/<int:request_id>/', views.approve_dsarrequest, name='approve_dsarrequest'),
    path('check-dsar-status/', views.check_dsar_request_status, name='check_dsar_request_status'),
    path('dsarcontrol/approve/<int:request_id>/', views.approve_dsarcontrol, name='approve_dsarcontrol'),
    path('approve/<int:request_id>/', views.approve_dsarcontrol, name='approve_dsarcontrol'),
    path('upload_public_key/<int:request_id>/', views.upload_public_key, name='upload_public_key'),
    path('check-approval/<int:request_id>/', check_approval_and_upload_key, name='check_approval_and_upload_key'),
    path('inform/', views.inform, name='inform'),
    path('logout/', logout_view, name='logout_page'),

]
