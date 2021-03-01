from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from .models import User, Listing, Category, Bid, Comment, WatchlistItem
from django.db.models import Max
from django.contrib.auth.decorators import login_required
from django import forms
import datetime, decimal


# FORM CLASSES
# Note:  the user and timestamp can be derived, so I'm not included them as form fields

# Comment form

class CommentForm(forms.Form):
    body = forms.CharField(required=True, strip=True,
                           widget=forms.Textarea, label=None)
    listing = forms.IntegerField(widget=forms.HiddenInput)


# Bid Form

class BidForm(forms.Form):
    listing = forms.IntegerField(widget=forms.HiddenInput)
    # TO DO:  can we validate the amount before the user submits the form? Ideal, but not required
    amount = forms.DecimalField(required=True, max_digits=9, decimal_places=2)


# METHODS

def index(request, listings=Listing.objects.filter(is_active=True), title='Active Listings'):
    return render(request, 'auctions/index.html', {'listings': listings, 'title': title})


# AUTHENTICATION METHODS

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
                'message': 'Invalid username and/or password.'
            })
    else:
        return render(request, 'auctions/login.html')


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']

        # Ensure password matches confirmation
        password = request.POST['password']
        confirmation = request.POST['confirmation']
        if password != confirmation:
            return render(request, 'auctions/register.html', {
                'message': 'Passwords must match.'
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, 'auctions/register.html', {
                'message': 'Username already taken.'
            })
        login(request, user)
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'auctions/register.html')


# LISTING METHODS

# Display the detail view of a listing

def listing_view(request, listing_id, message=''):
    listing = Listing.objects.get(pk=listing_id)
    # Load a blank comment form and list any existing comments
    comment_form = CommentForm(initial={'listing': listing_id})
    comments = Comment.objects.filter(
        listing=listing_id).order_by('-timestamp')
    # Determine whether this listing is in the user's watchlist
    if request.user.is_authenticated and WatchlistItem.objects.filter(listing=listing_id, watcher=request.user):
        in_watchlist = True
    else:
        in_watchlist = False
    # Load a blank bid form with the current price
    bid_form = BidForm(initial={'listing': listing_id})
    return render(request, 'auctions/listing.html', {
        'listing_id': listing_id,
        'listing': listing,
        'in_watchlist': in_watchlist,
        'comments': comments,
        'comment_form': comment_form,
        'bid_form': bid_form,
        'message': message
    })


# Close a listing:  ends the auction, making the highest bidder the winner

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
        return listing_view(request, listing_id)  


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
        return listing_view(request, listing_id, message)  


# View the user's watch list

def watchlist_view(request):
    # Show the user's watched items with the most recently-added at the top
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
    category_name = Category.objects.get(pk=category_id).name
    listings = Listing.objects.filter(category=category_id, is_active=True)
    return index(request, listings, category_name)


# COMMENT METHODS

# Submit the comment form

def comment_add(request):
    # Validate and save the comment form
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            # Get the listing as an object
            listing_id = form.cleaned_data['listing']
            listing = Listing.objects.get(pk=listing_id)
            body = form.cleaned_data['body']
            comment = Comment(commenter=request.user, timestamp=datetime.datetime.now(), listing=listing, body=body)
            comment.save()
            return listing_view(request, listing_id)
        else:
            # TO DO: return an error message to the user
            return HttpResponse('invalid')


# BIDDING METHODS

# Submit a bid
@login_required
def bid_add(request):
    if request.method == "POST":
        form = BidForm(request.POST)
        if form.is_valid():
            # Gather the bid details
            listing = Listing.objects.get(pk=form.cleaned_data['listing'])
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
                bid = Bid(bidder=request.user, listing=listing, amount=amount, timestamp=datetime.datetime.now())
                bid.save()
                message = 'Thank you for your bid'
        else:
            message = 'An unexpected error occurred.  Your bid has NOT been saved.'

        # Regardless of the outcome, Re-render the page with the current details and any messages
        return listing_view(request, listing.id, message)


# TEMP FOR TESTING
def dev(request, param='default parameter'):
    return render(request, 'auctions/dev.html', {
        'param': param,
    })
