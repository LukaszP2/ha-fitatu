"""Constants for the Fitatu integration."""

from datetime import timedelta

DOMAIN = "fitatu"
CONF_SESSION = "session"
CONF_USER_ID = "user_id"

PLATFORMS = ["sensor"]
UPDATE_INTERVAL = timedelta(minutes=30)

SENSOR_CALORIES_EATEN = "calories_eaten"

CATEGORY_CORE = "core"
CATEGORY_NUTRITION = "nutrition"
CATEGORY_HYDRATION = "hydration"
CATEGORY_ACTIVITY = "activity"
CATEGORY_BODY = "body"
CATEGORY_ADVANCED = "advanced"

MONITORING_CATEGORIES = (
    CATEGORY_CORE,
    CATEGORY_NUTRITION,
    CATEGORY_HYDRATION,
    CATEGORY_ACTIVITY,
    CATEGORY_BODY,
    CATEGORY_ADVANCED,
)

DEFAULT_MONITORING_CATEGORIES = MONITORING_CATEGORIES
