from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import User, NewUserPhoneVerification, Transaction, Balance
from .permissions import IsUserOrReadOnly
from .serializers import *
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.db import transaction
import uuid
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404

from . import utils

class UserPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'limit'
    max_page_size = 100

class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """
    Updates and retrieves user accounts
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsUserOrReadOnly,)

    def get_queryset(self):
        query = super().get_queryset()
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, "admin") or self.request.user.is_superuser: 
                return query
            return query.filter(id=self.request.user.id)
        return query.none()


class UserCreateViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """
    Creates user accounts
    """
    queryset = User.objects.all()
    serializer_class = CreateUserSerializer
    pagination_class = UserPagination
    permission_classes = (AllowAny,)

    def list(self, request, *args, **kwargs):
        """
        Lists users with pagination.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def get_queryset(self):
        query = super().get_queryset()
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, "admin") or self.request.user.is_superuser: 
                return query
            return query.filter(id=self.request.user.id)
        return query.none()

    
 

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

class UserDepositsView(GenericAPIView):
    queryset = Balance.objects.all()
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            amount = serializer.validated_data.get("amount")

            balance, created = Balance.objects.get_or_create(owner=user)

            # Update balances
            old_balance = balance.available_balance
            balance.available_balance += amount
            balance.book_balance += amount
            balance.save()

            # Create a transaction record
            Transaction.objects.create(
                owner=user,
                reference=str(uuid.uuid4()),
                amount=amount,
                new_balance=balance.available_balance,
                type= "DEPOSIT"
            )

            return Response(
                {
                    "message": "Deposit successful",
                    "status": status.HTTP_201_CREATED,
                    "old_balance": old_balance,
                    "available_balance": balance.available_balance,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {
                    "error": str(e),
                    "status": 400,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
       
class UserWithdrawalView(GenericAPIView):
    serializer_class = WithdrawalSerializer

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            serializer = WithdrawalSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            amount = serializer.validated_data["amount"]

            balance = Balance.objects.filter(owner=user).first()
            if not balance:
                raise Balance.DoesNotExist

            if amount > balance.available_balance:
                return Response(
                    {
                        "message": 'Insufficient balance',
                        "balance": balance.available_balance,
                        "amount": amount,
                        "status": status.HTTP_400_BAD_REQUEST
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            with transaction.atomic():
                print(f"Old Balance: {balance.old_balance}, New Balance: {balance.available_balance}")
                balance.old_balance = balance.available_balance
                balance.available_balance -= amount
                balance.book_balance -= amount
                balance.save()

                Transaction.objects.create(
                    owner=user,
                    reference=str(uuid.uuid4()),
                    amount=amount,
                    new_balance=balance.available_balance,
                    type="WITHDRAWAL"
                )
            return Response(
                {
                    "message": "Withdrawal successful",
                    "status": status.HTTP_200_OK,
                    "old_balance": balance.old_balance,
                    "available_balance": balance.available_balance
                }, status=status.HTTP_200_OK
            )
        except Balance.DoesNotExist:
            return Response(
                {
                    "message": "Balance record not found",
                    "status": status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    "message": str(e),
                    "status": status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST
            )

class TransferFundView(APIView):
    serializer_class = TransferFundSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, sender_account_id, recipient_account_id, *args, **kwargs):
        sender = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]

        recipient = get_object_or_404(User, id=recipient_account_id)
        sender_balance = Balance.objects.filter(owner=sender).first()
        recipient_balance = Balance.objects.filter(owner=recipient).first()

        if not sender_balance or not recipient_balance:
            return Response(
                {"message": "Balance records not found", "status": status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if sender_balance.available_balance < amount:
            return Response(
                {"message": "Insufficient funds", "status": status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                # Update balances
                sender_balance.old_balance = sender_balance.available_balance
                recipient_balance.old_balance = recipient_balance.available_balance

                sender_balance.available_balance -= amount
                sender_balance.book_balance -= amount
                recipient_balance.available_balance += amount
                recipient_balance.book_balance += amount

                sender_balance.save()
                recipient_balance.save()

                Transaction.objects.create(
                    owner=sender,
                    reference=str(uuid.uuid4()),
                    amount=amount,
                    new_balance=sender_balance.available_balance,
                    type="TRANSFER",
                )

                Transaction.objects.create(
                    owner=recipient,
                    reference=str(uuid.uuid4()),
                    amount=amount,
                    new_balance=recipient_balance.available_balance,
                    type="RECEIVED",
                )

            return Response(
                {
                    "message": "Transfer successful",
                    "status": status.HTTP_200_OK,
                    "sender_old_balance": sender_balance.old_balance,
                    "sender_new_balance": sender_balance.available_balance,
                    "recipient_old_balance": recipient_balance.old_balance,
                    "recipient_new_balance": recipient_balance.available_balance,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e), "status": status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST,
            )
   
class TransactionListView(GenericAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    # permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request, id, *args, **kwargs):
        try:
            user = request.user
            if str(user.id) != id:
                return Response(
                    {
                        "message": "You are not authorized to view this user's transactions",
                        "status": status.HTTP_403_FORBIDDEN
                    }, status=status.HTTP_403_FORBIDDEN
                )
            transactions = Transaction.objects.filter(owner=user).order_by('created_at')  # Order by created_at
            paginator = self.pagination_class()
            paginated_transactions = paginator.paginate_queryset(transactions, request)

            # Serialize the paginated transactions
            serializer = self.get_serializer(paginated_transactions, many=True)

            # Return the paginated response
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response(
                {
                    "errors": str(e),
                    "status": status.HTTP_400_BAD_REQUEST
                }, status= status.HTTP_400_BAD_REQUEST
                
            )
        
class TransactionDetailView(GenericAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get(self, request, id, transaction_id, *args, **kwargs):
        try:
            user = request.user
            if str(user.id) != id:
                return Response(
                    {
                        "message": "You are not authorized to view this user's transactions",
                        "status": status.HTTP_403_FORBIDDEN
                    }, status=status.HTTP_403_FORBIDDEN
                )
            transaction = Transaction.objects.get(id=transaction_id, owner=user)

            serializer = self.get_serializer(transaction)            
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Transaction.DoesNotExist:
                return Response(
                    {
                        "message": "Transaction not found",
                        "status": status.HTTP_404_NOT_FOUND
                    }, status=status.HTTP_404_NOT_FOUND
                )        
        except Exception as e:
            return Response(
                {
                    "errors": str(e),
                    "status": status.HTTP_400_BAD_REQUEST
                }, status= status.HTTP_400_BAD_REQUEST
                
            )