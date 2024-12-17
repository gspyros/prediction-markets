import datetime

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from accounts.models import CustomUser
from django.utils import timezone

from .pricing import *

# Create your models here.


class Market(models.Model):
    """
    Represents a prediction market.

    A market defines a specific event or question for which predictions are made.
    It manages associated instruments (e.g., Yes/No, outcomes), trading parameters (e.g., currency, starting funds),
    and its lifecycle status (e.g., Pending, Open, Closed, Settled).
    """

    class MarketStatus(models.TextChoices):
        """
        Represents the different lifecycle stages of a prediction market.
    
        PENDING: The market is being set up and is not yet open for trading.
        OPEN: The market is open for trading.
        SUSPENDED: Trading in the market is temporarily halted.
        CLOSED: The market is no longer open for trading, awaiting outcome determination.
        SETTLED: The market's outcome has been determined, and payouts have been calculated.
        """
        PENDING = "PENDING", _('Pending')
        OPEN = "OPEN", _('Open')
        SUSPENDED = "SUSPENDED", _('Suspended')
        CLOSED = "CLOSED", _('Closed')
        SETTLED = "SETTLED", _('Settled')

    class Currencies(models.TextChoices):
        TOK = "TOK", _('Token'),
        EUR = "EUR", _('Euro'),
        USD = "USD", _('United States Dollar')
        GBP = "GBP", _('British Pound')

    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, default="")
    currency = models.CharField(max_length=3, choices=Currencies.choices, default=Currencies.EUR)
    starting_funds = models.FloatField()
    initial_yes_value = models.FloatField(default=0.5)
    status = models.CharField(max_length=12, choices=MarketStatus.choices, default=MarketStatus.PENDING)
    opening_date = models.DateField()
    opening_time = models.TimeField()
    closing_date = models.DateField()
    closing_time = models.TimeField()
    n_exec_trades = models.IntegerField(default=0)
    outcome = models.OneToOneField('Instrument', null=True, blank=True, on_delete=models.SET_NULL, related_name='market_outcome')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, '_state'):
            self.__original_yes_value = self.__dict__.get('initial_yes_value', None)
            self.__original_starting_funds = self.__dict__.get('starting_funds', None)
            self.__original_status = self.__dict__.get('status', None)

    def __str__(self):
        return self.name

    @property
    def n_exec_trades_live(self):
        """Return the number of executed trades for this market."""
        return self.trades.filter(status='EXECUTED').count()
  
    def schedule(self):
        """Open pending markets or close open markets based on the current time."""
        now = timezone.now()
        opening_dt = self._get_opening_dt()
        closing_dt = self._get_closing_dt()
        if opening_dt <= now < closing_dt:
            self.status = Market.MarketStatus.OPEN
        elif now >= closing_dt:
            self.status = Market.MarketStatus.CLOSED
        else:
            return
        self.save()

    def get_internal_time(self):
        """Get internal time for this market (seconds since open datetime)."""
        now = timezone.now()
        opening_dt = self._get_opening_dt()
        return max(0, int((now - opening_dt).total_seconds()))

    def update_n_exec_trades(self, qty = 1):
        """Update the number of executed trades for this market."""
        self.n_exec_trades += qty
        self.save()
    
    def price_instrs(self, source='Initial'):
        instrs = self._get_tradeable_instrs()
        net_positions = [i.net_pos for i in instrs]
        prices = get_prices(net_positions)
        for (instr, price) in zip(instrs, prices):
            instr.set_price(price, source=source)

    def create_instrs(self):
        """
        Create Instruments for this market.
        Creates three instruments: "Yes", "No", and "Cash".  "Yes" and "No" represent the tradable outcomes,
        initialized with prices derived from `initial_yes_value`. "Cash" represents the currency used for trading,
        with a fixed price of 1.0.
        """
        instr_data = {
            'Yes': round(self.initial_yes_value, 2),
            'No': round(1.0 - self.initial_yes_value, 2),
            'Cash': 1.0 
        }
        for name, starting_price in instr_data.items():
            Instrument.objects.create(name=name, market=self, starting_price=starting_price, is_tradeable=(name != 'Cash'))

    def reset_or_create_positions(self):
        """
        Updates or creates instrument positions for all users.
        This method ensures that every user has a position
        for each instrument in the market (Cash, Yes, No).  If a position exists, its size is updated
        to the market's `starting_funds` for Cash and 0 for Yes/No. If no position exists, a new one
        is created with these initial values.
        """
        instrs = self._get_instrs_by_name()
        users = CustomUser.objects.all()
        instr_data = {'Cash': self.starting_funds, 'Yes': 0, 'No': 0}
        for user in users:
            for instr_name, size in instr_data.items():
                instr = instrs[instr_name]
                instr.upd_or_create_position(user, size)
        
    def settle(self):
        """Settle the market: calculate payouts, and mark as SETTLED."""
        self.status = 'SETTLED'
        outcome_instr = self.outcome
        cash_instr = self._get_cash_instr()
        users = CustomUser.objects.all()
        for user in users:
            positions = user.positions
            cash_pos = positions.get(instrument=cash_instr)
            outcome_pos = positions.get(instrument=outcome_instr)
            total_pos = cash_pos.size + outcome_pos.size
            Payout.objects.update_or_create(user=user, market=self, status="PENDING", defaults = {'amount':round(total_pos, 2)})
        
    def unsettle(self):
        """Unsettle the market: remove all payouts and mark as CLOSED."""
        self.status = 'CLOSED'
        payouts = Payout.objects.filter(market=self)
        payouts.delete() 
        
    def save(self, force_insert = False, force_update = False, *args, **kwargs):
        is_new = self._state.adding

        if self.outcome:
            self.settle()
        elif self.__original_status == 'SETTLED':
            self.unsettle()

        super().save(force_insert, force_update, *args, **kwargs)

        if is_new:
            self.create_instrs()
            self.price_instrs('Initial')
            self.reset_or_create_positions()
        else:   
            if self.__original_starting_funds != self.starting_funds:
                self.reset_or_create_positions()
                self.__original_starting_funds = self.starting_funds
            
            if(self.__original_yes_value!= self.initial_yes_value):
                self.price_instrs('Initial')
                self.__original_yes_value = self.initial_yes_value

    def _get_opening_dt(self):
        """Return the opening datetime of the market as a timezone-aware datetime object."""
        return timezone.make_aware(datetime.datetime.combine(self.opening_date, self.opening_time))
    
    def _get_closing_dt(self):
        """Return the closing datetime of the market as a timezone-aware datetime object."""
        return timezone.make_aware(datetime.datetime.combine(self.closing_date, self.closing_time))
    
    def _get_instrs(self):
        """Return a QuerySet of all instruments associated with this market."""
        return Instrument.objects.filter(market=self)  # Simplified

    def _get_cash_instr(self):
        """Return the cash instrument for this market."""
        return self._get_instrs().get(name='Cash') # Simplified

    def _get_tradeable_instrs(self):
        """Return a QuerySet of all tradeable instruments associated with this market."""
        return self._get_instrs().filter(is_tradeable=True) # Simplified

    def _get_instrs_by_name(self):
        """Return a dictionary of instruments keyed by their names."""
        return {i.name: i for i in self._get_instrs()} # Simplified
 
    __original_yes_value = None
    __original_starting_funds = None
    __original_status = None



