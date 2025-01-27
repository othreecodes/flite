import uuid
import factory


class UserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'users.User'
        django_get_or_create = ('username',)

    id = factory.Faker('uuid4')
    username = factory.Sequence(lambda n: f'testuser{n}')
    password = factory.Faker('password', length=10, special_chars=True, digits=True,
                             upper_case=True, lower_case=True)
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False

# # Created Balance Factory
class BalanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'users.Balance'

    owner = factory.SubFactory(UserFactory)  # Link to UserFactory
    available_balance = factory.Faker('random_int', min=1000, max=10000)  # Random balance between 1000 and 10000
    book_balance = factory.LazyAttribute(lambda o: o.available_balance)  # Same as available balance initially
    active = True  # Assume balance is always active


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'users.Transaction'

    owner = factory.SubFactory(UserFactory)  # Link to UserFactory
    reference = factory.LazyFunction(lambda: uuid.uuid4().hex[:8])
    status = 'success'  # Assume transaction is always successful
    amount = factory.Faker('random_int', min=-1000, max=1000)  # Random amount between -1000 and 1000
    new_balance = factory.Faker('pyfloat', left_digits=4, right_digits=2, positive=True, min_value=10, max_value=10000)  # Random float value between 0 and 10000