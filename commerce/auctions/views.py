# Note:  This submission is based on homework I submitted when I took this class in Spring 2021
#        I have added comments marked "POST-GRADING" to show where I made changes based on Vlad's grading feedback
#        Other changes that were not based on TF feedback are not called out.

from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import Http404
from django.shortcuts import render
from django.urls import reverse
from django.db.models import Max
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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
            messages.error(request, 'Invalid username and/or password.')

    return render(request, 'auctions/login.html')


# Log out

def logout_view(request):
    logout(request)
    # We don't need to unset the timezone; that is done when index is called
    return HttpResponseRedirect(reverse('index'))


# Register a new user

def register(request):
    # Gather a list of timezones to populate the timezone choice field in the form
    timezones = pytz.common_timezones

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']

        # Ensure password matches confirmation and is not empty
        password = request.POST['password']
        confirmation = request.POST['confirmation']
        if password != confirmation:
            messages.error(request, 'Passwords must match')
            # return HttpResponseRedirect('register')
            return render(request, 'auctions/register.html', {
                'timezones': timezones,
                'default_timezone': settings.DEFAULT_TIMEZONE
            })
        if password == '':
            messages.error(request, 'Password cannot be blank')
            return render(request, 'auctions/register.html', {
                'timezones': timezones,
                'default_timezone': settings.DEFAULT_TIMEZONE
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.timezone = request.POST['user_timezone']
            user.save()
        except IntegrityError:
            messages.error(request, 'Username already taken.')
            return render(request, 'auctions/register.html', {
                'timezones': timezones,
                'default_timezone': settings.DEFAULT_TIMEZONE
            })
        login(request, user)
        # Set the display timezone to the user's chosen time
        timezone.activate(user.timezone)
        # Send the user to the home page
        return HttpResponseRedirect(reverse('index'))

    else:
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

def listing_view(request, listing_id):
    # CITATION:  error checking based on cookbook example in Vlad's section
    try:
        listing = Listing.objects.get(pk=listing_id)
    except Listing.DoesNotExist:
        raise Http404("Listing does not exist")

    # Determine whether this listing is in the user's watchlist
    if request.user.is_authenticated:
        # POST-GRADING:  Didn't realize request.user was already a User object
        in_watchlist = listing in request.user.watchlist_items.all()
    else:
        in_watchlist = False

    # Render the listing detail page
    return render(request, 'auctions/listing.html', {
        'listing_id': listing_id,
        'listing': listing,
        'in_watchlist': in_watchlist,
        'comments': Comment.objects.filter(listing=listing_id).order_by('timestamp'),
        'comment_form': CommentForm(initial={'listing': listing_id}),
        'bid_form': BidForm(initial={'listing': listing})
    })


# Create a new listing

@login_required
def listing_add(request):
    # If we're posting data, attempt to process the form
    if request.method == 'POST':
        form = ListingForm(request.POST)
        if form.is_valid():
            # POST-GRADING:  Model form handling refactored based on the cookbook example from Vlad's section
            # Save the new listing locally, so we can add the owner attribute
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.save()
            return listing_view(request, listing.id)
        else:
            messages.error(
                request, 'Invalid form entry.  Please fix the issues below and resubmit.')
            return render(request, 'auctions/new_listing.html', {
                'listing_form': form
            })
    # It we're not posting, load the page with a blank new listing form
    # POST-GRADING:  Merged the "new form" functionality into this function based on Vlad's feedback
    else:
        return render(request, 'auctions/new_listing.html', {
            'listing_form': ListingForm()
        })


# Close a listing:  ends the auction, making the highest bidder the winner

@login_required
def close_listing(request, listing_id):
    # Mark the listing as closed
    try:
        listing = Listing.objects.get(pk=listing_id)
    except Listing.DoesNotExist:
        raise Http404("Listing does not exist")

    # TO DO: error handling
    listing.is_active = False
    listing.save()
    # Re-render the page with the new information
    return listing_view(request, listing_id)


# WATCHLIST METHODS

# Display the user's watchlist

@login_required
def watchlist_view(request):
    # Gather the current user's watchlist
    # POST-GRADING:  Didn't realize that request.user was already a User object
    watchlist_items = request.user.watchlist_items.all()
    return index(request, watchlist_items, 'My Watchlist')


# Add a listing to the user's watchlist
# NOTE:  I chose to allow users to include their own listings and closed listings on their watch lists,
#           since we are not providing any other way for users to track those things

@login_required
def watchlist_add(request, listing_id):
    try:
        listing = Listing.objects.get(pk=listing_id)
        listing.watchlist_items.add(request.user)
        messages.success(request, 'This item has been added to your watchlist')
    except Exception:
        messages.error(
            request, 'An error occurred while attempting to add this item to your watchlist')
    finally:
        return HttpResponseRedirect(reverse('listing', args=[listing_id]))


# Remove a listing from the user's watchlist

@login_required
def watchlist_remove(request, listing_id):
    try:
        listing = Listing.objects.get(pk=listing_id)
        listing.watchlist_items.remove(request.user)
        # .remove() does not give an error if the item is not in the watchlist,
        # but we don't need to show the user an error - either way, the item ends up not in the list
        messages.success(
            request, 'This item has been removed from your watchlist')
    except Exception:
        # If this fails for any other reason, return an error to the user
        messages.error(
            request, 'An error occurred while attempting to remove this item from your watchlist')
    finally:
        return HttpResponseRedirect(reverse('listing', args=[listing_id]))


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
        try:
            category_name = Category.objects.get(pk=category_id).name
        except Category.DoesNotExist:
            raise Http404("Category does not exist")
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
            # POST-GRADING:  Model form handling refactored based on the cookbook example from Vlad's section
            # Save the comment locally first, so we can add the commenter and timestamp
            comment = form.save(commit=False)
            # Non-empty body validation is performed on the model level, but let's double-check
            if comment.body:
                comment.commenter = request.user
                comment.timestamp = datetime.datetime.now()
                comment.save()
                messages.success(request, 'Thank you for your comment')
            else:
                messages.error(request, 'Your comment cannot be blank.')
            # Refresh the listing page and show a success or error message
            return HttpResponseRedirect(reverse('listing', args=[comment.listing.id]))

        else:
            messages.error(
                request, 'An error occurred while processing your submission.  Your comment has NOT been saved.')
            # If we don't have a valid form, we don't have a listing ID, so take the user back to the index
            return HttpResponseRedirect(reverse('index'))


# BIDDING METHODS

# Submit a bid

@login_required
def bid_add(request):
    if request.method == 'POST':
        form = BidForm(request.POST)
        if form.is_valid():
            # POST-GRADING:  Model form handling refactored based on the cookbook example from Vlad's section
            # Save the bid locally so we can test
            bid = form.save(commit=False)
            listing = bid.listing
            # Validate the form on the backend
            if bid.amount < listing.required_bid:
                messages.error(
                    request, f'You must bid at least ${listing.required_bid}')
            elif listing.owner == request.user:
                messages.error(
                    request, 'You may not bid on your own listings.')
            elif not listing.is_active:
                messages.error(request, 'Sorry, this auction has ended.')
            # If all validation passes, save the bid
            else:
                bid.bidder = request.user
                bid.timestamp = datetime.datetime.now()
                bid.save()
                messages.success(request, 'Thank you for your bid')
            # Refresh the listing page and show a success or error message
            return HttpResponseRedirect(reverse('listing', args=[listing.id]))
        # If we don't have a valid form, we don't have a listing ID, so take the user back to the index
        else:
            messages.error(
                request, 'An error occurred while validating your bid.  Your bid has NOT been saved.')
            return HttpResponseRedirect(reverse('index'))
