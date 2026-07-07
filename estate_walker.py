# estate_walker.py — Multi-person home navigation
# Tracks where each resident is. Each person calls move() to navigate.
# Shared state stored in locations.json.
# Run directly: python estate_walker.py PersonName
#
# HOW TO USE:
# 1. Update RESIDENTS below with your household's names
# 2. Drop alongside estate.py (this file imports from it)
# 3. locations.json is auto-created on first run — add it to .gitignore

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from estate import navigate, get_description, list_exits, ROOMS

LOCATIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locations.json")

# Update these with your household's names
RESIDENTS = ["Person1", "Person2", "Person3"]
DEFAULT_LOCATIONS = {name: "front door" for name in RESIDENTS}


def load_locations():
    if os.path.exists(LOCATIONS_FILE):
        with open(LOCATIONS_FILE) as f:
            return json.load(f)
    return DEFAULT_LOCATIONS.copy()


def save_locations(locations):
    with open(LOCATIONS_FILE, "w") as f:
        json.dump(locations, f, indent=2)


def where_am_i(person):
    """Returns current location of a person."""
    return load_locations().get(person, "front door")


def where_is_everyone():
    """Returns dict of {person: location}."""
    return load_locations()


def who_else_is_here(person, location):
    """Returns list of other residents in the same room."""
    locations = load_locations()
    return [name for name, loc in locations.items()
            if loc == location and name != person]


def move(person, direction):
    """
    Move a person in a direction. Updates shared locations.json.

    Returns: (new_location, description, message, others_here)
      new_location  — where the person ends up (same if movement failed)
      description   — room description if they moved, else None
      message       — stay message, special action, or None
      others_here   — list of other residents in the new location
    """
    locations = load_locations()
    current = locations.get(person, "front door")

    new_location, description, message = navigate(current, direction)

    locations[person] = new_location
    save_locations(locations)

    others = [name for name, loc in locations.items()
              if loc == new_location and name != person]

    return new_location, description, message, others


def look(person):
    """
    Describe the room the person is currently in, plus who else is there.

    Returns: (current_location, description, others_here)
    """
    locations = load_locations()
    current = locations.get(person, "front door")
    description = get_description(current)
    others = [name for name, loc in locations.items()
              if loc == current and name != person]
    return current, description, others


def exits(person):
    """Returns list of unique destination rooms reachable from person's current location."""
    return list_exits(where_am_i(person))


def status():
    """Returns a formatted string showing where everyone is."""
    locations = load_locations()
    lines = []
    for person in RESIDENTS:
        location = locations.get(person, "front door")
        lines.append(f"  {person}: {location}")
    return "\n".join(lines)


def reset(person=None):
    """Reset one person or everyone to the front door."""
    locations = load_locations()
    if person:
        locations[person] = "front door"
    else:
        locations = DEFAULT_LOCATIONS.copy()
    save_locations(locations)


# Initialize locations.json if it doesn't exist
if not os.path.exists(LOCATIONS_FILE):
    save_locations(DEFAULT_LOCATIONS.copy())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python estate_walker.py <Name>")
        print("Residents:", ", ".join(RESIDENTS))
        print("\nCurrent locations:")
        print(status())
        sys.exit(0)

    person = sys.argv[1]
    if person not in RESIDENTS:
        print(f"Unknown name '{person}'. Options: {', '.join(RESIDENTS)}")
        sys.exit(1)

    HELP = (
        "  go <room>      — move to a room (e.g. 'go kitchen')\n"
        "  look           — describe current room\n"
        "  exits          — list reachable rooms from here\n"
        "  where / status — show where all residents are\n"
        "  quit           — exit"
    )

    current, description, others = look(person)
    print(f"\n[{person} — {current}]")
    print(description)
    if others:
        print(f"Also here: {', '.join(others)}")
    print(f"\nCommands:\n{HELP}")

    while True:
        try:
            raw = input(f"\n[{person}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{person} steps away.")
            break

        if not raw:
            continue

        cmd = raw.lower()

        if cmd in ("quit", "exit", "q"):
            print(f"{person} steps away.")
            break

        elif cmd in ("look", "here", "room"):
            current, description, others = look(person)
            print(f"\n[{person} — {current}]")
            print(description)
            if others:
                print(f"Also here: {', '.join(others)}")

        elif cmd in ("where", "status", "everyone"):
            print("\nWhere everyone is:")
            print(status())

        elif cmd in ("exits", "doors", "ways", "options"):
            e = exits(person)
            print(f"From here you can reach: {', '.join(e)}")

        elif cmd in ("help", "?"):
            print(HELP)

        elif cmd.startswith("go "):
            direction = raw[3:].strip()
            new_location, description, message, others = move(person, direction)
            if description:
                print(f"\n[{person} — {new_location}]")
                print(description)
            if message:
                print(message)
            if others:
                print(f"Also here: {', '.join(others)}")

        else:
            new_location, description, message, others = move(person, raw)
            if description:
                print(f"\n[{person} — {new_location}]")
                print(description)
            if message:
                print(message)
            if others:
                print(f"Also here: {', '.join(others)}")
