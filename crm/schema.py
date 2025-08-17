import graphene
from graphene_django.types import DjangoObjectType
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Customer, Product, Order
import re
from graphene import InputObjectType, List, String, Decimal, Int, ID

# DjangoObjectTypes for GraphQL types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer

class ProductType(DjangoObjectType):
    class Meta:
        model = Product

class OrderType(DjangoObjectType):
    class Meta:
        model = Order

# Input types
class CustomerInput(InputObjectType):
    name = String(required=True)
    email = String(required=True)
    phone = String(required=False)

class OrderInput(InputObjectType):
    customer_id = ID(required=True)
    product_ids = List(ID, required=True)
    order_date = String(required=False)

# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        # Validate phone format (e.g., +1234567890 or 123-456-7890)
        if input.phone and not re.match(r'^\+?\d{10,15}$|^\d{3}-\d{3}-\d{4}$', input.phone):
            raise ValidationError("Phone must be in format +1234567890 or 123-456-7890")

        # Check for unique email
        if Customer.objects.filter(email=input.email).exists():
            raise ValidationError("Email already exists")

        # Create customer
        customer = Customer(name=input.name, email=input.email, phone=input.phone)
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created successfully")

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        created_customers = []
        errors = []
        for item in input:
            try:
                if Customer.objects.filter(email=item.email).exists():
                    errors.append(f"Email {item.email} already exists")
                    continue
                if item.phone and not re.match(r'^\+?\d{10,15}$|^\d{3}-\d{3}-\d{4}$', item.phone):
                    errors.append(f"Invalid phone format for {item.name}")
                    continue
                customer = Customer(name=item.name, email=item.email, phone=item.phone)
                customer.save()
                created_customers.append(customer)
            except Exception as e:
                errors.append(f"Error creating {item.name}: {str(e)}")
        return BulkCreateCustomers(customers=created_customers, errors=errors)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = InputObjectType(
            name=String(required=True),
            price=Decimal(required=True),
            stock=Int(required=False, default_value=0)
        )

    product = graphene.Field(ProductType)

    @staticmethod
    def mutate(root, info, input):
        if input.price <= 0:
            raise ValidationError("Price must be positive")
        if input.stock < 0:
            raise ValidationError("Stock cannot be negative")
        product = Product(name=input.name, price=input.price, stock=input.stock)
        product.save()
        return CreateProduct(product=product)

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)

    @staticmethod
    def mutate(root, info, input):
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            raise ValidationError("Invalid customer ID")

        products = Product.objects.filter(id__in=input.product_ids)
        if not products.exists():
            raise ValidationError("No valid products selected")

        order = Order(customer=customer)
        order.save()
        order.products.set(products)
        order.total_amount = sum(p.price for p in products)
        order.save()
        return CreateOrder(order=order)

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()