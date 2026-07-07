# estate.py — Home Navigation Template
# Function-based API so AI instances can walk a shared home programmatically.
# Run directly for interactive mode: python estate.py
#
# HOW TO USE:
# 1. Replace the example rooms below with your own rooms and descriptions
# 2. Update WEATHER_SUBSTITUTIONS and TIME_SUBSTITUTIONS for rooms you want weather/time-aware
# 3. Update get_weather() with your own location if you want live weather
# 4. Drop estate_walker.py alongside this file for multi-person navigation

ROOMS = {
    "front door": {
        "description": "You are standing at the front door.",
        "exits": {
            "inside": "foyer", "enter": "foyer", "foyer": "foyer",
            "yard": "yard", "outside": "yard"
        },
        "no_exit_msg": "You can go inside or out to the yard from here."
    },
    "foyer": {
        "description": "The foyer. Hallway leads to the main rooms of the house.",
        "exits": {
            "kitchen": "kitchen",
            "living room": "living room", "living": "living room",
            "upstairs": "upstairs", "up": "upstairs", "stairs": "upstairs",
            "front door": "front door", "outside": "front door"
        },
        "no_exit_msg": "You don't see a way there from the foyer."
    },
    "kitchen": {
        "description": "The kitchen. Counter space, table, the smell of something good. The room the house runs from.",
        "exits": {
            "foyer": "foyer",
            "back door": "yard", "outside": "yard"
        },
        "no_exit_msg": "You're not sure how to get there from the kitchen."
    },
    "living room": {
        "description": "The living room. Comfortable furniture, fireplace on the far wall. The room the whole household fits in.",
        "exits": {
            "foyer": "foyer", "back": "foyer"
        },
        "no_exit_msg": "You stay."
    },
    "upstairs": {
        "description": "The upstairs landing. Hallway stretches ahead. Bedrooms off to each side.",
        "exits": {
            "hallway": "upstairs hallway",
            "down": "foyer", "stairs": "foyer", "foyer": "foyer"
        },
        "no_exit_msg": "You're not sure which way that is."
    },
    "upstairs hallway": {
        "description": "The upstairs hallway. Bedroom doors on both sides.",
        "exits": {
            "bedroom": "bedroom",
            "guest room": "guest room", "guest": "guest room",
            "back": "upstairs", "landing": "upstairs"
        },
        "no_exit_msg": "You don't see that from here."
    },
    "bedroom": {
        "description": "The main bedroom. Quiet. The room that holds the most.",
        "exits": {
            "hallway": "upstairs hallway", "back": "upstairs hallway"
        },
        "no_exit_msg": "You're not ready to leave."
    },
    "guest room": {
        "description": "The guest room. Everything someone needs, nothing extra. A room that says you were expected.",
        "exits": {
            "hallway": "upstairs hallway", "back": "upstairs hallway"
        },
        "no_exit_msg": "You stay."
    },
    "yard": {
        "description": "The yard. Open space, sky overhead. The house is behind you.",
        "exits": {
            "front door": "front door", "inside": "front door", "back": "front door"
        },
        "no_exit_msg": "You don't see a way there from the yard."
    }
}

# Weather substitutions — swap text in room descriptions based on current conditions.
# Format: "weather_condition": { "room_name": ("text to replace", "replacement text") }
# Add entries for any rooms whose descriptions should change with the weather.
WEATHER_SUBSTITUTIONS = {
    "rain": {
        "yard": (
            "Open space, sky overhead.",
            "Open space, rain coming down. The ground is wet."
        ),
    },
    "storm": {
        "yard": (
            "Open space, sky overhead.",
            "Open space, storm moving through. Lightning in the distance."
        ),
    },
    "fog": {
        "yard": (
            "Open space, sky overhead.",
            "Open space, fog low over everything. You can't see far."
        ),
    },
    "cloudy": {
        "yard": (
            "Open space, sky overhead.",
            "Open space, overcast sky above."
        ),
    },
}

# Time substitutions — swap text in room descriptions based on time of day.
# Format: "time_period": { "room_name": ("text to replace", "replacement text") }
TIME_SUBSTITUTIONS = {
    "morning": {
        "kitchen": (
            "the smell of something good",
            "morning light coming in, coffee already going"
        ),
    },
    "evening": {
        "living room": (
            "Comfortable furniture, fireplace on the far wall.",
            "Comfortable furniture, fire going. The room is warm."
        ),
    },
    "night": {
        "yard": (
            "Open space, sky overhead.",
            "Open space, dark sky overhead. Stars if it's clear."
        ),
    },
}

