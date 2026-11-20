from django.contrib import admin

from workers.models import Booking, Review, Worker


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('name', 'skill', 'area', 'phone', 'experience', 'available',
                    'available_now', 'verified')
    list_filter = ('verified', 'available', 'available_now', 'skill', 'area')
    search_fields = ('name', 'skill', 'area', 'phone')
    actions = ['mark_verified', 'remove_verified']

    @admin.action(description='Mark selected workers as Verified (ID checked)')
    def mark_verified(self, request, queryset):
        self.message_user(request, f'{queryset.update(verified=True)} worker(s) verified.')

    @admin.action(description='Remove Verified badge from selected workers')
    def remove_verified(self, request, queryset):
        self.message_user(request, f'{queryset.update(verified=False)} worker(s) updated.')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'worker', 'date', 'time_slot', 'phone', 'status')
    list_filter = ('status', 'time_slot', 'date')
    readonly_fields = ('otp', 'otp_attempts', 'created_at')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('worker', 'customer', 'rating', 'created_at')
    list_filter = ('rating',)
