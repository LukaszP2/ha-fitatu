"""Test Fitatu sensors."""

import unittest
from unittest.mock import MagicMock

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfMass

from custom_components.fitatu.const import CONF_USER_ID
from custom_components.fitatu.sensor import (
    SENSORS,
    FitatuValueSensor,
    FitatuWeightSensor,
)


class TestFitatuSensors(unittest.TestCase):
    """Test suite for Fitatu sensors."""

    def test_sensors_state_class(self):
        """Test that daily reset sensors do not have state_class TOTAL and calories don't have ENERGY."""
        for sensor_desc in SENSORS:
            # Check state_class
            self.assertNotEqual(
                sensor_desc.state_class,
                SensorStateClass.TOTAL,
                f"Sensor {sensor_desc.key} must not have state_class TOTAL",
            )
            # Check device_class for calories/activities
            if "calorie" in sensor_desc.key or "activity" in sensor_desc.key:
                self.assertNotEqual(
                    sensor_desc.device_class,
                    SensorDeviceClass.ENERGY,
                    f"Food/activity sensor {sensor_desc.key} must not have device_class ENERGY",
                )

    def test_value_sensor(self):
        """Test value sensor attributes and state."""
        entry = MagicMock()
        entry.data = {CONF_USER_ID: "999"}
        coordinator = MagicMock()
        coordinator.data = {"energy_eaten": 1850, "date": "2026-11-06"}

        desc = next(s for s in SENSORS if s.key == "calories_eaten")
        sensor = FitatuValueSensor(entry, coordinator, desc)

        self.assertEqual(sensor.unique_id, "999_calories_eaten")
        self.assertEqual(sensor.native_value, 1850)
        self.assertEqual(sensor.extra_state_attributes, {"date": "2026-11-06"})

    def test_weight_sensor(self):
        """Test weight sensor unit conversion and values."""
        entry = MagicMock()
        entry.data = {CONF_USER_ID: "999"}
        coordinator = MagicMock()

        # Known unit KG
        coordinator.data = {"weight": 82.5, "weight_unit": "KG", "weight_date": "2026-11-05"}
        sensor = FitatuWeightSensor(entry, coordinator)
        self.assertEqual(sensor.native_unit_of_measurement, UnitOfMass.KILOGRAMS)
        self.assertEqual(sensor.native_value, 82.5)
        self.assertEqual(sensor.extra_state_attributes, {"date": "2026-11-05"})

        # Known unit LB
        coordinator.data = {"weight": 180.0, "weight_unit": "LBS", "weight_date": "2026-11-05"}
        self.assertEqual(sensor.native_unit_of_measurement, UnitOfMass.POUNDS)
        self.assertEqual(sensor.native_value, 180.0)

        # Unknown unit
        coordinator.data = {"weight": 82.5, "weight_unit": "UNKNOWN", "weight_date": "2026-11-05"}
        self.assertIsNone(sensor.native_unit_of_measurement)
        self.assertIsNone(sensor.native_value)

    def test_sensors_none_data_safety(self):
        """Test sensors safely return None/empty when coordinator.data is None."""
        entry = MagicMock()
        entry.data = {CONF_USER_ID: "999"}
        coordinator = MagicMock()
        coordinator.data = None

        desc = next(s for s in SENSORS if s.key == "calories_eaten")
        value_sensor = FitatuValueSensor(entry, coordinator, desc)
        self.assertIsNone(value_sensor.native_value)
        self.assertEqual(value_sensor.extra_state_attributes, {})

        weight_sensor = FitatuWeightSensor(entry, coordinator)
        self.assertIsNone(weight_sensor.native_unit_of_measurement)
        self.assertIsNone(weight_sensor.native_value)
        self.assertEqual(weight_sensor.extra_state_attributes, {})

    def test_water_sensor_config(self):
        """Test water sensor has None device_class and MEASUREMENT state_class for LTS."""
        water_desc = next(s for s in SENSORS if s.key == "water")
        self.assertIsNone(water_desc.device_class)
        self.assertEqual(water_desc.state_class, SensorStateClass.MEASUREMENT)
