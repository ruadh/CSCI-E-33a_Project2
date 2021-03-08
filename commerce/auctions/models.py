from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Max
from django.conf import settings
from django.core.validators import MinValueValidator
import decimal
import pytz


class User(AbstractUser):
    # Timezones list approach from:  https://stackoverflow.com/a/45867250
    timezones = tuple(zip(pytz.all_timezones, pytz.all_timezones))
    timezone = models.CharField(max_length=32, choices=timezones,
                                default=settings.DEFAULT_TIMEZONE)

    def __str__(self):
        return f'{self.username}'


class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name_plural = 'Categories'


class Listing(models.Model):
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='listings')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, related_name='listings', null=True, blank=True)
    watchlist_items = models.ManyToManyField(
        User, blank=True, related_name='watchlist_items')
    title = models.CharField(max_length=150)
    description = models.TextField(max_length=2000)
    starting_price = models.DecimalField(max_digits=9, decimal_places=2, validators=[
                                         MinValueValidator(decimal.Decimal('0.01'))])
    is_active = models.BooleanField(default=True)
    image_url = models.URLField(
        null=True, blank=True, verbose_name='Image URL')
    timestamp = models.DateTimeField(auto_now_add=True)

    # Sort most recent listings first by default
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.owner.username}\'s {self.title}'

    # Count bids for this listing
    # CITATION:  Learned the @property decorator approach from:  https://stackoverflow.com/a/17682694
    @property
    def bid_count(self):
        return self.bids.count()

    # Highest existing bid for this listing
    @property
    def max_bid(self):
        try:
            bid = self.bids.aggregate(Max('amount'))
            return round(bid['amount__max'], 2)
        except:
            return None

    # The minimum valid bid for this item
    @property
    def required_bid(self):
        if self.max_bid is None:
            return self.starting_price
        else:
            return round(self.max_bid + decimal.Decimal(settings.BID_INCREMENT), 2)

    # The winner of this auction, if any
    @property
    def winner(self):
        if self.bid_count > 0:
            try:
                # From this listing's bid objects, find the one w/ the max bid amount and return its user
                return self.bids.filter(amount=self.max_bid)[0].bidder
            except:
                return 'Error determining winner'
        else:
            return None

    # If the user did not supply an image, use the placeholder
    # NOTE:  Necessary because relative paths fail URL field validation when the listing is updated in the admin interface
    @property
    def image_display(self):
        if self.image_url is None:
            return settings.PLACEHOLDER_IMAGE
        else:
            return self.image_url


class Bid(models.Model):
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='bids')
    timestamp = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(
        max_digits=9, decimal_places=2, verbose_name='Your bid')

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
