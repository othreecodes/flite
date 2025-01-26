import uuid
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import AllBanks, Bank, P2PTransfer, Transaction, User, NewUserPhoneVerification, Balance
from .permissions import IsUserOrReadOnly
from .serializers import BalanceSerializer, CreateUserSerializer, TransactionSerializer, TransferSerializer, UserSerializer, SendNewPhonenumberSerializer
from rest_framework.views import APIView
from . import utils
from django.db import transaction as db_transaction
import random

class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """
    Updates and retrieves user accounts
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id' # This is the field that will be used to look up the user
    permission_classes = (IsUserOrReadOnly, IsAuthenticated)
    http_method_names = ['get', 'post', 'head', 'options']
    
    # func retrieves specific user by 'id'
    def retrieve(self, request, *args, **kwargs)->Response:
        """
        Retrieve a specific user by 'id'.
        """
        user = self.get_object()  # Fetch the user by 'id'
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    # func retrieves all users in the database
    def list(self, request, *args, **kwargs) -> Response:
        """
        List all users.
        
        This endpoint returns a paginated list of users if 'page' and 'limit'
        query parameters are provided. Otherwise, it returns the full list of users.
        """
        users = self.get_queryset()  # Retrieve all user objects
        page = self.paginate_queryset(users)  # Apply pagination if query parameters are provided
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)  # Serialize paginated data
            return self.get_paginated_response(serializer.data)  # Return paginated response
        
        # If no pagination, serialize all users
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserCreateViewSet(mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    """
    Creates user accounts
    """
    queryset = User.objects.all()
    serializer_class = CreateUserSerializer
    permission_classes = (IsAuthenticated,)


class SendNewPhonenumberVerifyViewSet(mixins.CreateModelMixin,mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    Sending of verification code
    """
    queryset = NewUserPhoneVerification.objects.all()
    serializer_class = SendNewPhonenumberSerializer
    permission_classes = (AllowAny,)


    def update(self, request, pk=None,**kwargs):
        verification_object = self.get_object()
        code = request.data.get("code")

        if code is None:
            return Response({"message":"Request not successful"}, 400)    

        if verification_object.verification_code != code:
            return Response({"message":"Verification code is incorrect"}, 400)    

        code_status, msg = utils.validate_mobile_signup_sms(verification_object.phone_number, code)
        
        content = {
                'verification_code_status': str(code_status),
                'message': msg,
        }
        return Response(content, 200)    

