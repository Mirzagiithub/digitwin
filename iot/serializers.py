from rest_framework import serializers
from .models import (
    TelemetryData,
    Alert,
    Device,
    Sensor,
    Command
)

class TelemetryDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemetryData
        fields = '__all__'


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'


class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = '__all__'


class CommandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Command
        fields = '__all__'
