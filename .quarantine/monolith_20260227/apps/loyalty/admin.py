
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import LoyaltyTier, LoyaltyAccount, PointsTransaction


@admin.register(LoyaltyTier)
class LoyaltyTierAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'min_points_required', 'points_multiplier', 'redemption_bonus', 'member_count']
    list_filter = ['name']
    search_fields = ['display_name', 'name']
    ordering = ['min_points_required']
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_tier', 'current_points_balance', 'total_points_earned', 'lifetime_spending', 'created_at']
    list_filter = ['current_tier', 'created_at', 'tier_qualification_date']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['total_points_earned', 'created_at', 'updated_at', 'tier_qualification_date']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'current_tier')
        }),
        ('Points & Spending', {
            'fields': ('current_points_balance', 'total_points_earned', 'lifetime_spending')
        }),
        ('Tier Information', {
            'fields': ('tier_qualification_date',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'current_tier')


@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'account_user', 'transaction_type', 'points_amount', 'status', 'reference_id', 'created_at']
    list_filter = ['transaction_type', 'status', 'created_at', 'expires_at']
    search_fields = ['account__user__username', 'reference_id', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'processed_at']
    raw_id_fields = ['account']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('id', 'account', 'transaction_type', 'points_amount', 'status')
        }),
        ('Reference Information', {
            'fields': ('reference_id', 'description', 'metadata')
        }),
        ('Expiry Tracking', {
            'fields': ('expires_at', 'expired_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def account_user(self, obj):
        if obj.account and obj.account.user:
            url = reverse('admin:auth_user_change', args=[obj.account.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.account.user.username)
        return '-'
    account_user.short_description = 'User'
    account_user.admin_order_field = 'account__user__username'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('account__user', 'account__current_tier')
    
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='completed')
        self.message_user(request, f'{updated} transactions marked as completed.')
    mark_as_completed.short_description = 'Mark selected transactions as completed'
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='failed')
        self.message_user(request, f'{updated} transactions marked as failed.')
    mark_as_failed.short_description = 'Mark selected transactions as failed'