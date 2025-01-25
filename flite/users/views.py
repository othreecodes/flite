from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import AllBanks, Bank, Transaction, User, NewUserPhoneVerification, Balance
from .permissions import IsUserOrReadOnly
from .serializers import CreateUserSerializer, TransactionSerializer, UserSerializer, SendNewPhonenumberSerializer
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
    serializer_class = TransactionSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post', 'head', 'options']

    @action(detail=True, methods=['post'], url_path='deposits', url_name='deposit')
    def deposit(self, request, *args, **kwargs):
        """
        Deposit funds into a user's account.
        """
        user = self.get_object()  # Get the user making the request
        balance = Balance.objects.filter(owner=user).first()

        # Validate input using a TransactionSerializer
        serializer = TransactionSerializer(data=request.data)
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
                reference=f"DEP-{random.randint(100000, 999999)}",  # Unique reference
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

        # Validate input using a TransactionSerializer
        serializer = TransactionSerializer(data=request.data)
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
                reference=f"WDL-{random.randint(100000, 999999)}",  # Unique reference
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

