from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.db.models import Max
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django import forms
import datetime
import pytz
from .models import User, Listing, Category, Bid, Comment


# FORM CLASSES

# Comment form

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body', 'listing']
        widgets = {
            'listing': forms.HiddenInput,
            'body': forms.Textarea(
                attrs={'placeholder': 'Enter your comment here'}),
        }


# Bid Form

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['listing', 'amount']
        widgets = {
            'listing': forms.HiddenInput,
        }


# New Listing Form

class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'description',
                  'starting_price', 'category', 'image_url']


# AUTHENTICATION

# Log in

def login_view(request):
    if request.method == 'POST':

        # Attempt to sign user in
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        next = request.POST['next']

        # Check if authentication successful
        if user is not None:
            login(request, user)
            # Set the display timezone to the user's chosen time
            timezone.activate(user.timezone)
            # CITATION:  Using 'next' to return to starting page:  https://stackoverflow.com/a/21693784
            if next:
                return HttpResponseRedirect(request.POST.get('next'))
            else:
                return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, 'auctions/login.html', {
                'message': 'Invalid username and/or password.',
                'message_class': 'error'
            })
    else:
        return render(request, 'auctions/login.html')


# Log out

def logout_view(request):
    logout(request)
    # We don't need to unset the timezone; that is done when index is called
    return HttpResponseRedirect(reverse('index'))


