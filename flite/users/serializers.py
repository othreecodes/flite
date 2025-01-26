from rest_framework import serializers
from .models import Balance, Bank, Card, Transaction, User, NewUserPhoneVerification,UserProfile,Referral
from . import utils

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',)
        read_only_fields = ('username', )


class CreateUserSerializer(serializers.ModelSerializer):
    referral_code = serializers.CharField(required=False)


    def validate_referral_code(self, code):
        
        self.reffered_profile = UserProfile.objects.filter(referral_code=code.lower())
        is_valid_code = self.reffered_profile.exists()
        if not is_valid_code:
            raise serializers.ValidationError(
                "Referral code does not exist"
            )
        else:
            return code

    def create(self, validated_data):
        # call create_user on user object. Without this
        # the password will be stored in plain text.
        referral_code = None
        if 'referral_code' in validated_data:
            referral_code = validated_data.pop('referral_code',None)
            
        user = User.objects.create_user(**validated_data)

        if referral_code:
            referral =Referral()
            referral.owner = self.reffered_profile.first().user
            referral.referred = user
            referral.save()

        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'first_name', 'last_name', 'email', 'auth_token','referral_code')
        read_only_fields = ('auth_token',)
        extra_kwargs = {'password': {'write_only': True}}


class SendNewPhonenumberSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        phone_number = validated_data.get("phone_number", None) 
        email = validated_data.get("email", None)

        obj, code = utils.send_mobile_signup_sms(phone_number, email)
        
        return {
            "verification_code":code,
            "id":obj.id
        }

    class Meta:
        model = NewUserPhoneVerification
        fields = ('id', 'phone_number', 'verification_code', 'email',)
        extra_kwargs = {'phone_number': {'write_only': True, 'required':True}, 'email': {'write_only': True}, }
        read_only_fields = ('id', 'verification_code')

# Transaction Serializer  
class DebitOrWithdrawSerializer(serializers.Serializer):
    amount = serializers.FloatField()

    class Meta:
        model = Balance
        fields = ['owner', 'book_balance', 'available_balance', 'active']

class TransferSerializer(serializers.Serializer):
    amount = serializers.FloatField(min_value=0.01)  # Transfer amount must be greater than 0

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'reference', 'status', 'amount', 'new_balance']

class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Balance
        fields = ['owner', 'book_balance', 'available_balance', 'active']

class BankSerializer(serializers.ModelSerializer):
    bank = serializers.StringRelatedField()  # To display the bank name instead of the ID
    
    class Meta:
        model = Bank
        fields = ['bank', 'account_name', 'account_number', 'account_type']
        
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['referral_code']

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = [
            'authorization_code', 'ctype', 'cbin', 'cbrand', 'country_code', 
            'first_name', 'last_name', 'number', 'bank', 
            'expiry_month', 'expiry_year', 'is_active'
        ]

class UserAccountSerializer(serializers.ModelSerializer):
    balances = BalanceSerializer(many=True, source='balance_set')
    banks = BankSerializer(many=True, source='bank_set')
    cards = CardSerializer(many=True, source='card_set')
    profile = UserProfileSerializer(source='userprofile')
    transactions = TransactionSerializer(many=True, source='transaction')

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'balances', 'banks', 'cards', 'profile', 'transactions']
