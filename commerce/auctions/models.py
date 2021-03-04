from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Max
# from django.core.validators import MinValueValidator
import decimal

class User(AbstractUser):

    def __str__(self):
        return f'{self.username}'


class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name_plural = "Categories"


class Listing(models.Model):
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='listings')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, related_name='listings', null=True, blank=True)
    watchlist_items = models.ManyToManyField(User, blank=True, related_name='watchlist_items')
    title = models.CharField(max_length=150)
    description = models.TextField(max_length=2000)
    starting_price = models.DecimalField(max_digits=9, decimal_places=2)
    is_active = models.BooleanField(default=True)
    image_url = models.URLField(null=True, blank=True, verbose_name='Image URL')
    timestamp = models.DateTimeField(auto_now_add=True)

    # Default sorting:  most recent listings first
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.owner.username}\'s {self.title}'


    # Calculated current bid price
    # CITATION:  @property decorator approach based on:  https://stackoverflow.com/a/17682694

    @property
    def bid_count(self):
        return Bid.objects.filter(listing=self.id).count()


    @property
    def bid_price(self):
        try:
            bids = Bid.objects.filter(listing=self.id)
            if bids.count() > 0:
                max_bid = Bid.objects.filter(listing=self.id).aggregate(Max('amount'))
                return round(max_bid['amount__max'], 2)
            else:
                return self.starting_price
        except:
            return 'Error determining current bid'

    # Calculated winner

    @property
    def winner(self):
        try:
            bids = Bid.objects.filter(listing=self.id)
            max_bid = bids.aggregate(Max('amount'))['amount__max']
            return bids.filter(amount=max_bid)[0].bidder
        except:
            return "Error determining winner"


class Bid(models.Model):
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Your bid')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.bidder.username} for {self.listing.title}: ${self.amount}'


class Comment(models.Model):
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name='comments')
    commenter = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments')
    body = models.TextField(max_length=500, blank=False, null=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.timestamp.strftime("%x %X")} - {self.commenter.username} on {self.listing.title}'
