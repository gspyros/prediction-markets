from rest_framework import serializers

from .models import Market, Instrument, Trade, Position


class MarketSerializer(serializers.ModelSerializer):
    """
    Serializer for the Market model.
    """

    class Meta:
        model = Market
        fields = ['id','name','status']


class InstrumentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Instrument model. Includes the current market time (seconds).
    """

    current_mt = serializers.SerializerMethodField()

    def get_current_mt(self, obj):
        return obj.market.get_internal_time()

    class Meta:
        model = Instrument
        fields = ['id','name','price','price_upd_mt','market_id','current_mt','outcome_status']
        select_related = ['market']


class TradeSerializer(serializers.ModelSerializer):
    """
    Serializes Trade model instances.
    """

    market_id = serializers.SerializerMethodField()
    instrument_name = serializers.SerializerMethodField()

    def get_market_id(self, obj):
        return obj.instrument.market.id

    def get_instrument_name(self, obj):
        return obj.instrument.name

    def validate(self, data):
        if data['type'] == "BUY" and data['shares'] < 0.0:
            raise serializers.ValidationError("A BUY trade requires a positive number of shares")
        elif data['type'] == "SELL" and data['shares'] > 0.0:
            raise serializers.ValidationError("A SELL trade requires a negative number of shares")
        return data

    def get_current_user(self, obj):
        request = self.context.get('request', None)
        if request:
            return request.user.id

    class Meta:
        model = Trade
        fields = ['id', 'instrument', 'instrument_name', 'type', 'shares', 'timestamp', 'market_id', 'status', 'price']
        select_related = ('instrument__market',)


class PositionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Position model.
    """

    class Meta:
        model = Position
        exclude = ('user',)
        depth = 1


class TradePosSerializer(serializers.Serializer):
    """
    Serializer for combining trade and position data.
    """
    trade = TradeSerializer()
    positions = PositionSerializer(many=True)
    n_exec_trades = serializers.IntegerField()


class MarketInstrumentsSerializer(serializers.ModelSerializer):
    """
    Serializer for the Market model, including detailed information about its instruments.
    """
    instruments = InstrumentSerializer(many=True)

    class Meta:
        model = Market
        fields = ('id', 'status', 'n_exec_trades', 'instruments',)
        depth: 3
