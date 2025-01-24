from django.urls import reverse
from django.forms.models import model_to_dict
from django.contrib.auth.hashers import check_password
from nose.tools import ok_, eq_
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from faker import Faker
from ..models import User,UserProfile,Referral
from .factories import UserFactory
from django.urls import reverse
from rest_framework import status
from flite.users.models import Balance, Transaction, User
import uuid

fake = Faker()


class TestUserListTestCase(APITestCase):
    """
    Tests /users list operations.
    """

    def setUp(self):
        self.url = reverse('user-list')
        self.user_data = model_to_dict(UserFactory.build())

    def test_post_request_with_no_data_fails(self):
        response = self.client.post(self.url, {})
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_request_with_valid_data_succeeds(self):
        response = self.client.post(self.url, self.user_data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(pk=response.data.get('id'))
        eq_(user.username, self.user_data.get('username'))
        ok_(check_password(self.user_data.get('password'), user.password))

    def test_post_request_with_valid_data_succeeds_and_profile_is_created(self):
        response = self.client.post(self.url, self.user_data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        eq_(UserProfile.objects.filter(user__username=self.user_data['username']).exists(),True)

    def test_post_request_with_valid_data_succeeds_referral_is_created_if_code_is_valid(self):
        
        referring_user = UserFactory()
        self.user_data.update({"referral_code":referring_user.userprofile.referral_code})
        response = self.client.post(self.url, self.user_data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        eq_(Referral.objects.filter(referred__username=self.user_data['username'],owner__username=referring_user.username).exists(),True)


    def test_post_request_with_valid_data_succeeds_referral_is_not_created_if_code_is_invalid(self):
        
        self.user_data.update({"referral_code":"FAKECODE"})
        response = self.client.post(self.url, self.user_data)
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)
        
class TestUserDetailTestCase(APITestCase):
    """
    Tests /users detail operations.
    """

    def setUp(self):
        self.user = UserFactory()
        self.url = reverse('user-detail', kwargs={'pk': self.user.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')

    def test_get_request_returns_a_given_user(self):
        response = self.client.get(self.url)
        eq_(response.status_code, status.HTTP_200_OK)

    def test_put_request_updates_a_user(self):
        new_first_name = fake.first_name()
        payload = {'first_name': new_first_name}
        response = self.client.put(self.url, payload)
        eq_(response.status_code, status.HTTP_200_OK)

        user = User.objects.get(pk=self.user.id)
        eq_(user.first_name, new_first_name)

class UserDepositsViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)
        self.url = reverse('user_deposits', kwargs={'id': self.user.id})

    def test_deposit_successful(self):
        # Check if the user already has a balance
        initial_balance = Balance.objects.filter(owner=self.user).first()
        initial_available_balance = initial_balance.available_balance if initial_balance else 0.0
        initial_book_balance = initial_balance.book_balance if initial_balance else 0.0

        data = {
            'amount': 100.0
        }
        response = self.client.post(self.url, data, format='json')

        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Deposit successful')
        self.assertEqual(response.data['status'], status.HTTP_201_CREATED)
        self.assertIn('available_balance', response.data)

        # Check if the balance was updated correctly
        updated_balance = Balance.objects.get(owner=self.user)
        self.assertEqual(updated_balance.available_balance, initial_available_balance + data['amount'])
        self.assertEqual(updated_balance.book_balance, initial_book_balance + data['amount'])

        # Check if the transaction was created correctly
        transaction = Transaction.objects.get(owner=self.user)
        self.assertEqual(transaction.amount, data['amount'])
        self.assertEqual(transaction.new_balance, updated_balance.available_balance)
        self.assertEqual(transaction.type, 'DEPOSIT')

    def test_deposit_invalid_amount(self):
        data = {
            'amount': 'invalid'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_deposit_missing_amount(self):
        data = {}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

class UserWithdrawalViewTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)
        self.balance = Balance.objects.create(owner=self.user, available_balance=1000.00, book_balance=1000.00)
        self.withdrawal_url = reverse('user_withdrawals', kwargs={'id': self.user.id})  # Update with your URL pattern name

    def test_successful_withdrawal(self):
        data = {'amount': 100.00}
        response = self.client.post(self.withdrawal_url, data, format='json')
        self.balance.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Withdrawal successful')
        self.assertEqual(self.balance.available_balance, 900.00)
        self.assertEqual(self.balance.book_balance, 900.00)
        self.assertTrue(Transaction.objects.filter(owner=self.user, amount=100.00, type='WITHDRAWAL').exists())

    def test_insufficient_funds(self):
        data = {'amount': 1100.00}
        response = self.client.post(self.withdrawal_url, data, format='json')
        self.balance.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Insufficient funds')
        self.assertEqual(self.balance.available_balance, 1000.00)
        self.assertEqual(self.balance.book_balance, 1000.00)
        self.assertFalse(Transaction.objects.filter(owner=self.user, amount=1100.00, type='WITHDRAWAL').exists())
