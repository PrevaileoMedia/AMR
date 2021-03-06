from datetime import datetime
import simplejson as simplejson
import stripe as stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.db.models import Q, Count
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.text import slugify
from django.views.generic import TemplateView

from .extras import generate_order_id, transact, generate_client_token

from .forms import CreateUserForm, AddCourseForm
from trainingyard.models import *
from collections import defaultdict

stripe.api_key = settings.STRIPE_SECRET_KEY


# currentId = 0


def home(request, data={}):
    group = ""
    if request.user.groups.all():
        group=request.user.groups.all()[0].name
    courses_qs = Categories.objects.all()
    return render(request, 'accounts/index.html', {"courses_qs": courses_qs, "group":group})


def subCategoriesView(request, category_id):
    grp = ""
    if request.user.groups.all():
        grp=request.user.groups.all()[0].name

    if category_id == 0:
        courses_qs = Categories.objects.all()
        return render(request, 'accounts/allcourses.html', {"courses_qs": courses_qs,"group":grp})
    else:
        category_qs = Categories.objects.get(pk=category_id)
        subcategory_qs = Course.objects.all()
        subcategoryNames_qs = SubCategories.objects.filter(category__id=category_id)
        return render(request, 'accounts/subcategory.html', {"subcategory_qs": subcategory_qs, "category": category_qs,
                                                             "subcategoryNames_qs": subcategoryNames_qs})


def courses(request, subCategory_id):
    courses_qs = Course.objects.filter(~Q(subCategory__id=subCategory_id)).all()
    return render(request, 'accounts/courses.html', {"courses_qs": courses_qs})


def details(request, course_id):
    course_details_qs = Course.objects.filter(id=course_id)
    seller_qs = Seller.objects.filter(course__id=course_details_qs[0].id)
    course_details_all_seller = Course.objects.filter(seller=seller_qs.first())
    print(course_details_all_seller)
    #print(SubCategories.objects.values("category"))#.annotate(Count("name")).all())
    categories = defaultdict(int)
    for obj in Categories.objects.all():
        for obj2 in SubCategories.objects.values("category"):
            if obj.id == obj2["category"]:
                categories[obj.name] += 1
        if not categories[obj.name]:
            categories[obj.name] = 0
    categories = dict(categories)
    return render(request, 'accounts/single.html',
                  {"course_details_qs": course_details_qs,
                   "seller_qs": seller_qs[0],
                   "course_id": course_id,
                   "course_details_all": course_details_all_seller,
                   "categories":categories})


def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.groups.all():
            login(request, user)
            context = ''
            course_details = []
            if user.groups.all()[0].name == "customer":
                context = "customer"
                try:
                    course_details = Order.objects.filter(owner__in=user)
                except:
                    course_details = []
                return redirect(uprofile)
                # render(request, 'accounts/user_profile.html', {"user": user, "course_details": course_details})
            else:
                context = "seller"
                try:
                    course_details = Course.objects.filter(seller__in=user)
                except:
                    course_details = []
                return redirect(sprofile)

            # if "login" in HttpResponseRedirect(request.META.get('HTTP_REFERER')):
            #     return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            # else:
            #     return render(request, 'accounts/index.html', {"context": context})
        else:
            messages.error(request, 'Username or password is incorrect')
    else:
        system_messages = messages.get_messages(request)
        for message in system_messages:
            pass
    return render(request, 'registration/login.html', {})


def registerPage(request):
    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            group = form.cleaned_data.get('group')
            group = Group.objects.get(name=group)
            user.groups.add(group)
            # Added username after video because of error returning customer name if not added
            print(str(group) + ' ----' + 'customer')
            if str(group) == "customer":
                Customer.objects.create(
                    user=user,
                    name=user.username,
                )
            else:
                Seller.objects.create(
                    user=user,
                    name=user.username,
                )

            messages.success(request, 'Account was created for ' + username)

            return redirect(loginPage)

    context = {'form': form}
    return render(request, 'registration/register.html', context)


def get_user_pending_order(request):
    user_profile = get_object_or_404(Customer, user=request.user)
    order = Order.objects.filter(owner=user_profile, is_ordered=False)
    if order.exists():
        return order[0]
    return 0


