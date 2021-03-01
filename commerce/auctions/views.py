from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from .models import User, Listing, Category, Bid, Comment, WatchlistItem
from django.db.models import Max
from django.contrib.auth.decorators import login_required
from django import forms
import datetime

# CLASSES

# Comment form


class CommentForm(forms.Form):
    # TO DO:  test hidden fields
    body = forms.CharField(required=True, strip=True, widget=forms.Textarea, label=None)
    listing = forms.IntegerField(widget=forms.HiddenInput)


def index(request):
    return render(request, 'auctions/index.html', {'listings': Listing.objects.all()})


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
            # CITATION:  'next' approach adapted from:  https://stackoverflow.com/a/21693784
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


# Display the detail view of a listing

def listing_view(request, listing_id):
    # Load a blank comment form and any existing comments
    comment_form = CommentForm(initial={'listing': listing_id })
    comments = Comment.objects.filter(
        listing=listing_id).order_by('-timestamp')
    # Determine whether this listing is in the user's watchlist
    if request.user.is_authenticated and WatchlistItem.objects.filter(listing=listing_id, watcher=request.user):
        in_watchlist = True
    else:
        in_watchlist = False
    return render(request, 'auctions/listing.html', {
        'listing_id': listing_id,
        'listing': Listing.objects.get(pk=listing_id),
        'in_watchlist': in_watchlist,
        'comments': comments,
        'comment_form': comment_form
    })


# Add an item to the user's watchlist
# NOTE:  I chose to allow users to include their own listings and closed listings on their watch lists,
#           since the spec doesn't call for any features to track those

@login_required
def watchlist_add(request, listing_id):
    try:
        item = WatchlistItem(listing=Listing.objects.get(
            pk=listing_id), watcher=request.user)
        item.save()
        return render(request, 'auctions/listing.html', {
            'listing_id': listing_id,
            'listing': Listing.objects.get(pk=listing_id),
            'message': None,
            'in_watchlist': True
        })
    except:
        # If the item is already on the list, just show that status - the user doesn't need an error
        if WatchlistItem.objects.filter(listing=Listing.objects.get(pk=listing_id), watcher=request.user):
            message = None
            in_watchlist = True
        # If the item can't be added for another reason, show the user an error
        else:
            message = 'An error occurred while attempting to add this item to your watchlist'
            in_watchlist = False
        return render(request, 'auctions/listing.html', {
            'listing_id': listing_id,
            'listing': Listing.objects.get(pk=listing_id),
            'message': message,
            'in_watchlist': in_watchlist
        })


# Remove an item from the user's watch list

@login_required
def watchlist_remove(request, listing_id):
    try:
        item = WatchlistItem.objects.get(
            listing=Listing.objects.get(pk=listing_id), watcher=request.user)
        item.delete()
        return render(request, 'auctions/listing.html', {
            'listing_id': listing_id,
            'listing': Listing.objects.get(pk=listing_id),
            'in_watchlist': False
        })
    except:
        # If the item doesn't exist or cannot be deleted, return an error to the user
        return render(request, 'auctions/listing.html', {
            'listing_id': listing_id,
            'listing': Listing.objects.get(pk=listing_id),
            'in_watchlist': True,
            'message': 'An error occurred while attempting to remove this item from your watch list',
            'message_class': 'error'
        })


# View the user's watch list

def watchlist_view(request):
    # Show the user's watched items with the most recently-added at the top
    return render(request, 'auctions/watchlist.html', {
        'watchlist_items': WatchlistItem.objects.filter(watcher=request.user).order_by('-id')
    })


# Close a listing:  ends the auction, making the highest bidder the winner

def close_listing(request, listing_id):
    # Mark the listing as closed
    listing = Listing.objects.get(pk=listing_id)
    listing.is_active = False
    listing.save()
    # # Re-render the page with the new information
    return listing_view(request, listing_id)


# Submit the comment form

def comment_add(request):
    # Validate and save the comment form
    if request.method=="POST":
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


# TEMP FOR TESTING
def dev(request, param='default parameter'):
    return render(request, 'auctions/dev.html', {
        'param': param,
    })