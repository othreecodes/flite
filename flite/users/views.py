from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import *
from .permissions import IsUserOrReadOnly
from .serializers import *
from rest_framework.views import APIView
from . import utils
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes

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


class SendNewPhonenumberVerifyViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    Sending of verification code
    """
    queryset = NewUserPhoneVerification.objects.all()
    serializer_class = SendNewPhonenumberSerializer
    permission_classes = (AllowAny,)

    def update(self, request, pk=None, **kwargs):
        verification_object = self.get_object()
        code = request.data.get("code")

        if code is None:
            return Response({"message": "Request not successful"}, 400)

        if verification_object.verification_code != code:
            return Response({"message": "Verification code is incorrect"}, 400)

        code_status, msg = utils.validate_mobile_signup_sms(verification_object.phone_number, code)

        content = {
            'verification_code_status': str(code_status),
            'message': msg,
        }
        return Response(content, 200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deposit_money(request, user_id):
    if not request.data.get('amount'):
        responseDetails = utils.error_response('Amount field is required!')
        return Response(responseDetails, status=status.HTTP_400_BAD_REQUEST)

    amount = float(request.data.get('amount'))

    if amount <= 0:
        responseDetails = utils.error_response('Amount must be greater than zero!')
        return Response(responseDetails, status=status.HTTP_400_BAD_REQUEST)

    currentUser = User.objects.get(id=user_id)
    userBalance = Balance.objects.get(owner=currentUser)

    userBalance.book_balance = F('book_balance') + amount
    userBalance.available_balance = F('available_balance') + amount
    userBalance.save()
    userBalance.refresh_from_db()

    userTransaction = Transaction(status='success', amount=amount,
                                  new_balance=userBalance.available_balance, owner=currentUser)
    userTransaction.save()

    responseData = {
        'first_name': currentUser.first_name,
        'last_name': currentUser.last_name,
        'available_balance': userBalance.available_balance
    }
    responseDetails = utils.success_response('amount deposited successfully', responseData)
    return Response(responseDetails, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw_money(request, user_id):
    if not request.data.get('amount'):
        responseDetails = utils.error_response('Amount field is required!')
        return Response(responseDetails, status=status.HTTP_400_BAD_REQUEST)

    amount = float(request.data.get('amount'))

    if amount <= 0.0:
        responseDetails = utils.error_response('Amount must be greater than zero!')
        return Response(responseDetails, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    currentUser = User.objects.get(id=user_id)
    userBalance = Balance.objects.get(owner=currentUser)

    if userBalance.available_balance < amount:
        responseDetails = utils.error_response('You do not have enough balance to perform this operation!')
        return Response(responseDetails, status=status.HTTP_401_UNAUTHORIZED)

    userBalance.book_balance = F('book_balance') - amount
    userBalance.available_balance = F('available_balance') - amount
    userBalance.save()
    userBalance.refresh_from_db()

    userTransaction = Transaction(status='success', amount=amount,
                                  new_balance=userBalance.available_balance, owner=currentUser)
    userTransaction.save()

    responseData = {
        'first_name': currentUser.first_name,
        'last_name': currentUser.last_name,
        'available_balance': userBalance.available_balance
    }
    responseDetails = utils.success_response(
        'amount withdrawn successfully...no more insufficient funds😀', responseData)
    return Response(responseDetails, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_transactions(request, account_id):
    try:
        possibleUserAccount = Bank.objects.get(id=account_id)
        if not possibleUserAccount:
            responseDetails = utils.error_response('account does not exist')
            return Response(responseDetails, status=status.HTTP_404_NOT_FOUND)

        if possibleUserAccount.owner != request.user:
            responseDetails = utils.error_response('user not permitted to perform this operation')
            return Response(responseDetails, status=status.HTTP_403_FORBIDDEN)

        userTransactions = Transaction.objects.filter(owner=request.user)
        finalResponseData = utils.success_response(
            'user transactions retrieved successfully', userTransactions)
        return Response(finalResponseData, status.HTTP_200_OK)

    except:
        responseDetails = utils.error_response('internal server error')
        return Response(responseDetails, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_detail(request, account_id, transaction_id):
    try:
        possibleUserAccount = Bank.objects.get(id=account_id)
        if not possibleUserAccount:
            responseDetails = utils.error_response('account does not exist')
            return Response(responseDetails, status=status.HTTP_404_NOT_FOUND)

        if possibleUserAccount.owner_id != request.user.id:
            responseDetails = utils.error_response('user not permitted to perform this operation')
            return Response(responseDetails, status=status.HTTP_403_FORBIDDEN)

        singleUserTransaction = Transaction.objects.get(id=transaction_id)
        finalResponseData = utils.success_response(
            'user transaction retrieved successfully', singleUserTransaction)
        return Response(finalResponseData, status.HTTP_200_OK)

    except:
        responseDetails = utils.error_response('internal server error')
        return Response(responseDetails, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def p2p_transfer(request, sender_account_id, recipient_account_id):
    try:
        possibleSenderAccount = Bank.objects.get(id=sender_account_id)
        possibleRecipientAccount = Bank.objects.get(id=recipient_account_id)

        if not possibleSenderAccount:
            responseDetails = utils.error_response('sender account does not exist')
        if not possibleRecipientAccount:
            responseDetails = utils.error_response('recipient account does not exist')

        if possibleSenderAccount.owner != request.user:
            responseDetails = utils.error_response('user not permitted to perform this operation')
            return Response(responseDetails, status=status.HTTP_403_FORBIDDEN)

        amount = request.data.amount
        if amount <= 0.0:
            raise serializers.ValidationError('Amount must be greater than zero!')

        # debit the sender
        senderBalance = Balance.objects.get(owner=possibleSenderAccount.owner)
        senderBalance.book_balance = F('book_balance') - amount
        senderBalance.available_balance = F('available_balance') - amount
        senderBalance.save()
        senderBalance.refresh_from_db()

        senderTransaction = Transaction(
            status='success', amount=amount, new_balance=senderBalance.available_balance, owner=possibleSenderAccount.owner)
        senderTransaction.save()

        # credit the recipient
        recipientBalance = Balance.objects.get(owner=possibleRecipientAccount.owner)
        recipientBalance.book_balance = F('book_balance') + amount
        recipientBalance.available_balance = F('available_balance') + amount
        recipientBalance.save()
        recipientBalance.refresh_from_db()

        recipientTransaction = Transaction(
            status='success', amount=amount, new_balance=recipientBalance.available_balance, owner=possibleRecipientAccount.owner)
        recipientTransaction.save()

        p2p_transfer_record = P2PTransfer(
            transaction_ptr=senderTransaction, sender=possibleSenderAccount.owner, receipient=possibleRecipientAccount.owner)
        p2p_transfer_record.save()

        # return a response
        responseDetails = utils.success_response('transfer successful', senderBalance)
        return Response(responseDetails, status=status.HTTP_200_OK)

    except:
        responseDetails = utils.error_response('internal server error')
        return Response(responseDetails, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
