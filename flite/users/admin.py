from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from django.contrib import admin


@admin.register(User)
class UserAdmin(UserAdmin):
    model = User
    list_display = ('id', 'username' )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    model = UserProfile
    list_display = ('user', 'referral_code' )

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('owner', 'referred')

@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ('owner', 'book_balance', 'available_balance', 'active')

@admin.register(AllBanks)
class AllBanksAdmin(admin.ModelAdmin):
    list_display = ('name', 'acronym', 'bank_code')

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('owner', 'bank', 'account_name', 'account_number', 'account_type')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('owner', 'reference', 'amount', 'type', 'created_at')
    ordering = ['-created_at']

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('owner', 'number', 'bank', 'expiry_month', 'expiry_year', 'is_active')