class Instrument(models.Model):
    """
    Represents an instrument within a prediction market.

    A tradeable instrument can represent a specific outcome (e.g., "Yes", "No"). A cash instrument represents currency ("Cash").
    """

    name = models.CharField(max_length=50)
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='instruments')
    price = models.FloatField(default=0.0)
    price_upd_ts = models.DateTimeField(auto_now_add=True)
    price_upd_mt = models.IntegerField(default=0)
    starting_price = models.FloatField()
    settlement_price = models.FloatField(null=True)
    is_tradeable = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name}'

    @property
    def is_outcome(self):
        """Checks if the instrument represents the outcome of its market."""
        return self.market.outcome == self

    @property
    def outcome_status(self):
        """Returns the outcome status of the instrument (Won/Lost/Pending)."""
        if self.market.status == 'SETTLED':
            return "Won" if self.is_outcome else "Lost"
        return "Pending"

    @property
    def n_trades(self):
        """Returns the number of executed trades for this instrument."""
        return self.trades.filter(status='EXECUTED').count()
    
    @property
    def net_pos(self):
        net_position = sum([p.size for p in self.positions.all()])
        return net_position

    def upd_or_create_position(self, user, size):
        """Create a position for this instrument of the given size on the given user"""
        defaults = {'size': size}
        position = Position.objects.update_or_create(user=user, instrument = self, defaults=defaults)
        return position

    def set_price(self, price, market_time = None, source = "Initial"):
        """Sets the price for the instrument and records it in the HistoricPrice model."""
        self.price = round(price,2)
        self.price_upd_ts = timezone.now()
        if market_time is not None:
            self.price_upd_mt = market_time
        else:
            self.price_upd_mt = self.market.get_internal_time()
        self.save()
        historic_price = HistoricPrice(instrument = self, value=self.price, timestamp = self.price_upd_ts, market_time_seconds = self.price_upd_mt, source = source)
        historic_price.save()