# Deposit funds into a user's account
class TransactionViewSet(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    """
    Updates and retrieves user accounts
    """
    queryset = User.objects.all()
    serializer_class = TransferSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post', 'head', 'options']

    @action(detail=True, methods=['post'], url_path='deposits', url_name='deposit')
    def deposit(self, request, *args, **kwargs):
        """
        Deposit funds into a user's account.
        """
        user = self.get_object()  # Get the user making the request
        balance = Balance.objects.filter(owner=user).first()

        # Validate input using a TransferSerializer
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deposit_amount = serializer.validated_data['amount']

        if deposit_amount <= 0:
            return Response({"error": "Deposit amount must be greater than zero"}, status=status.HTTP_400_BAD_REQUEST)

        if not balance.active:
            return Response({"error": "User account is not active for deposits"}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure atomicity
        with db_transaction.atomic():
            # Update the balance
            balance.book_balance += deposit_amount
            balance.available_balance += deposit_amount
            balance.save()

            # Create a transaction record
            transaction = Transaction.objects.create(
                owner=user,
                reference=f"DEP-{uuid.uuid4().hex[:8]}",  # Unique reference
                status="Successful",
                amount=deposit_amount,
                new_balance=balance.book_balance,
            )

        # Return a response with transaction details
        return Response({
            "message": "Deposit successful",
            "new_balance": balance.book_balance,
            "transaction_reference": transaction.reference
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='withdrawals', url_name='withdraw')
    def withdraw(self, request, *args, **kwargs):
        """
        Withdraw funds from a user's account.
        """
        user = self.get_object()  # Get the user making the request
        balance = Balance.objects.filter(owner=user).first()

        if not balance:
            return Response({"error": "Balance account not found."}, status=status.HTTP_404_NOT_FOUND)

        # Validate input using a TransferSerializer
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        withdrawal_amount = serializer.validated_data['amount']

        if withdrawal_amount <= 0:
            return Response({"error": "Withdrawal amount must be greater than zero"}, status=status.HTTP_400_BAD_REQUEST)

        if not balance.active:
            return Response({"error": "User account is not active for withdrawals"}, status=status.HTTP_400_BAD_REQUEST)

        if balance.available_balance < withdrawal_amount:
            return Response({"error": "Insufficient funds"}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure atomicity
        with db_transaction.atomic():
            # Update the balance
            balance.book_balance -= withdrawal_amount
            balance.available_balance -= withdrawal_amount
            balance.save()

            # Create a transaction record
            transaction = Transaction.objects.create(
                owner=user,
                reference=f"WDL-{uuid.uuid4().hex[:8]}",  # Unique reference
                status="Successful",
                amount=-withdrawal_amount,  # Negative to indicate withdrawal
                new_balance=balance.book_balance,
            )

        # Return a response with transaction details
        return Response({
            "message": "Withdrawal successful",
            "new_balance": balance.book_balance,
            "transaction_reference": transaction.reference
        }, status=status.HTTP_201_CREATED)

class TransferView(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """
    Handles account-related operations:
    1. Money transfers between accounts.
    2. Retrieve a paginated list of transactions for a given account.
    3. Retrieve a specific transaction by ID.
    """
    queryset = User.objects.all()
    serializer_class = TransferSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post', 'head', 'options']
    
    @action(detail=True, methods=['get', 'post'], url_path='transfers/(?P<recipient_account_id>[^/.]+)', url_name='transfer')
    def transfer(self, request, pk=None, recipient_account_id=None):
        """
        Transfer funds from sender's account to recipient's account.
        """
        sender = self.get_object()  # Sender account based on pk

        # Fetch sender balance
        sender_balance = Balance.objects.filter(owner=sender).first()
        if not sender_balance:
            return Response({"error": "Sender account balance not found."}, status=status.HTTP_404_NOT_FOUND)

        recipient = User.objects.filter(id=recipient_account_id).first()
        if not recipient:
            return Response({"error": "Recipient account not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch recipient balance
        recipient_balance = Balance.objects.filter(owner=recipient).first()
        if not recipient_balance:
            return Response({"error": "Recipient account balance not found."}, status=status.HTTP_404_NOT_FOUND)

        # Validate transfer amount using a serializer
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transfer_amount = serializer.validated_data['amount']

        if transfer_amount <= 0:
            return Response({"error": "Transfer amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

        if sender_balance.available_balance < transfer_amount:
            return Response({"error": "Insufficient funds."}, status=status.HTTP_400_BAD_REQUEST)

        # Begin the transfer within a transaction block
        with db_transaction.atomic():
            # Update sender balance
            sender_balance.available_balance -= transfer_amount
            sender_balance.book_balance -= transfer_amount
            sender_balance.save()

            # Update recipient balance
            recipient_balance.available_balance += transfer_amount
            recipient_balance.book_balance += transfer_amount
            recipient_balance.save()

            # Create transaction records for both sender and recipient
            sender_transaction = P2PTransfer.objects.create(
                owner=sender,  # Add this line to set the owner
                sender=sender,
                receipient=recipient,
                reference=f"TRF-{uuid.uuid4().hex[:8]}",
                status="Successful",
                amount=-transfer_amount,  # Negative to indicate transfer
                new_balance=sender_balance.book_balance,
            )

            recipient_transaction = P2PTransfer.objects.create(
                owner=recipient,  # Add this line to set the owner
                sender=sender,
                receipient=recipient,
                reference=f"TRF-{uuid.uuid4().hex[:8]}",
                status="Successful",
                amount=transfer_amount,
                new_balance=recipient_balance.book_balance,
            )

        return Response({
            "message": "Transfer successful",
            "sender_new_balance": sender_balance.book_balance,
            "recipient_new_balance": recipient_balance.book_balance,
            "transaction_reference": sender_transaction.reference
        }, status=status.HTTP_201_CREATED)

class TransactionDetailView(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """
    Handles account-related operations:
    1. Money transfers between accounts.
    2. Retrieve a paginated list of transactions for a given account.
    3. Retrieve a specific transaction by ID.
    """
    queryset = User.objects.all()
    serializer_class = TransferSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post', 'head', 'options']
    
    @action(detail=True, methods=['get'], url_path='transactions', url_name='transactions-list')
    def list_transactions(self, request, pk=None):
        """
        List transactions for a given account, paginated.
        """
        user = self.get_object()  # Get the user account using pk
        # Fetch all transactions associated with the user
        transactions = Transaction.objects.filter(owner=user)

        # Apply pagination to the result
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = TransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # If no pagination is applied, return the full list of transactions
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='transactions/(?P<transaction_id>[^/.]+)', url_name='transaction-detail')
    def transaction_detail(self, request, pk=None, transaction_id=None):
        """
        Retrieve details of a specific transaction.
        """
        transaction = Transaction.objects.filter(id=transaction_id).first()
        if not transaction:
            return Response({"error": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = TransactionSerializer(transaction)
        return Response(serializer.data)
