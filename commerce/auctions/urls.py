from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("listing/<int:listing_id>", views.listing_view, name="listing"),
    path("watchlist/<int:listing_id>", views.watchlist_add, name="watchlist_add"),
    path("watchlist_remove/<int:listing_id>", views.watchlist_remove, name="watchlist_remove"),
    path("watchlist", views.watchlist_view, name="watchlist_view"),
    path("close/<int:listing_id>", views.close_listing, name="close_listing"),
    path("comment_add", views.comment_add, name="comment_add"),
    path("bid_add", views.bid_add, name="bid_add"),


    # TEMP FOR TESTING
    path('dev', views.dev, name="dev")
]
