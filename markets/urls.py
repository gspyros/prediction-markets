from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    path("api/markets", views.MarketsList.as_view()),
    path("api/trades", views.TradeList.as_view()),
    path("api/instruments", views.InstrumentList.as_view()),
    path("api/market_instruments", views.MarketInstruments.as_view()),
    path("api/schedule", views.MarketScheduler.as_view()),
    path("markets", login_required(views.MarketsView.as_view()), name="home"),
]