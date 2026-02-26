
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Place, Flight, Passenger, Ticket, Week


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            data['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return data


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ['id', 'city', 'airport', 'code', 'country']


class WeekSerializer(serializers.ModelSerializer):
    class Meta:
        model = Week
        fields = ['id', 'number', 'name']


class FlightSerializer(serializers.ModelSerializer):
    origin = PlaceSerializer(read_only=True)
    destination = PlaceSerializer(read_only=True)
    depart_day = WeekSerializer(many=True, read_only=True)
    # Include flight_number in serialization

    class Meta:
        model = Flight
        fields = [
            'id', 'origin', 'destination', 'depart_time', 'depart_day',
            'duration', 'arrival_time', 'plane', 'airline', 'flight_number',
            'economy_fare', 'business_fare', 'first_fare'
        ]


class PassengerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passenger
        fields = ['id', 'first_name', 'last_name', 'gender']


class TicketSerializer(serializers.ModelSerializer):
    passengers = PassengerSerializer(many=True, read_only=True)
    flight = FlightSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'ref_no', 'user', 'passengers', 'flight',
            'flight_ddate', 'flight_adate', 'flight_fare', 'other_charges',
            'coupon_used', 'coupon_discount', 'total_fare', 'seat_class',
            'booking_date', 'mobile', 'email', 'status'
        ]


class FlightSearchSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=3)
    destination = serializers.CharField(max_length=3)
    depart_date = serializers.DateField()
    seat_class = serializers.ChoiceField(choices=['economy', 'business', 'first'])
    trip_type = serializers.ChoiceField(choices=['1', '2'], default='1')  # 1=one-way, 2=round-trip
    return_date = serializers.DateField(required=False)


class BookingSerializer(serializers.Serializer):
    flight_id = serializers.IntegerField()
    flight_date = serializers.DateField()
    seat_class = serializers.ChoiceField(choices=['economy', 'business', 'first'])
    passengers = PassengerSerializer(many=True)
    mobile = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    country_code = serializers.CharField(max_length=5, default='+91')
