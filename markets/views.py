import logging

from django.db.models import Q
from django.views.generic import TemplateView
from itertools import groupby
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import MarketSerializer, TradeSerializer, InstrumentSerializer, TradePosSerializer, MarketInstrumentsSerializer
from .models import Market, Instrument, Trade
from .util import *

# Create your views here.


class MarketsView(TemplateView):
    """
    Renders the markets view, displaying a list of available markets and facilitating the buy/sell action.
    """
    template_name = "markets/markets.html"

    def get_context_data(self, **kwargs):
        """
        Prepares the context data for the markets template.

        Retrieves and organizes market data, including:
            - List of available markets (sorted by status).
            - User's available funds (cash position).
            - Instruments within each market.
            - User's positions in each instrument.
            - Number of executed trades (market-wide and user-specific).
            - User's trade history.
            - Price history for a representative instrument ("Yes").
        """
        context = super().get_context_data(**kwargs)
        status_order = ['OPEN', 'PENDING', 'SUSPENDED', 'CLOSED', 'SETTLED']
        user = self.request.user

        all_markets = Market.objects.prefetch_related(
            'instruments', 
            'instruments__positions', 
            'instruments__trades',
        ).all()

        sorted_markets = sorted(all_markets, key=lambda x: status_order.index(x.status))

        context['markets'] = []

        for market in sorted_markets:
            instruments = market.instruments.all()
            traded_instruments = market.instruments.filter(~Q(name = 'Cash'))
            cash_instrument = market.instruments.get(name="Cash")
            cash_pos = cash_instrument.positions.get(user=self.request.user)

            yes_instrument = instruments.get(name="Yes")
            market_price_hist = yes_instrument.historic_prices.all()  # Use reverse relation
            market_price_data = [[elem.market_time_seconds, elem.value] for elem in market_price_hist]

            market_data = {
                'market':market,
                'avail_funds':cash_pos.size,
                'instruments':[],
                'price_history': market_price_data
            }

            market_trades = Trade.objects.order_by('-timestamp').filter(instrument__market=market).all()
            market_trades_executed = market_trades.filter(status=Trade.TradeStatus.EXECUTED).all()
            user_trades = market_trades.filter(user=self.request.user).all()
            user_trades_executed = user_trades.filter(status=Trade.TradeStatus.EXECUTED).all()
            for instrument in traded_instruments:
                position = instrument.positions.get(user=user)
                instrument_data = {
                    'instrument':instrument,
                    'position':position,
                    'projected_return':position.size + cash_pos.size,
                    'outcome_status': instrument.outcome_status
                }
                market_data['instruments'].append(instrument_data)
                market_data.update({'n_market_trades_executed': len(market_trades_executed), 
                                    'n_user_trades_executed': len(user_trades_executed), 
                                    'user_trades': user_trades})
            context['markets'].append(market_data);
        return context


class MarketsList(APIView):
    """
    API endpoint that returns a list of all markets.
    """

    def get(self, request, format=None):
        all_markets = Market.objects.all()
        serializer = MarketSerializer(all_markets, many=True)
        return Response(serializer.data)


class InstrumentList(APIView):
    """
    API endpoint that returns a list of traded instruments.
    """

    def get(self, request, format=None):
        """Handles GET requests to retrieve a list of traded instruments."""
        all_instruments = Instrument.objects.all()
        traded_instruments = all_instruments.filter(~Q(name="Cash")).all()
        serializer = InstrumentSerializer(traded_instruments, many=True)
        return Response(self._transform(serializer.data)) # object keyed by market_id

    def _transform(self, data):
        """Transforms the serialized instrument data into a dictionary keyed by market ID."""
        market_ids = list(set([elem['market_id'] for elem in data]))
        output = {}
        for m_id in market_ids:
            output[m_id] = [elem for elem in data if elem['market_id']== m_id]
        return output
    
class MarketInstruments(APIView):
    """
    API endpoint that returns a list of open markets with their instruments.
    """

    def get(self, request, format=None):
        open_markets = Market.objects.all()
        serializer = MarketInstrumentsSerializer(open_markets, many=True)
        return Response(serializer.data)


class MarketScheduler(APIView):
    """
    API endpoint that schedules markets.
    """
    def get(self, request, format = None):

        markets = Market.objects.filter(
            Q(status="OPEN") | Q(status="PENDING")
        )

        scheduled_markets = []
        errors = []

        for market in markets:
            try:
                market.schedule()
                scheduled_markets.append(market.id)
            except Exception as e:
                errors.append({'market_id': market.id, 'error': str(e)})

        if errors:
            return Response(
                {'status': 'error', 'errors': errors}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        else:
            return Response(
                {'status': 'success', 'scheduled_markets': scheduled_markets}, 
                status=status.HTTP_200_OK
            )


class TradeList(APIView):
    """
    API endpoint for retrieving and creating trades.
    """

    def get(self, request, format=None):
        """Handles GET requests to retrieve a list of trades."""
        user = self.request.user
        user_trades = Trade.objects.filter(user_id=user.id)
        serializer = TradeSerializer(user_trades, many=True)
        return Response(self._transform_trades(serializer.data))

    def post(self, request):
        """Handles POST requests to create a new trade."""
        serializer = TradeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            new_trade = serializer.save(user=self.request.user)
            
            self.process_trade(new_trade)  

            market = new_trade.instrument.market
            market_instruments = market.instruments.all()
            user_positions = [instr.positions.get(user=request.user) for instr in market_instruments]
            
            user_trades = Trade.objects.filter(user=request.user, instrument__market=market, status="EXECUTED").all()  
            n_exec_trades = len(user_trades)
            
            trade_pos_dict = {
                'trade': new_trade,
                'positions': user_positions,
                'n_exec_trades': n_exec_trades
            }
            trade_pos_serializer = TradePosSerializer(trade_pos_dict)
            return Response(self._transform_positions(trade_pos_serializer.data))
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _transform_trades(self, data):
        """Transforms the serialized trade data into a dictionary keyed by market ID."""
        output = {}
        for market_id, trades in groupby(data, key=lambda x: x['market_id']):  
            output[market_id] = list(trades)
        return output
        
    def process_trade(self, trade):
        """Processes a trade by attempting the trade and updating its status."""
        logging.basicConfig()
        logging.debug('Processing trade...')
        trade_metadata = create_trade_metadata(trade)
        try:
            is_trade = attempt_trade(trade, trade_metadata)
            if is_trade:
                trade.success()
            else:
                trade.fail()
        except Exception as e:
            trade.fail()
            logging.exception(str(trade.id) + ' EXCEPTION - ' + str(e))
        return

    def _transform_positions(self, data):
        """Transforms position data for better front-end usability."""
        output = {}
        output['trade'] = data['trade']
        output['n_exec_trades'] = data['n_exec_trades']
        output['positions'] = {}
        for pos in data['positions']:
            output['positions'][pos['instrument']['name']] = pos
        return output
