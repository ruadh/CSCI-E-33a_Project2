from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from .models import User, Listing, Category, Bid, Comment, WatchlistItem
from django.db.models import Max
from django.contrib.auth.decorators import login_required
from django import forms
from django.utils import timezone
import datetime


# SETTINGS

# Placeholder listing image courtesy of janjf93 on Pixabay:  https://pixabay.com/vectors/day-shield-price-tag-flyers-1727489/
placeholder_image = '/static/auctions/default_photo.png'
default_timezone = 'America/New_York'


# FORM CLASSES
# Note:  the user and timestamp can be derived, so I'm not including them as form fields

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


# AUTHENTICATION METHODS

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
            # CITATION:  Using 'next' to send the user back to their starting page adapted from:  https://stackoverflow.com/a/21693784
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
            user.save()
        except IntegrityError:
            return render(request, 'auctions/register.html', {
                'message': 'Username already taken.',
                'message_class': 'error'
            })
        login(request, user)
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'auctions/register.html')


# LISTING METHODS

# Display a list view of item listings
# NOTE: Default is all active listings, but may be called with different criteria by other methods

def index(request, listings=Listing.objects.filter(is_active=True), title='Active Listings'):
    timezone.activate(default_timezone)
    return render(request, 'auctions/index.html', {'listings': listings, 'title': title})


# Display the detail view of a listing

def listing_view(request, listing_id, message=None, message_class=None):
    listing = Listing.objects.get(pk=listing_id)
    # Load a blank comment form and list any existing comments
    comment_form = CommentForm(initial={'listing': listing_id})
    comments = Comment.objects.filter(
        listing=listing_id).order_by('timestamp')
    # Determine whether this listing is in the user's watchlist
    if request.user.is_authenticated and WatchlistItem.objects.filter(listing=listing_id, watcher=request.user):
        in_watchlist = True
    else:
        in_watchlist = False
    # Load a blank bid form with the current price
    # bid_form = BidForm(initial={'listing': listing_id})
    bid_form = BidForm(initial={'listing': listing})
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
    form = ListingForm(request.POST)
    # Validate form submission and gather values
    if form.is_valid():
        category = form.cleaned_data['category']
        title = form.cleaned_data['title']
        description = form.cleaned_data['description']
        starting_price = form.cleaned_data['starting_price']
        # Check that the starting price is valid
        if starting_price > 0:
            # If no image was supplied, use the placeholder
            if form.cleaned_data['image_url']:
                image_url = form.cleaned_data['image_url']
            else:
                image_url = placeholder_image
            # Re-check for required fields, and save and render the listing
            if title and description and starting_price:
                listing = Listing(category=category, owner=request.user,  title=title, description=description,
                                  starting_price=starting_price, image=image_url, )
                listing.save()
                return listing_view(request, listing.id)
            else:
                return render(request, 'auctions/new_listing.html', {
                    'listing_form': form
                })
        else:
            return listing_form(request, form, 'Starting bid must be greater than $0', 'error')
    else:
        return listing_form(request, form, 'An error occurred while processing your submission.  Your listing has NOT been saved.', 'error')


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

# Add an item to the user's watchlist
# NOTE:  I chose to allow users to include their own listings and closed listings on their watch lists,
#           since users may need to track them, and the spec includes no features for doing that

@login_required
def watchlist_add(request, listing_id):
    try:
        item = WatchlistItem(listing=Listing.objects.get(
            pk=listing_id), watcher=request.user)
        item.save()
        # Re-render the page with the new information
        return listing_view(request, listing_id)
    except:
        # If the item is already on the list, just show that status - the user doesn't need an error
        if WatchlistItem.objects.filter(listing=Listing.objects.get(pk=listing_id), watcher=request.user):
            message = None
            in_watchlist = True
        # If the item can't be added for another reason, show the user an error
        else:
            message = 'An error occurred while attempting to add this item to your watchlist'
            in_watchlist = False
        # Re-render the page with the new information
        return listing_view(request, listing_id, message, 'error')


# Remove an item from the user's watch list

@login_required
def watchlist_remove(request, listing_id):
    try:
        item = WatchlistItem.objects.get(
            listing=Listing.objects.get(pk=listing_id), watcher=request.user)
        item.delete()
        # Re-render the page with the new information
        return listing_view(request, listing_id)
    except:
        # If the item doesn't exist or cannot be deleted, return an error to the user
        message = 'An error occurred while attempting to remove this item from your watch list'
        return listing_view(request, listing_id, message, 'error')


# View the user's watch list

@login_required
def watchlist_view(request):
    # Show the user's watched items with the most recently added at the top
    return render(request, 'auctions/watchlist.html', {
        'watchlist_items': WatchlistItem.objects.filter(watcher=request.user).order_by('-id')
    })


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
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            # Gather the form fields into comment object
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
    if request.method == "POST":
        form = BidForm(request.POST)
        # Initial assumption is error; we'll unset this if the bid passes validation
        message_class = 'error'
        if form.is_valid():
            # Gather the bid details
            listing = Listing.objects.get(pk=form.cleaned_data['listing'].id)
            amount = form.cleaned_data['amount']
            # Validate that the bid is higher than the current price
            if amount <= listing.bid_price:
                message = 'Your bid must be higher than the current price.'
            # Don't allow the user to bid on their own items  (UI should prevent this, but just to be safe)
            elif listing.owner == request.user:
                message = 'You may not bid on your own listings.'
            # Don't allow the user to bid on a closed listing
            # This could occur if the auction is closed beteween page load and bid submission
            elif listing.is_active == False:
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


# TEMP FOR TESTING
def dev(request, param='default parameter'):
    timezone.activate('America/New_York')
    param = timezone.get_current_timezone_name()
    return render(request, 'auctions/dev.html', {
        'param': param,
    })
