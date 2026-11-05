"""Read-only monitoring sensors for Fitatu."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfMass, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FitatuConfigEntry
from .const import (
    CATEGORY_ACTIVITY,
    CATEGORY_ADVANCED,
    CATEGORY_BODY,
    CATEGORY_CORE,
    CATEGORY_HYDRATION,
    CATEGORY_NUTRITION,
    CONF_USER_ID,
    DEFAULT_MONITORING_CATEGORIES,
    DOMAIN,
)
from .coordinator import FitatuCoordinator


@dataclass(frozen=True, kw_only=True)
class FitatuSensorDescription(SensorEntityDescription):
    """Describe a normalized Fitatu sensor."""

    data_key: str
    category: str


SENSORS: tuple[FitatuSensorDescription, ...] = (
    FitatuSensorDescription(
        key="calories_eaten",
        translation_key="calories_eaten",
        data_key="energy_eaten",
        category=CATEGORY_CORE,
        native_unit_of_measurement=UnitOfEnergy.KILO_CALORIE,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),
    FitatuSensorDescription(
        key="calories_target_min",
        translation_key="calories_target_min",
        data_key="energy_min",
        category=CATEGORY_CORE,
        native_unit_of_measurement=UnitOfEnergy.KILO_CALORIE,
        device_class=SensorDeviceClass.ENERGY,
    ),
    FitatuSensorDescription(
        key="calories_target_max",
        translation_key="calories_target_max",
        data_key="energy_max",
        category=CATEGORY_CORE,
        native_unit_of_measurement=UnitOfEnergy.KILO_CALORIE,
        device_class=SensorDeviceClass.ENERGY,
    ),
    FitatuSensorDescription(
        key="calories_planned",
        translation_key="calories_planned",
        data_key="energy_current",
        category=CATEGORY_NUTRITION,
        native_unit_of_measurement=UnitOfEnergy.KILO_CALORIE,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),
    FitatuSensorDescription(
        key="protein_eaten",
        translation_key="protein_eaten",
        data_key="protein_eaten",
        category=CATEGORY_NUTRITION,
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.TOTAL,
    ),
    FitatuSensorDescription(
        key="protein_planned",
        translation_key="protein_planned",
        data_key="protein_current",
        category=CATEGORY_NUTRITION,
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.TOTAL,
    ),
    FitatuSensorDescription(
        key="protein_target_min",
        translation_key="protein_target_min",
        data_key="protein_min",
        category=CATEGORY_NUTRITION,
        native_unit_of_measurement=UnitOfMass.GRAMS,
    ),
    FitatuSensorDescription(
        key="protein_target_max",
        translation_key="protein_target_max",
        data_key="protein_max",
        category=CATEGORY_NUTRITION,
        native_unit_of_measurement=UnitOfMass.GRAMS,
    ),
    FitatuSensorDescription(
        key="fat_eaten",
        translation_key="fat_eaten",
        data_key="fat_eaten",
        category=CATEGORY_NUTRITION,
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.TOTAL,
    ),
    FitatuSensorDescription(
        key="fat_planned",
        translation_key="fat_planned",
        data_key="fat_current",
        category=CATEGORY_NUTRITION,
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.TOTAL,
    ),
    FitatuSensorDescription(
        key="fat_target_min",
        translation_key="fat_target_min",
        data_key="fat_min",
        category=CATEGORY_NUTRITION,
        native_unit_of_measurement=UnitOfMass.GRAMS,
    ),
    FitatuSensorDescription(
        key="fat_target_max",
        translation_key="fat_target_max",
        data_key="fat_max",
        category=CATEGORY_NUTRITION,
        native_unit_of_measurement=UnitOfMass.GRAMS,
    ),
    FitatuSensorDescription(
        key="carbohydrate_eaten",
        translation_key="carbohydrate_eaten",
        data_key="carbohydrate_eaten",
        category=CATEGORY_NUTRITION,
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.TOTAL,
    ),
    FitatuSensorDescription(
        key="carbohydrate_planned",
        translation_key="carbohydrate_planned",
        data_key="carbohydrate_current",
        category=CATEGORY_NUTRITION,
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.TOTAL,
    ),
    FitatuSensorDescription(
        key="carbohydrate_target_min",
        translation_key="carbohydrate_target_min",
        data_key="carbohydrate_min",
        category=CATEGORY_NUTRITION,
        native_unit_of_measurement=UnitOfMass.GRAMS,
    ),
    FitatuSensorDescription(
        key="carbohydrate_target_max",
        translation_key="carbohydrate_target_max",
        data_key="carbohydrate_max",
        category=CATEGORY_NUTRITION,
        native_unit_of_measurement=UnitOfMass.GRAMS,
    ),
    FitatuSensorDescription(
        key="water",
        translation_key="water",
        data_key="water",
        category=CATEGORY_HYDRATION,
        native_unit_of_measurement=UnitOfVolume.MILLILITERS,
        device_class=SensorDeviceClass.VOLUME,
        state_class=SensorStateClass.TOTAL,
    ),
    FitatuSensorDescription(
        key="water_target",
        translation_key="water_target",
        data_key="water_target",
        category=CATEGORY_HYDRATION,
        native_unit_of_measurement=UnitOfVolume.MILLILITERS,
        device_class=SensorDeviceClass.VOLUME,
    ),
    FitatuSensorDescription(
        key="activity_energy",
        translation_key="activity_energy",
        data_key="activity_energy",
        category=CATEGORY_ACTIVITY,
        native_unit_of_measurement=UnitOfEnergy.KILO_CALORIE,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),
    FitatuSensorDescription(
        key="activity_count",
        translation_key="activity_count",
        data_key="activity_count",
        category=CATEGORY_ACTIVITY,
        native_unit_of_measurement="activities",
        state_class=SensorStateClass.TOTAL,
    ),
    FitatuSensorDescription(
        key="food_item_count",
        translation_key="food_item_count",
        data_key="food_item_count",
        category=CATEGORY_ADVANCED,
        native_unit_of_measurement="items",
        state_class=SensorStateClass.TOTAL,
    ),
    FitatuSensorDescription(
        key="bmr",
        translation_key="bmr",
        data_key="bmr",
        category=CATEGORY_ADVANCED,
        native_unit_of_measurement="kcal/day",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    FitatuSensorDescription(
        key="tmr",
        translation_key="tmr",
        data_key="tmr",
        category=CATEGORY_ADVANCED,
        native_unit_of_measurement="kcal/day",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FitatuConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add the selected monitoring sensors."""
    enabled_categories = set(
        entry.options.get("categories", DEFAULT_MONITORING_CATEGORIES)
    )
    entities: list[SensorEntity] = [
        FitatuValueSensor(entry, entry.runtime_data, description)
        for description in SENSORS
        if description.category in enabled_categories
    ]
    if CATEGORY_BODY in enabled_categories:
        entities.append(FitatuWeightSensor(entry, entry.runtime_data))
    async_add_entities(entities)


