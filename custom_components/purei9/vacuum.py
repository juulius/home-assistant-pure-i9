import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.vacuum import (
    SUPPORT_BATTERY,
    SUPPORT_PAUSE,
    SUPPORT_RETURN_HOME,
    SUPPORT_START,
    SUPPORT_STATE,
    SUPPORT_STATUS,
    SUPPORT_STOP,
    SUPPORT_TURN_ON,
    SUPPORT_TURN_OFF,
    StateVacuumEntity,
    PLATFORM_SCHEMA,
    STATE_CLEANING,
    STATE_PAUSED
)
from homeassistant.const import CONF_PASSWORD, CONF_EMAIL
from purei9_unofficial.cloud import CloudClient, CloudRobot
from . import purei9

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_EMAIL): cv.string,
    vol.Required(CONF_PASSWORD): cv.string
})

def setup_platform(hass, config, add_entities, discovery_info = None) -> None:
    client = CloudClient(config[CONF_EMAIL], config.get(CONF_PASSWORD))
    entities = map(PureI9.create, client.getRobots())
    add_entities(entities)

#
# Definitions of supported features: https://github.com/home-assistant/core/blob/dev/homeassistant/components/vacuum/services.yaml
# Source code to vacuum entity: https://github.com/home-assistant/core/tree/dev/homeassistant/components/vacuum
# Source code to entity: https://github.com/home-assistant/core/blob/adab367f0e8c48a68b4dffd0783351b0072fbd0a/homeassistant/helpers/entity.py
# Documentation to vacuum entity: https://developers.home-assistant.io/docs/core/entity/vacuum/
# Home Assistant developers: https://developers.home-assistant.io/
#
class PureI9(StateVacuumEntity):
    def __init__(
        self,
        robot: CloudRobot,
        id: str,
        name: str,
        battery: int,
        state: str,
        available: bool
    ):
        self._robot = robot
        self._id = id
        self._name = name
        self._battery = battery
        self._state = state
        self._available = available

    @staticmethod
    def create(robot: CloudRobot):
        id = robot.getid()
        name = robot.getname()
        battery = purei9.battery_to_hass(robot.getbattery())
        state = purei9.state_to_hass(robot.getstatus())
        available = robot.isconnected()
        return PureI9(robot, id, name, battery, state, available)

    @property
    def unique_id(self) -> str:
        return self._id

    @property
    def available(self) -> bool:
        return self._available

    @property
    def supported_features(self) -> int:
        return (
            SUPPORT_BATTERY
            | SUPPORT_START
            | SUPPORT_RETURN_HOME
            | SUPPORT_STOP
            | SUPPORT_PAUSE
            | SUPPORT_TURN_ON
            | SUPPORT_TURN_OFF
            | SUPPORT_STATE
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def battery_level(self) -> int:
        return self._battery

    @property
    def state(self) -> str:
        return self._state

    @property
    def error(self) -> str:
        # According to documentation then this is required if the entity can report error states
        # However, I can't fetch any error message
        return "Error"

    @property
    def is_on(self) -> bool:
        return self._state == STATE_CLEANING

    def start(self) -> None:
        if self._state != STATE_CLEANING:
            self._robot.startclean()

    def return_to_base(self) -> None:
        self._robot.gohome()

    def stop(self) -> None:
        self._robot.stopclean()

    def pause(self) -> None:
        if self._state != STATE_PAUSED:
            self._robot.pauseclean()

    def turn_on(self) -> None:
        self.start()

    def turn_off(self) -> None:
        self.stop()
        self.return_to_base()

    def update(self) -> None:
        battery = self._robot.getbattery()

        self._battery = purei9.battery_to_hass(battery)
        self._state = purei9.state_to_hass(self._robot.getstatus(), battery)
        self._available = self._robot.isconnected()
