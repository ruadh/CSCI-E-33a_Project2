from django.contrib import admin
from .models import User, Listing, Category, Bid, Comment

admin.site.register(User)
admin.site.register(Listing)
admin.site.register(Category)
admin.site.register(Bid)
admin.site.register(Comment)
