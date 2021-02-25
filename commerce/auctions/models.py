from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return f'{self.name}'


class Listing(models.Model):
    # CITATION:  Character limits based on: https://www.hellotax.com/blog/amazon/listing/optimization/
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='listings', null=True, blank=True)
    title = models.CharField(max_length=150)
    description = models.TextField(max_length=2000)
    starting_price = models.DecimalField(max_digits=9, decimal_places=2)
    is_active = models.BooleanField(default=True)
    image = models.URLField(null=True, blank=True, default='static/no_photo.png')

    def __str__(self):
        return f'{self.owner.username}\'s {self.title}'


class Bid(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.bidder.username} for {self.listing.title}: ${self.amount}'


class Comment(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='comments')
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    body = models.TextField(max_length=300)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.timestamp.strftime("%x %X")} - {self.commenter.username} on {self.listing.title}'

class WishlistItem(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='wishlist_items')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    comment = models.TextField(max_length=300)

    def __str__(self):
        return f'{self.listing}'

