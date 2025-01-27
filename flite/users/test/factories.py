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