class FitatuValueSensor(CoordinatorEntity[FitatuCoordinator], SensorEntity):
    """Expose one normalized daily value."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: FitatuConfigEntry,
        coordinator: FitatuCoordinator,
        description: FitatuSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.data[CONF_USER_ID]}_{description.key}"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> float | int | None:
        """Return the latest normalized value."""
        return self.coordinator.data.get(self.entity_description.data_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Identify the local date for daily values."""
        return {"date": self.coordinator.data.get("date")}


class FitatuWeightSensor(CoordinatorEntity[FitatuCoordinator], SensorEntity):
    """Expose the latest recorded body mass when its unit is known."""

    _attr_has_entity_name = True
    _attr_translation_key = "weight"
    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, entry: FitatuConfigEntry, coordinator: FitatuCoordinator
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.data[CONF_USER_ID]}_weight"
        self._attr_device_info = _device_info(entry)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return a recognized unit from the service response."""
        unit = self.coordinator.data.get("weight_unit")
        if unit in {"KG", "KILOGRAM", "KILOGRAMS"}:
            return UnitOfMass.KILOGRAMS
        if unit in {"LB", "LBS", "POUND", "POUNDS"}:
            return UnitOfMass.POUNDS
        return None

    @property
    def native_value(self) -> float | None:
        """Return the latest mass only when its unit is known."""
        if self.native_unit_of_measurement is None:
            return None
        return self.coordinator.data.get("weight")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the date of the last measurement."""
        return {"date": self.coordinator.data.get("weight_date")}


def _device_info(entry: FitatuConfigEntry) -> DeviceInfo:
    """Build a stable service device for this Fitatu account."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.data[CONF_USER_ID])},
        name="Fitatu",
        manufacturer="Fitatu",
        entry_type=DeviceEntryType.SERVICE,
    )
