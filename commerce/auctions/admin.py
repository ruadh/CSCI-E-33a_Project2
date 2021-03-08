from django.contrib import admin
from .models import User, Listing, Category, Bid, Comment


class ListingAdmin(admin.ModelAdmin):
    exclude = ('watchlist_items',)


admin.site.register(User)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Category)
admin.site.register(Bid)
admin.site.register(Comment)