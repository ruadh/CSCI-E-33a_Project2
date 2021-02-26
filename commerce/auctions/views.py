from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from .models import User, Listing, Category, Bid, Comment, WatchlistItem
from .models import User


def index(request):
    return render(request, 'auctions/index.html', {'listings': Listing.objects.all()})


def login_view(request):
    if request.method == 'POST':

        # Attempt to sign user in
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
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
    # Determine whether this listing is in the user's watchlist
    if WatchlistItem.objects.filter(listing=listing_id, watcher=request.user):
        in_watchlist = True
    else:
        in_watchlist = False
    return render(request, 'auctions/listing.html', {
        'listing_id': listing_id,
        'listing': Listing.objects.get(pk=listing_id),
        'in_watchlist': in_watchlist
    })


# Add an item to the user's watch list

def watchlist_add(request, listing_id):
    try:
        item = WatchlistItem(listing=Listing.objects.get(pk=listing_id), watcher=request.user)
        item.save()
        return render(request, 'auctions/listing.html', {
            'listing_id': listing_id,
            'listing': Listing.objects.get(pk=listing_id),
            'message': None,
            'message_class': None,
            'in_watchlist': True
        })
    # If the item is already on the wishlist or can't be added, return an error to the user
    except:
        if WatchlistItem.objects.filter(listing=Listing.objects.get(pk=listing_id), watcher=request.user):
            message = 'This item is already in your watchlist'
            in_watchlist = True
        else:
            message = 'An error occurred while attempting to add this item to your watchlist'
            in_watchlist = False
        return render(request, 'auctions/listing.html', {
            'listing_id': listing_id,
            'listing': Listing.objects.get(pk=listing_id),
            'message': message,
            'message_class': 'error',
            'in_watchlist': in_watchlist
        })


# Remove an item from the user's watch list

def watchlist_remove(request, listing_id):
    try:
        item = WatchlistItem.objects.get(listing=Listing.objects.get(pk=listing_id), watcher=request.user)
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
    return render(request, 'auctions/watchlist.html', {
        'watchlist_items': WatchlistItem.objects.filter(watcher=request.user)
    })



