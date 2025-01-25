from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import AllBanks, Bank, Transaction, User, NewUserPhoneVerification, Balance
from .permissions import IsUserOrReadOnly
from .serializers import CreateUserSerializer, DepositSerializer, UserSerializer, SendNewPhonenumberSerializer
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
    permission_classes = (IsUserOrReadOnly,)
    http_method_names = ['get', 'post', 'head', 'options']
    
    # func retrieves specific user by 'id'
    def retrieve(self, request, *args, **kwargs)->Response:
        """
        Retrieve a specific user by 'id'.
        """
        user = self.get_object()  # Fetch the user by 'id'
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    # func retrieves all users in the database
    def list(self, request, *args, **kwargs)->Response:
        """
        List all users.
        """
        users = self.get_queryset()
        page = self.paginate_queryset(users)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class BalanceViewSet(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    """
    Updates and retrieves user accounts
    """
    queryset = User.objects.all()
    serializer_class = DepositSerializer
    permission_classes = (AllowAny,)
    http_method_names = ['get', 'post', 'head', 'options']

    @action(detail=True, methods=['post'], url_path='deposits', url_name='deposit')
    def deposit(self, request, *args, **kwargs):
        """
        Deposit funds into a user's account.
        """
        user = self.get_object()  # Get the user making the request
        balance, _ = Balance.objects.get_or_create(owner=user)

        # Validate input using a DepositSerializer
        serializer = DepositSerializer(data=request.data)
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


class UserCreateViewSet(mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    """
    Creates user accounts
    """
    queryset = User.objects.all()
    serializer_class = CreateUserSerializer
    permission_classes = (AllowAny,)


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
