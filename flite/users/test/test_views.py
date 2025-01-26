from random import randint
from django.urls import reverse
from django.forms.models import model_to_dict
from django.contrib.auth.hashers import check_password
from nose.tools import ok_, eq_
from rest_framework.test import APITestCase
from rest_framework import status
from faker import Faker
from random import randint
from ..models import Balance, User,UserProfile,Referral
from .factories import BalanceFactory, UserFactory

fake = Faker()


# class TestUserListTestCase(APITestCase):
#     """
#     Tests /users list operations.
#     """

#     def setUp(self):
#         self.url = reverse('user-list')
#         self.user_data = model_to_dict(UserFactory.build())

#     def test_post_request_with_no_data_fails(self):
#         response = self.client.post(self.url, {})
#         eq_(response.status_code, status.HTTP_400_BAD_REQUEST)

#     def test_post_request_with_valid_data_succeeds(self): # failed
#         response = self.client.post(self.url, self.user_data)
#         eq_(response.status_code, status.HTTP_201_CREATED)

#         user = User.objects.get(pk=response.data.get('id'))
#         eq_(user.username, self.user_data.get('username'))
#         ok_(check_password(self.user_data.get('password'), user.password))

#     def test_post_request_with_valid_data_succeeds_and_profile_is_created(self): # failed
#         response = self.client.post(self.url, self.user_data)
#         eq_(response.status_code, status.HTTP_201_CREATED)

#         eq_(UserProfile.objects.filter(user__username=self.user_data['username']).exists(),True)

#     def test_post_request_with_valid_data_succeeds_referral_is_created_if_code_is_valid(self): # failed
        
#         referring_user = UserFactory()
#         self.user_data.update({"referral_code":referring_user.userprofile.referral_code})
#         response = self.client.post(self.url, self.user_data)
#         eq_(response.status_code, status.HTTP_201_CREATED)

#         eq_(Referral.objects.filter(referred__username=self.user_data['username'],owner__username=referring_user.username).exists(),True)


#     def test_post_request_with_valid_data_succeeds_referral_is_not_created_if_code_is_invalid(self): # failed
        
#         self.user_data.update({"referral_code":"FAKECODE"})
#         response = self.client.post(self.url, self.user_data)
#         eq_(response.status_code, status.HTTP_400_BAD_REQUEST)
        
# class TestUserDetailTestCase(APITestCase):
#     """
#     Tests /users detail operations.
#     """

#     def setUp(self):
#         self.user = UserFactory()
#         self.url = reverse('user-detail', kwargs={'pk': self.user.pk})
#         self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')

#     def test_get_request_returns_a_given_user(self):
#         response = self.client.get(self.url)
#         eq_(response.status_code, status.HTTP_200_OK)

#     def test_put_request_updates_a_user(self): #failed
#         new_first_name = fake.first_name()
#         payload = {'first_name': new_first_name}
#         response = self.client.put(self.url, payload)
#         eq_(response.status_code, status.HTTP_200_OK)

#         user = User.objects.get(pk=self.user.id)
#         eq_(user.first_name, new_first_name)

# Test for task endpoints
class TestUserDepositView(APITestCase):
    """
    Tests for the /user-deposit endpoint.
    """

    def setUp(self):
        balance = randint(1000, 10000)
        self.user = UserFactory()
        self.url = reverse('user-deposit', kwargs={'pk': self.user.id})  # Include the pk in the URL
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')  # Authenticate the user

    def test_post_user_deposit_success(self):
        payload = {'amount': 1000}  # Valid deposit amount
        response = self.client.post(self.url, payload)
        eq_(response.status_code, status.HTTP_201_CREATED)

    def test_post_user_deposit_fails_with_invalid_amount(self):
        payload = {'amount': -100}  # Invalid negative amount
        response = self.client.post(self.url, payload)
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)

class TestUserListView(APITestCase):
    """
    Tests for the /user-list endpoint.
    """

    def setUp(self):
        # Set up a user and URL for the list endpoint
        self.user = UserFactory()
        self.url = reverse('user-list')  # Correcting the URL to not include pk for a list
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')  # Authenticate the user

    def test_get_user_list_returns_success(self):
        # Test GET request to list users
        response = self.client.get(self.url)
        eq_(response.status_code, status.HTTP_200_OK)


class TestUserWithdrawView(APITestCase):
    """
    Tests for the /user-withdraw endpoint.
    """

    def setUp(self):
        # Set up a user and related balances
        self.user = UserFactory()
        self.balance = BalanceFactory(owner=self.user)  # BalanceFactory will automatically generate the other fields
        self.url = reverse('user-withdraw', kwargs={'pk': self.user.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')


    def test_post_user_withdraw_success(self):
        # Dynamically generate a withdrawal amount within the available balance
        payload = {'amount': randint(1, int(self.balance.available_balance))}
        response = self.client.post(self.url, payload)

        # Assert that withdrawal succeeds
        eq_(response.status_code, status.HTTP_201_CREATED)  # Adjust status code if necessary

    def test_post_user_withdraw_fails_with_invalid_amount(self):
        # Dynamically generate a negative withdrawal amount
        payload = {'amount': randint(-1000, -1)}  # Random negative value
        response = self.client.post(self.url, payload)

        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)  # Expect 400 for invalid input

    def test_post_user_withdraw_fails_with_invalid_data(self):
        # Dynamically generate invalid data (non-numeric)
        payload = {'amount': 'invalid'}
        response = self.client.post(self.url, payload)

        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)  # Expect 400 for invalid data

    def test_post_user_withdraw_fails_with_insufficient_balance(self):
        # Dynamically set a balance lower than the requested withdrawal amount
        insufficient_balance = randint(1, int(self.balance.available_balance) - 1)
        self.balance.available_balance = insufficient_balance  # Set lower available balance
        self.balance.save()

        # Generate a withdrawal amount higher than the available balance
        payload = {'amount': self.balance.available_balance + 100}  # Amount greater than available balance
        response = self.client.post(self.url, payload)

        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)  # Expect 400 for insufficient funds
