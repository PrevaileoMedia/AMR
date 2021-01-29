from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models


# Create your models here.
from star_ratings.models import Rating


class Customer(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    phone = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    profile_pic = models.ImageField(upload_to='static/images/profiles', default="profile1.png", null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    stripe_id = models.CharField(max_length=200, null=True, blank=True)
    courses = models.CharField(max_length=200, default='0')

    def __str__(self):
        return self.name


class Seller(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    phone = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    company = models.CharField(max_length=200, null=True)
    about = models.TextField(null=True)
    profile_pic = models.ImageField(upload_to='static/images/profiles', default="profile1.png", null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=200, null=True)

    def __str__(self):
        return self.name


class Categories(models.Model):
    name = models.CharField(max_length=200, null=True)
    image = models.ImageField(upload_to='static/images/categories', default="profile1.png", null=True, blank=True)

    def __str__(self):
        return self.name


class SubCategories(models.Model):
    name = models.CharField(max_length=200, null=True)
    category = models.ForeignKey(Categories, null=True, on_delete=models.SET_NULL)
    image = models.ImageField(upload_to='static/images/subcategories', default="profile1.png", null=True, blank=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    LEVEL = (
        ('Basic', 'Basic'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    )

    AVAILABILITY = (
        ('Online', 'Online'),
        ('Offline', 'Offline'),
        ('Both', 'Both'),
    )

    name = models.CharField(max_length=200, null=True)
    seller = models.ForeignKey(Seller, null=True, on_delete=models.SET_NULL)
    subCategory = models.ForeignKey(SubCategories, null=True, on_delete=models.SET_NULL)
    image = models.ImageField(upload_to='static/images/courses', default="profile1.png", null=True, blank=True)
    description = models.TextField(null=True)
    courseAvailability = models.CharField(max_length=200, null=True, choices=AVAILABILITY)
    price = models.FloatField(null=True)
    level = models.CharField(max_length=200, null=True, choices=LEVEL)
    requirements = models.TextField(null=True)
    tags = models.ManyToManyField(Tag)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    ratings = GenericRelation(Rating, related_query_name='foos')

    def __str__(self):
        return self.name

    class Meta:
        db_table = "Course"



class SellerCourses(models.Model):
    seller = models.ForeignKey(Seller, null=True, on_delete=models.SET_NULL)
    course = models.ForeignKey(Course, null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    price = models.FloatField(null=True)

    class Meta:
        db_table = "SellerCourses"


class OrderItem(models.Model):
    product = models.OneToOneField(Course, on_delete=models.SET_NULL, null=True)
    is_ordered = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now=True)
    date_ordered = models.DateTimeField(null=True)

    class Meta:
        db_table = "OrderItem"


class Order(models.Model):
    ref_code = models.CharField(max_length=15)
    owner = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    is_ordered = models.BooleanField(default=False)
    items = models.ManyToManyField(OrderItem)
    date_ordered = models.DateTimeField(auto_now=True)

    def get_cart_items(self):
        return self.items.all()

    def get_cart_total(self):
        return sum([item.product.price for item in self.items.all()])

    def __str__(self):
        return '{0} - {1}'.format(self.owner, self.ref_code)


class Transaction(models.Model):
    profile = models.ForeignKey(Customer, on_delete=models.CASCADE)
    token = models.CharField(max_length=120)
    order_id = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=100, decimal_places=2)
    success = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)

    def __str__(self):
        return self.order_id

    class Meta:
        ordering = ['-timestamp']


class Comments(models.Model):
    blogpost_connected = models.ForeignKey(
        Course, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(Customer, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, auto_now=False)

    def __str__(self):
        return str(self.author) + ', ' + self.blogpost_connected.title[:40]