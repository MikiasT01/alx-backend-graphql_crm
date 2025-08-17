import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')

import django
django.setup()

from crm.models import Customer, Product, Order

def seed_database():
    # Clear existing data
    Customer.objects.all().delete()
    Product.objects.all().delete()
    Order.objects.all().delete()

    # Seed Customers
    customers = [
        Customer(name="Alice", email="alice@example.com", phone="+1234567890"),
        Customer(name="Bob", email="bob@example.com", phone="123-456-7890"),
    ]
    Customer.objects.bulk_create(customers)

    # Seed Products
    products = [
        Product(name="Laptop", price=999.99, stock=10),
        Product(name="Mouse", price=29.99, stock=50),
    ]
    Product.objects.bulk_create(products)

    # Seed Order
    customer = Customer.objects.get(email="alice@example.com")
    order = Order.objects.create(customer=customer)
    order.products.set(Product.objects.all())
    order.total_amount = sum(p.price for p in order.products.all())
    order.save()

    print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database()