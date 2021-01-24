from django.urls import path
from django.conf.urls import url
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('courses/<int:subCategory_id>', views.courses, name="courses"),
    path('subcategory/<int:category_id>', views.subCategoriesView, name="subcategories"),
    path('details/<int:course_id>', views.details, name="course_details"),
    path('login/', views.loginPage, name="login"),
    path('ajax_autocomplete/', views.autocompleteModel, name="autocomplete"),
    path('contact/', views.contactView.as_view(), name="contact"),
    path('register/', views.registerPage, name="register"),
    path('partner/', views.registerPage, name="register"),
    path(r'add_to_cart/', views.add_to_cart, name="add_to_cart"),
    path(r'uprofile/', views.uprofile, name="user_profile"),
    path(r'sprofile/', views.sprofile, name="seller_profile"),
    path(r'sprofile_courses/', views.sprofile_courses, name="sprofile_courses"),
    url(r'^order_details/$', views.order_details, name="order_details"),
    url(r'^logout_view/$', views.logout_view, name="logout_view"),
    url(r'^success/$', views.success, name='purchase_success'),
    url(r'^item/delete/(?P<item_id>[-\w]+)/$', views.delete_from_cart, name='delete_item'),
    url(r'^checkout/$', views.checkout, name='checkout'),
    url(r'^update-transaction/(?P<token>[-\w]+)/$', views.update_transaction_records,
        name='update_records')

    # path('login/', views.loginPage, name="login"),
    # path('logout/', views.logoutUser, name="logout"),
    # path('user/', views.userPage, name="user-page"),
    # path('accounts/', views.accountSettings, name="accounts"),
    # path('customer/<str:pk_test>/', views.customer, name="customer"),
    # path('create_order/<str:pk>/', views.createOrder, name="create_order"),
    # path('update_order/<str:pk>/', views.updateOrder, name="update_order"),
    # path('delete_order/<str:pk>/', views.deleteOrder, name="delete_order"),
]