# Register a new user

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']

        # Ensure password matches confirmation
        password = request.POST['password']
        confirmation = request.POST['confirmation']
        if password != confirmation:
            return render(request, 'auctions/register.html', {
                'message': 'Passwords must match.',
                'message_class': 'error'
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.timezone = request.POST['user_timezone']
            user.save()
        except IntegrityError:
            return render(request, 'auctions/register.html', {
                'message': 'Username already taken.',
                'message_class': 'error'
            })
        login(request, user)
        # Set the display timezone to the user's chosen time
        timezone.activate(user.timezone)
        return HttpResponseRedirect(reverse('index'))
    else:
        timezones = pytz.all_timezones
        return render(request, 'auctions/register.html', {
            'timezones': timezones,
            'default_timezone': settings.DEFAULT_TIMEZONE
        })


# LISTINGS

# Display a list of listings

def index(request, listings=None, title='Active Listings'):
    # Show all active listings, unless a set is passed in
    if listings is None:
        listings = Listing.objects.filter(is_active=True)
    # If the user isn't authenticated, set the display timezone to the site's default
    if not request.user.is_authenticated:
        timezone.activate(settings.DEFAULT_TIMEZONE)
    return render(request, 'auctions/index.html', {'listings': listings, 'title': title})


# Display all inactive listings

def listings_closed(request):
    return index(request, Listing.objects.filter(is_active=False), 'Closed Listings')


# Display the detail view of a listing

def listing_view(request, listing_id, message=None, message_class=None):
    listing = Listing.objects.get(pk=listing_id)

    # Load a blank comment form and list any existing comments
    comment_form = CommentForm(initial={'listing': listing_id})
    comments = Comment.objects.filter(
        listing=listing_id).order_by('timestamp')

    # Determine whether this listing is in the user's watchlist
    if request.user.is_authenticated:
        user = User.objects.get(pk=request.user.id)
        watchlist_items = user.watchlist_items.all()
        in_watchlist = listing in watchlist_items
    else:
        in_watchlist = False

    # Load a blank bid form with the current price
    bid_form = BidForm(initial={'listing': listing})

    # Render the listing detail page
    return render(request, 'auctions/listing.html', {
        'listing_id': listing_id,
        'listing': listing,
        'in_watchlist': in_watchlist,
        'comments': comments,
        'comment_form': comment_form,
        'bid_form': bid_form,
        'message': message,
        'message_class': message_class
    })


# Load the new listing form

@login_required
def listing_form(request, form=ListingForm(), message=None, message_class=None):
    return render(request, 'auctions/new_listing.html', {
        'listing_form': form,
        'message': message,
        'message_class': message_class
    })


# Create a new listing

@login_required
def listing_add(request):

    # Validate form submission and gather values
    form = ListingForm(request.POST)
    if form.is_valid():
        category = form.cleaned_data['category']
        title = form.cleaned_data['title']
        description = form.cleaned_data['description']
        starting_price = form.cleaned_data['starting_price']
        image_url = form.cleaned_data['image_url']

        # Check that the starting price is valid so we can provide a value
        if starting_price > 0:
            # Re-check for required fields, and save and render the listing
            if title and description and starting_price:
                listing = Listing(category=category, owner=request.user,  title=title, description=description,
                                  starting_price=starting_price, image_url=image_url, )
                listing.save()
                return listing_view(request, listing.id)
            else:
                return render(request, 'auctions/new_listing.html', {
                    'listing_form': form
                })
        else:
            return listing_form(request, form, 'Starting bid must be greater than $0', 'error')
    else:
        return listing_form(request, form,
                            'An error occurred while processing your submission.  Your listing has NOT been saved.',
                            'error')


# Close a listing:  ends the auction, making the highest bidder the winner

@login_required
def close_listing(request, listing_id):
    # Mark the listing as closed
    listing = Listing.objects.get(pk=listing_id)
    listing.is_active = False
    listing.save()
    # Re-render the page with the new information
    return listing_view(request, listing_id)


# WATCHLIST METHODS

# Display the user's watchlist

@login_required
def watchlist_view(request):
    # Gather the current user's watchlist
    user = User.objects.get(pk=request.user.id)
    watchlist_items = user.watchlist_items.all()
    return index(request, watchlist_items, 'My Watchlist')


# Add a listing to the user's watchlist

# NOTE:  I chose to allow users to include their own listings and closed listings on their watch lists,
#           since users may need to track them, and the spec includes no features for doing that

@login_required
def watchlist_add(request, listing_id):
    try:
        listing = Listing.objects.get(pk=listing_id)
        listing.watchlist_items.add(request.user)
        return listing_view(request, listing_id, message='This item has been added to your watchlist')
    except Exception:
        message = 'An error occurred while attempting to add this item to your watchlist'
        in_watchlist = False
        return listing_view(request, listing_id, message, 'error')


# Remove a listing from the user's watchlist

@login_required
def watchlist_remove(request, listing_id):
    try:
        listing = Listing.objects.get(pk=listing_id)
        listing.watchlist_items.remove(request.user)
        # .remove() does not give an error if the item is not in the watchlist,
        # but we don't need to show the user an error - either way, the item ends up not in the list
        return listing_view(request, listing_id, message='This item has been removed from your watchlist')
    except Exception:
        # If this fails for any other reason, return an error to the user
        message = 'An error occurred while attempting to remove this item from your watch list'
        return listing_view(request, listing_id, message, 'error')


# CATEGORY METHODS

# View an index of all categories

def category_index(request):
    return render(request, 'auctions/categories.html', {
        'categories': Category.objects.all()
    })


# View a list of all listings for a given category

def category_listing(request, category_id):
    if category_id == 0:
        category_name = 'Uncategorized'
        listings = Listing.objects.filter(category=None, is_active=True)
    else:
        category_name = Category.objects.get(pk=category_id).name
        listings = Listing.objects.filter(category=category_id, is_active=True)
    return index(request, listings, category_name)


# COMMENT METHODS

# Submit the comment form

@login_required
def comment_add(request):

    # Validate and save the comment form
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            listing = form.cleaned_data['listing']
            body = form.cleaned_data['body']

            # Non-empty body validation is performed on the model level, but let's double-check
            if body:
                comment = Comment(commenter=request.user, timestamp=datetime.datetime.now(
                ), listing=listing, body=body)
                # Save the comment to the database and re-render the page
                comment.save()
                message = 'Thank you for your comment.'
                message_class = None
            else:
                message = 'Your comment cannot be blank.'
                message_class = 'error'
        else:
            message = 'An error occurred while processing your submission.  Your comment has NOT been saved.'
            message_class = 'error'
        return listing_view(request, listing.id, message, message_class)


# BIDDING METHODS

# Submit a bid

@login_required
def bid_add(request):
    if request.method == 'POST':
        form = BidForm(request.POST)
        message_class = 'error'
        if form.is_valid():
            # Gather the bid details
            listing = Listing.objects.get(pk=form.cleaned_data['listing'].id)
            amount = form.cleaned_data['amount']
            # Make sure the bid is high enough
            if amount < listing.required_bid:
                message = f'You must bid at least ${listing.required_bid}'
            # Don't allow the user to bid on their own items  (UI should prevent this, but just to be safe)
            elif listing.owner == request.user:
                message = 'You may not bid on your own listings.'
            # Don't allow the user to bid on a closed listing
            # This could occur if the auction is closed beteween page load and bid submission
            elif not listing.is_active:
                message = 'Sorry, this auction has ended.'
            # If all validation passes, save the bid
            else:
                bid = Bid(bidder=request.user, listing=listing,
                          amount=amount, timestamp=datetime.datetime.now())
                bid.save()
                message = 'Thank you for your bid'
                message_class = None
        else:
            message = 'An unexpected error occurred.  Your bid has NOT been saved.'

        # Regardless of the outcome, Re-render the page with the current details and any messages
        return listing_view(request, listing.id, message, message_class)