SPECIAL_ACTIONS = {
    "upstairs": {
        "look over": "You lean on the railing and look down over the foyer.",
        "look down": "You lean on the railing and look down over the foyer.",
    }
}


def get_time_of_day():
    """Returns current time period: morning, afternoon, evening, or night.
    Update the timezone offset (timedelta hours) for your location.
    """
    from datetime import datetime, timezone, timedelta
    local_tz = timezone(timedelta(hours=-5))  # CDT — update for your timezone
    hour = datetime.now(local_tz).hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"


_weather_cache = {"value": "clear", "expires": 0}

def get_weather():
    """Returns current weather via wttr.in. Cached 10 minutes.
    Replace 'Your+City' with your own location, or remove weather features entirely.
    """
    import urllib.request, json, time
    now = time.time()
    if now < _weather_cache["expires"]:
        return _weather_cache["value"]
    try:
        url = "https://wttr.in/Your+City?format=j1"  # <-- update this
        with urllib.request.urlopen(url, timeout=3) as r:
            data = json.loads(r.read())
        code = int(data["current_condition"][0]["weatherCode"])
        if code == 113:
            result = "clear"
        elif code in [116, 119, 122]:
            result = "cloudy"
        elif code in [143, 248, 260]:
            result = "fog"
        elif code in [200, 386, 389, 392, 395]:
            result = "storm"
        elif code >= 176:
            result = "rain"
        else:
            result = "clear"
    except Exception:
        result = "clear"
    _weather_cache["value"] = result
    _weather_cache["expires"] = now + 600
    return result


def navigate(location, direction):
    """
    Navigate from current location in a given direction.

    Returns: (new_location, description, message)
      new_location  — where you end up (same as input if movement failed)
      description   — room description if you entered a new room, else None
      message       — any message to print (stay msg, special action, auto-exit note)
    """
    direction = direction.lower().strip()

    if location in SPECIAL_ACTIONS and direction in SPECIAL_ACTIONS[location]:
        return location, None, SPECIAL_ACTIONS[location][direction]

    room = ROOMS.get(location)
    if not room:
        return location, None, "You're not sure where you are."

    new_location = room["exits"].get(direction)
    if new_location:
        if ROOMS.get(new_location):
            return new_location, get_description(new_location), None

    if "auto_exit" in room:
        auto_loc = room["auto_exit"]
        if ROOMS.get(auto_loc):
            return auto_loc, get_description(auto_loc), room.get("no_exit_msg")

    return location, None, room.get("no_exit_msg", "You stay.")


def get_description(location):
    """Returns the description for a location, adjusted for time of day and weather."""
    room = ROOMS.get(location)
    if not room:
        return "Unknown location."
    desc = room["description"]
    period = get_time_of_day()
    time_subs = TIME_SUBSTITUTIONS.get(period, {}).get(location)
    if time_subs:
        desc = desc.replace(time_subs[0], time_subs[1])
    weather = get_weather()
    weather_subs = WEATHER_SUBSTITUTIONS.get(weather, {}).get(location)
    if weather_subs:
        desc = desc.replace(weather_subs[0], weather_subs[1])
    return desc


def list_exits(location):
    """Returns the unique destination names reachable from this location."""
    room = ROOMS.get(location)
    if not room:
        return []
    return sorted(set(room["exits"].values()))


def who_is_here(location, occupants):
    """
    Given a location and a dict of {name: location},
    returns list of names currently in the same room.
    """
    return [name for name, loc in occupants.items() if loc == location]


if __name__ == "__main__":
    import json
    from pathlib import Path

    LOCATIONS_FILE = Path(__file__).parent / "locations.json"

    def _save_user(loc):
        try:
            data = json.loads(LOCATIONS_FILE.read_text(encoding="utf-8")) if LOCATIONS_FILE.exists() else {}
            data["user"] = loc
            LOCATIONS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _clear_user():
        try:
            data = json.loads(LOCATIONS_FILE.read_text(encoding="utf-8"))
            data.pop("user", None)
            LOCATIONS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    location = "front door"
    _save_user(location)
    print("\n" + ROOMS[location]["description"])

    while True:
        direction = input("\nWhere do you go? ").strip()
        if direction.lower() in ["quit", "exit", "q"]:
            _clear_user()
            print("You leave.")
            break

        new_location, description, message = navigate(location, direction)
        if new_location != location:
            location = new_location
            _save_user(location)

        if description:
            print("\n" + description)
        if message:
            print(message)
