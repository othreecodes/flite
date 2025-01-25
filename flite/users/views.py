from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import User, NewUserPhoneVerification, Transaction, Balance
from .permissions import IsUserOrReadOnly
from .serializers import *
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
import uuid

from . import utils

class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """
    Updates and retrieves user accounts
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsUserOrReadOnly,)


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


class UserDepositsView(GenericAPIView):
    queryset = Balance.objects.all()
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Get the amount from the validated data
            amount = serializer.validated_data.get("amount")

            # Get or create the user's balance
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

            # Use filter() to ensure there's only one Balance object and handle multiple cases
            balance = Balance.objects.filter(owner=user).first()
            if not balance:
                return Response(
                    {
                        "message": "Balance record not found",
                        "status": status.HTTP_400_BAD_REQUEST
                    }, status=status.HTTP_400_BAD_REQUEST
                )

            if amount > balance.available_balance:
                return Response(
                    {
                        "message": 'Insufficient funds',
                        "status": status.HTTP_400_BAD_REQUEST
                    }, status=status.HTTP_400_BAD_REQUEST
                )

            old_balance = balance.available_balance
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
                    "old_balance": old_balance,
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



class TransferFundView(GenericAPIView):
    serializer_class = TransferFundSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, sender_account_id, recipient_account_id, *args, **kwargs):
        sender = request.user

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]

        try:
            recipient = User.objects.get(id=recipient_account_id)

            sender_balance = Balance.objects.filter(owner=sender).first()

            if sender_balance is None:
                return Response(
                    {
                        "message": "Sender balance record not found",
                        "status": status.HTTP_400_BAD_REQUEST
                    }, status=status.HTTP_400_BAD_REQUEST
                )

            recipient_balance = Balance.objects.filter(owner=recipient).first()

            if recipient_balance is None:
                return Response(
                    {
                        "message": "Recipient balance record not found",
                        "status": status.HTTP_400_BAD_REQUEST
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            
            if sender_balance.available_balance < amount:
                return Response(
                    {
                        "message": "Insufficient funds",
                        "status": status.HTTP_400_BAD_REQUEST
                    }, status=status.HTTP_400_BAD_REQUEST
                )

            sender_balance.old_balance = sender_balance.available_balance
            recipient_balance.old_balance = recipient_balance.available_balance
            sender_balance.available_balance -= amount
            sender_balance.book_balance -= amount
            recipient_balance.available_balance += amount
            recipient_balance.book_balance += amount
            sender_balance.save()
            recipient_balance.save()

            # Create transaction records for sender
            Transaction.objects.create(
                owner=sender,
                reference=str(uuid.uuid4()),
                amount=amount,
                new_balance=sender_balance.available_balance,
                type="TRANSFER"
            )

            # Create transaction record for recipient
            Transaction.objects.create(
                owner=recipient,
                reference=str(uuid.uuid4()),
                amount=amount,
                new_balance=recipient_balance.available_balance,
                type="RECEIVED"
            )

            return Response(
                {
                    "message": "Transfer successful",
                    "status": status.HTTP_200_OK,
                    "sender_old_balance": sender_balance.old_balance,
                    "sender_new_balance": sender_balance.available_balance,
                    "recipient_old_balance": recipient_balance.old_balance,
                    "recipient_new_balance": recipient_balance.available_balance
                }, status=status.HTTP_200_OK
            )
        # except User.DoesNotExist:
        #     return Response(
        #         {
        #             "message": "Recipient user not found",
        #             "status": status.HTTP_400_BAD_REQUEST
        #         }, status=status.HTTP_400_BAD_REQUEST
        #     )
        except Exception as e:
            return Response(
                {
                    "error": str(e),
                    "status": status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST
            )