class HistoricPrice(models.Model):
    """
    Stores historical price data for an instrument.
    """

    class PriceSource(models.TextChoices):
        INITIAL = "INITIAL", _('Initial'),
        TRADING = "TRADING", _('Trading'),
        SETTLEMENT = "SETTLEMENT", _('Settlement')

    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name='historic_prices')
    timestamp = models.DateTimeField()
    market_time_seconds = models.PositiveIntegerField(default=0)
    value = models.FloatField()
    source = models.CharField(max_length=10, choices=PriceSource.choices) 


class Position(models.Model):
    """
    Represents a user's position in a specific instrument.
    """

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='positions')
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name='positions')
    size = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])

    def add(self, batch_size):
        self.size += batch_size
        self.save()

    def sub(self, batch_size):
        self.size -= batch_size
        self.save()

    def update(self, size):
        self.size = size
        self.save()

    def save(self, *args, **kwargs):
        if(self.size >= 0):
            super().save(*args, **kwargs)


class Trade(models.Model):
    """
    Represents a trade action performed by a user on an instrument.
    """

    class TradeTypes(models.TextChoices):
        BUY = "BUY", _('Buy'),
        SELL = "SELL", _('Sell')

    class TradeStatus(models.TextChoices):
        PENDING = "PENDING", _('Pending'),
        EXECUTED = "EXECUTED", _('Executed')
        FAILED = "FAILED", _('Failed')

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name="trades")
    shares = models.IntegerField(default=0, verbose_name="Shares Traded")
    type = models.CharField(max_length=4, choices=TradeTypes.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    market_time_seconds = models.IntegerField(default=0)
    status = models.CharField(max_length=12, choices=TradeStatus.choices, default=TradeStatus.PENDING)
    price = models.FloatField(default = 0.0, null=True)

    def fail(self):
        """
        Marks the trade as failed.
        """
        self.status = self.TradeStatus.FAILED
        self.save()

    def success(self):
        """
        Marks the trade as executed.
        """
        self.status = self.TradeStatus.EXECUTED
        self.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == self.TradeStatus.EXECUTED:
            self.instrument.market.update_n_exec_trades()


class Payout(models.Model):
    """
    Represents a payout to a user in a specific market.
    """

    class PayoutStatus(models.TextChoices):
        PENDING = "PENDING", _('Pending'),
        PAID = "PAID", _('Paid'),
        CANCELLED = "CANCELLED", _('Cancelled')

    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='payouts')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    status = models.CharField(max_length=12, choices=PayoutStatus.choices)

    
class TradeMetadata(models.Model):
    """
    Stores metadata associated with a trade.
    """
    trade = models.OneToOneField(Trade, on_delete=models.CASCADE, related_name='trade_metadata')
    cash_before = models.FloatField(default=0.0)
    cash_after = models.FloatField(default=0.0)
    shares_before = models.IntegerField(default=0)
    shares_after = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        self.cash_before = round(self.cash_before, 2)
        self.cash_after = round(self.cash_after, 2)
        super().save(*args, **kwargs)
