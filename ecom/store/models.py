from django.db import models
import datetime

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "categories"
 
class Customer(models.Model):
    firstname = models.CharField(max_length=30)
    lastname = models.CharField(max_length=30)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=30)
    phone = models.CharField(max_length=17)
    def __str__(self):
        return f'{self.firstname}-{self.lastname}'

class Product(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(default=0,max_digits=6,decimal_places=2)
    category = models.ForeignKey(Category,on_delete=models.CASCADE,default=1)
    description = models.CharField(max_length=240,default="",
                                   null=True,blank=True)
    image = models.ImageField(upload_to='photos/')
    is_sale = models.BooleanField(default = False)
    sale_price = models.DecimalField(default=0,max_digits=6,decimal_places=2)

    def __str__(self):
        return self.name
    
class Order(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    address = models.CharField(max_length=100,default="",blank=True)
    phone = models.CharField(max_length=50,default="",blank=True)
    date = models.DateField(default=datetime.datetime.today())
    status = models.BooleanField(default=False)
    def __str__(self):
        return self.product

   

    

