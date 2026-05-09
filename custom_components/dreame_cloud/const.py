"""Constants for the Dreame Vacuum Cloud integration."""

DOMAIN = "dreame_cloud"

# Config entry keys
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_REGION = "region"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_DEVICE_ID = "device_id"
CONF_HOST_PREFIX = "host_prefix"

# Defaults
DEFAULT_REGION = "sg"
DEFAULT_SCAN_INTERVAL = 30  # seconds

# API
AUTH_URL_TEMPLATE = "https://{region}.iot.dreame.tech:13267/dreame-auth/oauth/token"
API_URL_TEMPLATE = "https://{region}.iot.dreame.tech:13267/dreame-iot-com-{host_prefix}/device/sendCommand"
DEVICE_LIST_URL_TEMPLATE = "https://{region}.iot.dreame.tech:13267/dreame-user-iot/iotuserbind/device/listV2"

BASIC_AUTH = "Basic ZHJlYW1lX2FwcHYxOkFQXmR2QHpAU1FZVnhOODg="
USER_AGENT = "Dreame_Smarthome/2.1.9 (iPhone; iOS 18.4.1; Scale/3.00)"
TENANT_ID = "000000"
PASSWORD_SALT = "RAylYC%fmSKp7%Tq"

REGIONS = ["sg", "cn", "eu", "us"]

# Property mappings (siid, piid)
PROP_BATTERY_LEVEL = (3, 1)
PROP_CHARGING_STATUS = (3, 2)
PROP_STATUS = (4, 1)
PROP_LAST_CLEAN_TIME = (4, 2)
PROP_LAST_CLEAN_AREA = (4, 3)
PROP_SUCTION_LEVEL = (4, 4)
PROP_WATER_VOLUME = (4, 5)
PROP_TASK_STATUS = (4, 7)
PROP_FAULTS = (4, 18)
PROP_SELF_WASH_BASE_STATUS = (4, 25)
PROP_MOP_IN_STATION = (4, 52)
PROP_MOP_PAD_INSTALLED = (4, 53)
PROP_SHORTCUTS = (4, 48)
PROP_MAIN_BRUSH_LIFE = (9, 2)
PROP_SIDE_BRUSH_LIFE = (10, 2)
PROP_FILTER_LIFE = (11, 2)
PROP_SENSOR_DIRTY = (16, 2)
PROP_MOP_PAD_LIFE = (18, 2)
PROP_TOTAL_CLEAN_TIME = (12, 2)
PROP_TOTAL_CLEAN_AREA = (12, 4)

# Actions (siid, aiid)
ACTION_START = (2, 1)
ACTION_PAUSE = (2, 2)
ACTION_CHARGE = (3, 1)
ACTION_START_CUSTOM = (4, 1)
ACTION_STOP = (4, 2)

# Status codes
STATUS_MAP = {
    3: "charging",
    6: "wifi_setup",
    9: "error",
    11: "sleeping",
    14: "sleeping",
    17: "standby",
    18: "room_cleaning",
    19: "zone_cleaning",
    20: "spot_cleaning",
    24: "summon_clean",
    25: "shortcut_running",
}

CHARGING_STATUS_MAP = {
    0: "not_charging",
    1: "charging",
    2: "discharging",
    5: "returning",
}

SUCTION_MAP = {
    0: "quiet",
    1: "standard",
    2: "strong",
    3: "turbo",
}

WATER_MAP = {
    0: "off",
    1: "low",
    2: "medium",
    3: "high",
}

TASK_STATUS_MAP = {
    0: "none",
    1: "auto_clean",
    3: "room_clean",
    5: "shortcut",
    7: "scheduled",
}

ERROR_MAP = {
    0: "none",
    1: "drop_sensor",
    2: "cliff_sensor",
    3: "bumper_hit",
    4: "gesture",
    8: "dustbox_missing",
    10: "water_empty",
    11: "dustbox_full",
    12: "main_brush",
    13: "side_brush",
    14: "fan",
    19: "charger_issue",
    20: "battery_low",
    21: "charge_fault",
}

# Shortcut status value used in START_CUSTOM
SHORTCUT_STATUS_VALUE = 25
CLEANING_PROPERTIES_PIID = 10
STATUS_PIID = 1
