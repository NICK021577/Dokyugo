from django.contrib import admin
from .models import AppointmentSlot, Booking, BookingEvent, Document, Notification, Requirement, ResidentProfile

class RequirementInline(admin.TabularInline):
    model = Requirement
    extra = 1

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'bookable', 'fee', 'updated_at']
    list_filter = ['group', 'bookable']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ['name']}
    inlines = [RequirementInline]

@admin.register(AppointmentSlot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ['starts_at', 'capacity', 'reserved', 'is_open']
    list_filter = ['is_open', 'starts_at']
    readonly_fields = ['reserved']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'resident', 'date', 'slot', 'status']
    list_filter = ['status', 'date']
    search_fields = ['resident__first_name', 'resident__last_name', 'resident__email']
    readonly_fields = [f.name for f in Booking._meta.fields] + ['documents']
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(ResidentProfile)
admin.site.site_header = 'DokyuGo administration'
admin.site.site_title = 'DokyuGo'