@login_required()
def add_to_cart(request):
    try:
        currentId = request.POST.get('item')
        request.COOKIES['item'] = currentId
    except:
        currentId = request.COOKIES['item']

    # get the user profile
    #user_profile = Customer.objects.all()#(user=request.user)
    user_profile = get_object_or_404(Customer, user=request.user)

    print(user_profile)
    # filter products by id
    # product = Course.objects.filter(id=request.POST.get('item', "id")).first()
    # items = Customer.objects.filter(courses=request.POST.get('item', "id"))
    product = Course.objects.filter(id=currentId).first()
    items = Customer.objects.filter(courses=currentId)
    iall = Customer.objects.filter(user=request.user)

    # check if the user already owns this product
    if items:
        print('You already own this ebook')
        messages.info(request, 'You already own this ebook')
        return redirect(reverse('login', kwargs={'course_id': request.POST.get('item', "")}))

    order_item, status = OrderItem.objects.get_or_create(product=product)
    user_order, status = Order.objects.get_or_create(owner=user_profile, is_ordered=False)
    user_order.items.add(order_item)

    if status:
        user_order.ref_code = generate_order_id()
        user_order.save()

    messages.info(request, "item added to cart")
    return redirect(order_details)


@login_required()
def delete_from_cart(request, item_id):
    item_to_delete = OrderItem.objects.filter(pk=item_id)
    if item_to_delete.exists():
        item_to_delete[0].delete()
        messages.info(request, "Item has been deleted")
        existing_order = get_user_pending_order(request)
        context = {
            'order': existing_order
        }
    return render(request, 'shopping_cart/order_summary.html', context)


@login_required()
def order_details(request, **kwargs):
    grp = ""
    if request.user.groups.all():
        grp=request.user.groups.all()[0].name

    existing_order = get_user_pending_order(request)
    print(existing_order)
    context = {
        'order': existing_order,
        'group': grp,
    }
    return render(request, 'shopping_cart/order_summary.html', context)


@login_required()
def checkout(request, **kwargs):
    grp = ""
    if request.user.groups.all():
        grp=request.user.groups.all()[0].name
    # client_token = generate_client_token()
    existing_order = get_user_pending_order(request)
    publishKey = settings.STRIPE_PUBLISHABLE_KEY
    if request.method == 'POST':
        token = request.POST.get('stripeToken', False)
        if token:
            try:
                charge = stripe.Charge.create(
                    amount=100 * existing_order.get_cart_total(),
                    currency='usd',
                    description='Example charge',
                    source=token,
                )

                return redirect(reverse('shopping_cart:update_records',
                                        kwargs={
                                            'token': token
                                        })
                                )
            except stripe.CardError as e:
                messages.info(request, "Your card has been declined.")
        else:
            result = transact({
                'amount': existing_order.get_cart_total(),
                'payment_method_nonce': request.POST['payment_method_nonce'],
                'options': {
                    "submit_for_settlement": True
                }
            })

            if result.is_success or result.transaction:
                return redirect(reverse('shopping_cart:update_records',
                                        kwargs={
                                            'token': result.transaction.id
                                        })
                                )
            else:
                for x in result.errors.deep_errors:
                    messages.info(request, x)
                return redirect(reverse('shopping_cart:checkout'))
        # result = transact({
        #          'amount': existing_order.get_cart_total(),
        #          'payment_method_nonce': request.POST['payment_method_nonce'],
        #          'options': {
        #              "submit_for_settlement": True
        #          }
        #      })
        #return redirect(reverse('shopping_cart:update_records',
        #                        kwargs={ 'token': result.transaction.id,'group':grp,}))

    context = {
        'order': existing_order,
        # 'client_token': client_token,
        'STRIPE_PUBLISHABLE_KEY': publishKey,
        'group':grp,
    }

    return render(request, 'shopping_cart/checkout.html', context)


@login_required()
def logout_view(request):
    logout(request)
    return redirect('home')


@login_required()
def uprofile(request):
    grp = ""
    if request.user.groups.all():
        grp=request.user.groups.all()[0].name
    user = Customer.objects.filter(user=request.user)
    course_details = Order.objects.filter(owner__in=user)
    Orders = {}
    for data in course_details:
        for data2 in data.items.all():
            Orders = Course.objects.filter(name=data2.product)
    return render(request, 'accounts/user_profile.html', {"user": user,
                                                          "course_details": Orders,
                                                          "group": grp})

@login_required()
def editCourse(request, course_id):
    course_details_qs = Course.objects.filter(id=course_id)
    return render(request, 'accounts/edit_courses.html', {"data": course_details_qs[0]})


