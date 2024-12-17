from .models import Position, TradeMetadata
from .pricing import get_cost_of_trade
from django.db import transaction
import logging

logging.basicConfig()

def create_trade_metadata(trade):
    """
    Create a TradeMetadata object for a given trade.
    """
    trade_metadata = TradeMetadata(trade = trade)
    trade_metadata.shares_before = 0
    trade_metadata.shares_after = 0
    trade_metadata.cash_before = 0
    trade_metadata.cash_after = 0
    trade_metadata.save()
    return trade_metadata

@transaction.atomic()
def attempt_trade(trade, trade_metadata):
    """
    Attempt to execute a trade atomically.
    """
    market = trade.instrument.market
    instr_to_trade = trade.instrument
    tradeable_instruments = market._get_tradeable_instrs()
    cash_instr = market._get_cash_instr()
    traded_shares = trade.shares

    if instr_to_trade not in tradeable_instruments:
        return False
    elif market.status != "OPEN":
        return False

    #Fetch and lock user's market positions.
    user_market_trade_pos = Position.objects.filter(instrument=instr_to_trade, user=trade.user).select_for_update()[0]
    user_market_cash_pos = Position.objects.filter(instrument=cash_instr, user=trade.user).select_for_update()[0]
    
    #Create the trade metadata object
    trade_metadata.shares_before = user_market_trade_pos.size
    trade_metadata.cash_before = user_market_cash_pos.size

    #Get cost of trade
    instrument_positions = {}
    for i in tradeable_instruments:
        instrument_positions[i.name] = i.net_pos
    cost = get_cost_of_trade(instrument_positions, instr_to_trade.name, traded_shares)

    #Validate and attempt trade
    if cost > user_market_cash_pos.size:
        return False
    elif user_market_trade_pos.size + traded_shares < 0:
        return False
    else:
        #Update the positions
        user_market_trade_pos.add(traded_shares)
        logging.debug(f'''TradeID {trade.id} - user_market_trade_pos.add({traded_shares})''')
        user_market_cash_pos.sub(cost)
        logging.debug(f'''TradeID {trade.id} - Cash Movement ({cost})''')
        trade.price = round(cost, 2)
        market.price_instrs(source="Trading")

        trade_metadata.shares_after = user_market_trade_pos.size
        trade_metadata.cash_after = user_market_cash_pos.size
        trade_metadata.save()
        return True