from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Customer)
admin.site.register(Seller)
admin.site.register(Categories)
admin.site.register(Course)
admin.site.register(SellerCourses)
admin.site.register(SubCategories)
admin.site.register(Tag)
admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.register(Transaction)