@login_required()
def sprofile(request):
    grp = ""
    if request.user.groups.all():
        grp=request.user.groups.all()[0].name
    user1 = Seller.objects.filter(user=request.user)
    user = Seller.objects.get(user=request.user)
    course = Course.objects.filter(seller__in=user1)
    form = AddCourseForm()
    if request.user.is_authenticated:
        if request.method == "POST":
            if request.POST.get("profile"):
                print("im @ profile")
                user.name = request.POST.get('name')
                user.phone = request.POST.get('phone')
                user.email = request.POST.get('email')
                user.company = request.POST.get('company')
                user.about = request.POST.get('about')
                user.profile_pic = request.POST.get('profile_pic')
                user.save()

            if 'new_course' in request.POST:
                form = AddCourseForm(request.POST, request.FILES)
                id = request.POST.get('id')
                name = request.POST.get('name')
                seller = user
                print("====>>>>>>" + request.POST.get('subCategory'))
                subCategory = SubCategories.objects.get(id=request.POST.get('subCategory'))
                image = request.FILES['image']
                description = request.POST.get('description')
                courseAvailability = request.POST.get('courseAvailability')
                price = request.POST.get('price')
                level = request.POST.get('level')
                requirements = request.POST.get('requirements')
                # tags = Tag.objects.get(id=request.POST.get('tags'))
                newCourse = Course(id=id, name=name, seller=seller, subCategory=subCategory,
                                   image=image, description=description,
                                   courseAvailability=courseAvailability,
                                   price=price, level=level,
                                   requirements=requirements)
                newCourse.save()
                # newCourse.tags.set(tags)

            elif request.POST.get('edit_course'):
                print(request.POST.get('id'))
                courseE = Course.objects.get(seller=user, id=request.POST.get('id'))
                courseE.name = request.POST.get('name')
                courseE.seller = user
                courseE.subCategory = request.POST.get('subCategory')
                courseE.image = request.POST.get('image')
                courseE.description = request.POST.get('description')
                courseE.courseAvailability = request.POST.get('courseAvailability')
                courseE.price = request.POST.get('price')
                courseE.level = request.POST.get('level')
                courseE.requirements = request.POST.get('requirements')
                # courseE.tags = request.POST.get('tags')
                courseE.save()

    return render(request, 'accounts/sprofile_courses.html', {"seller_qs": user1[0],
                                                              "course_details_qs": course,
                                                              "form": form,
                                                              "group": grp})


@login_required()
def sprofile_courses(request):
    user1 = Seller.objects.filter(user=request.user)
    return render(request, 'accounts/sprofile_courses.html', {"seller_qs": user1[0]})


@login_required()
def update_transaction_records(request, token):
    # get the order being processed
    order_to_purchase = get_user_pending_order(request)

    # update the placed order
    order_to_purchase.is_ordered = True
    order_to_purchase.date_ordered = datetime.datetime.now()
    order_to_purchase.save()

    # get all items in the order - generates a queryset
    order_items = order_to_purchase.items.all()

    # update order items
    order_items.update(is_ordered=True, date_ordered=datetime.datetime.now())

    # Add products to user profile
    user_profile = get_object_or_404(Customer, user=request.user)
    # get the products from the items
    order_products = [item.product for item in order_items]
    user_profile.ebooks.add(*order_products)
    user_profile.save()

    # create a transaction
    transaction = Transaction(profile=request.user.profile,
                              token=token,
                              order_id=order_to_purchase.id,
                              amount=order_to_purchase.get_cart_total(),
                              success=True)
    # save the transcation (otherwise doesn't exist)
    transaction.save()

    # send an email to the customer
    # look at tutorial on how to send emails with sendgrid
    messages.info(request, "Thank you! Your purchase was successful!")
    return redirect(reverse('accounts:my_profile'))


def success(request, **kwargs):
    # a view signifying the transcation was successful
    return render(request, 'shopping_cart/purchase_success.html', {})


def contactView(request):
    group = ""
    if request.user.groups.all():
        group=request.user.groups.all()[0].name
    return render(request, 'accounts/contact.html', {"group":group})


def autocompleteModel(request):
    search_qs = Course.objects.all()
    results = []
    for r in search_qs:
        results.append(r.name)
    qs_json = serializers.serialize('json', search_qs)
    return HttpResponse(qs_json, content_type='application/json')