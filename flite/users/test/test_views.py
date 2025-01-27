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
from ..serializers import *
from django.db import transaction

fake = Faker()


class TestUserListTestCase(APITestCase):
    """
    Tests /users list operations.
    """

    def setUp(self):
        self.url = reverse('user-list')
        self.user_data = model_to_dict(UserFactory.build())
        self.admin_user = User.objects.create_superuser(username="admin", email="admin@gmail.com", password="adminpass")
        self.regular_user = User.objects.create_user(username="user", password="userpass")        

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

    def test_list_request_as_admin_succeeds(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), User.objects.count())

    def test_list_request_as_regular_user_succeeds(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['username'], self.regular_user.username)        

    def test_list_request_with_pagination(self):
        for i in range(10):
            User.objects.create_user(username=f'user{i}', password='password')

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('results' in response.data)
        self.assertTrue('count' in response.data)
        self.assertTrue('next' in response.data or 'previous' in response.data)
        self.assertEqual(response.data['count'], User.objects.count())        
    
        
class TestUserDetailTestCase(APITestCase):
    """
    Tests /users detail operations.
    """

    def setUp(self):
        self.user = UserFactory()
        self.other_user = UserFactory()        
        self.url = reverse('user-detail', kwargs={'pk': self.user.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')
        self.other_user_url = reverse('user-detail', kwargs={'pk': self.other_user.pk})        

    def test_get_request_returns_a_given_user(self):
        response = self.client.get(self.url)
        eq_(response.status_code, status.HTTP_200_OK)
        eq_(response.data['id'], self.user.id)

    def test_get_request_fails_for_other_user(self):
        response = self.client.get(self.other_user_url)
        eq_(response.status_code, status.HTTP_404_NOT_FOUND)

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
        Balance.objects.filter(owner=self.user).delete()     
        self.balance = Balance.objects.create(owner=self.user, available_balance=1000.00, book_balance=1000.00, old_balance=0.0)
        self.withdrawal_url = reverse('user_withdrawals', kwargs={'id': self.user.id}) 

    def test_successful_withdrawal(self):
        data = {'amount': 100.00}
        response = self.client.post(self.withdrawal_url, data, format='json')
        self.balance.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Withdrawal successful')
        self.assertEqual(self.balance.available_balance, 900.00)
        self.assertEqual(self.balance.book_balance, 900.00)
        self.assertEqual(self.balance.old_balance, 1000.00)
        self.assertTrue(Transaction.objects.filter(owner=self.user, amount=100.00, type='WITHDRAWAL').exists())

    def test_insufficient_funds(self):
        data = {'amount': 1100.00}
        response = self.client.post(self.withdrawal_url, data, format='json')
        self.balance.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Insufficient balance')
        self.assertEqual(self.balance.available_balance, 1000.00)
        self.assertEqual(self.balance.book_balance, 1000.00)
        self.assertFalse(Transaction.objects.filter(owner=self.user, amount=1100.00, type='WITHDRAWAL').exists())



class TransactionListViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='user', password='password')
        self.other_user = User.objects.create_user(username='other_user', password='password')
        self.client.force_authenticate(user=self.user)
        self.url = reverse('transactions', kwargs={'id': self.user.id})

        self.transactions = [
            Transaction.objects.create(owner=self.user, reference='ref1', amount=100.0, new_balance=900.0, type='TRANSFER'),
            Transaction.objects.create(owner=self.user, reference='ref2', amount=200.0, new_balance=700.0, type='TRANSFER'),
            Transaction.objects.create(owner=self.user, reference='ref3', amount=300.0, new_balance=400.0, type='TRANSFER')
        ]

    def test_get_transactions_successful(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], len(self.transactions))

        # Check if the transactions are serialized correctly
        serializer = TransactionSerializer(self.transactions, many=True)
        self.assertEqual(response.data['results'], serializer.data)

    def test_get_transactions_unauthorized(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['message'], "You are not authorized to view this user's transactions")

    def test_get_transactions_no_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_transactions_invalid_user(self):
        invalid_url = reverse('transactions', kwargs={'id': 'invalid_id'})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['message'], "You are not authorized to view this user's transactions")


class TransactionDetailViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='user', password='password')
        self.other_user = User.objects.create_user(username='other_user', password='password')
        self.client.force_authenticate(user=self.user)
        self.transaction = Transaction.objects.create(owner=self.user, reference='ref1', amount=100.0, new_balance=900.0, type='TRANSFER')
        self.url = reverse('transaction_detail', kwargs={'id': self.user.id, 'transaction_id': self.transaction.id})

    def test_get_transaction_successful(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the transaction is serialized correctly
        serializer = TransactionSerializer(self.transaction)
        self.assertEqual(response.data, serializer.data)

    def test_get_transaction_unauthorized(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['message'], "You are not authorized to view this user's transactions")

    def test_get_transaction_no_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_transaction_not_found(self):
        non_existent_transaction_id = uuid.uuid4() 
        invalid_url = reverse('transaction_detail', kwargs={'id': self.user.id, 'transaction_id': non_existent_transaction_id})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], "Transaction not found")


class TransferFundViewTest(APITestCase):
    def setUp(self):
        self.sender = User.objects.create_user(username="sender", password="password123")
        self.recipient = User.objects.create_user(username="recipient", password="password123")
        Balance.objects.filter(owner=self.sender).delete()     
        Balance.objects.filter(owner=self.recipient).delete()      

        self.sender_balance = Balance.objects.create(owner=self.sender, available_balance=1000, book_balance=1000)
        self.recipient_balance = Balance.objects.create(owner=self.recipient, available_balance=500, book_balance=500)
        self.url = reverse('transfer_funds', kwargs={'sender_account_id': self.sender.id, 'recipient_account_id': self.recipient.id})
        
        self.client.force_authenticate(user=self.sender)

    @transaction.atomic
    def test_successful_transfer(self):
        data = {"amount": 200}
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.sender_balance.refresh_from_db()
        self.recipient_balance.refresh_from_db()
        
        self.assertEqual(self.sender_balance.available_balance, 800)
        self.assertEqual(self.recipient_balance.available_balance, 700)
        

        self.assertEqual(Transaction.objects.filter(owner=self.sender, type="TRANSFER").count(), 1)
        self.assertEqual(Transaction.objects.filter(owner=self.recipient, type="RECEIVED").count(), 1)

    @transaction.atomic
    def test_insufficient_funds(self):
        data = {"amount": 2000}
        
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Insufficient funds", response.data["message"])

    @transaction.atomic
    def test_recipient_not_found(self):
        recipient_id = uuid.uuid4()
        url = f"/api/v1/account/{self.sender.id}/transfers/{recipient_id}/"
        data = {"amount": 200}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Not found", response.data["detail"])
