from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import User, NewUserPhoneVerification
from .permissions import IsUserOrReadOnly
from .serializers import CreateUserSerializer, UserSerializer, SendNewPhonenumberSerializer
from rest_framework.views import APIView
from . import utils

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

    # func retrieves specific user by 'id'
    def retrieve(self, request, *args, **kwargs)->Response:
        """
        Retrieve a specific user by 'id'.
        """
        user = self.get_object()  # Fetch the user by 'id'
        return Response(UserSerializer(user).data)

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
        return Response(serializer.data)


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
