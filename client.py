import paho.mqtt.client as mqtt
import json
import time
import threading
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout

# MQTT settings
broker = "mqtt.cackalacky.ninja"
port = 1883
client_id = "0070AD72"
username = "cyberpartner"
password = "Dif6EnmKdm4y"
will_topic = "cackalacky/badge/egress/0070AD72/status"
will_message = bytes.fromhex("6f66666c696e65")

base_topic = "cackalacky/badge/egress/0070AD72"
available_games = ["ogrady", "roulotto"]

session = PromptSession()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    if rc == 0:
        client.subscribe("cackalacky/#", qos=0)
        #client.subscribe("cackalacky/badge/ingress/0070AD72/#")
    else:
        print("Connection failed")

def on_message(client, userdata, msg):
    payload = msg.payload.decode(errors='replace')
    if client_id in msg.topic or client_id in payload:
        print_formatted_text(HTML(f'<ansigreen>[>>>>] {msg.topic}: {payload}</ansigreen>'))
    else:
        print(f"[MQTT] {msg.topic}: {payload}")
    sys.stdout.flush()

def heartbeat_loop():
    topic = f"{base_topic}/heartbeat"
    payload = b"9823"
    while True:
        time.sleep(30)
        client.publish(topic, payload, qos=0)

def command_interface():
    while True:
        try:
            with patch_stdout():
                cmd = session.prompt("> ").strip()

            if cmd.startswith("play"):
                parts = cmd.split()
                if len(parts) < 2:
                    print("Usage: play <game> [args]")
                    continue
                _, game, *args = parts
                if game not in available_games:
                    print(f"Invalid game. Available: {', '.join(available_games)}")
                    continue

                ts = int(time.time())
                topic = f"{base_topic}/cp/game/play"

                if game == "ogrady":
                    if len(args) != 1:
                        print("Usage: play ogrady <roundsWon>")
                        continue
                    try:
                        rounds_won = int(args[0])
                    except ValueError:
                        print("roundsWon must be an integer.")
                        continue
                    payload = json.dumps({
                        "game": "ogrady",
                        "roundsWon": rounds_won,
                        "ts": ts
                    }, separators=(",", ":"))

                elif game == "roulotto":
                    if len(args) != 2:
                        print("Usage: play roulotto <betAmount> <won>")
                        continue
                    try:
                        bet_amount = int(args[0])
                    except ValueError:
                        print("betAmount must be an integer.")
                        continue
                    won_str = args[1].lower()
                    if won_str not in ["true", "false"]:
                        print("won must be 'true' or 'false'")
                        continue
                    won = won_str == "true"
                    payload = json.dumps({
                        "game": "roulotto",
                        "betAmount": bet_amount,
                        "betType": "Inside 30",
                        "won": won,
                        "ts": ts
                    }, separators=(",", ":"))

                client.publish(topic, payload, qos=0)
                print(f"Published to {topic}: {payload}")

            elif cmd.startswith("inv"):
                parts = cmd.split()
                if len(parts) != 7:
                    print("Usage: inv <apple> <bread> <cereal> <water> <soda> <money>")
                    continue
                try:
                    apple, bread, cereal, water, soda, money = map(int, parts[1:])
                except ValueError:
                    print("All inventory values must be integers.")
                    continue

                ts = time.time()
                topic = f"cackalacky/badge/egress/{client_id}/cp/inventory/update"
                payload = json.dumps({
                    "apple": apple,
                    "bread": bread,
                    "cereal": cereal,
                    "water": water,
                    "soda": soda,
                    "money": money,
                    "ts": ts
                }, separators=(",", ":"))

                client.publish(topic, payload)
                print(f"Published to {topic}: {payload}")


            elif cmd.startswith("ach"):
                parts = cmd.split()
                if len(parts) != 2:
                    print("Usage: ach <ach>")
                    continue
                _, ach = parts

                ts = int(time.time())

                topic = f"{base_topic}/cp/achmnt/{ach}"
                payload = json.dumps({
                    "ts": ts
                }, separators=(",", ":"))

                client.publish(topic, payload, qos=0)
                print(f"Published to {topic}: {payload}")

            elif cmd.strip() == "get":
                ts = int(time.time())
                topic = f"{base_topic}/state/get"
                payload = json.dumps({"ts": ts}, separators=(",", ":"))
                client.publish(topic, payload, qos=0)
                print(f"Published to {topic}: {payload}")

            elif cmd.strip() == "status":
                ts = int(time.time())
                topic = f"{base_topic}/status"
                client.publish(topic, b"online")
                print(f"Published to {topic}: online")

            elif cmd.strip() == "create":
                ts = int(time.time())
                topic = f"{base_topic}/cp/create"
                payload = json.dumps({"ts": ts}, separators=(",", ":"))
                client.publish(topic, payload)
                print(f"Published to {topic}: {payload}")

            elif cmd.startswith("eat"):
                parts = cmd.split()
                if len(parts) != 2:
                    print("Usage: eat <item>")
                    continue
                _, item = parts
                valid_items = ["apple", "scone", "bread", "cereal", "pudding", "monster", "malort"]
                if item not in valid_items:
                    print(f"Invalid item. Available: {', '.join(valid_items)}")
                    continue

                ts = int(time.time())
                topic = f"{base_topic}/cp/state/update"
                payload = json.dumps({
                    "ts": ts,
                    "cp_event": f"eat.{item}"
                }, separators=(",", ":"))
                client.publish(topic, payload, qos=0)
                print(f"Published to {topic}: {payload}")


            elif cmd.startswith("purchase"):
                parts = cmd.split()
                if len(parts) != 2:
                    print("Usage: purchase <item>")
                    continue
                _, item = parts
                valid_items = ["apple", "scone", "bread", "cereal", "pudding", "monster", "malort"]
                if item not in valid_items:
                    print(f"Invalid item. Available: {', '.join(valid_items)}")
                    continue

                ts = int(time.time())
                topic = f"{base_topic}/cp/store/state"
                payload = json.dumps({
                    "ts": ts,
                    "cp_event": f"purchase.{item}"
                }, separators=(",", ":"))
                client.publish(topic, payload, qos=0)
                print(f"Published to {topic}: {payload}")

            else:
                print("Unknown command.")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

# MQTT client setup
client = mqtt.Client(client_id=client_id, clean_session=True)
client.username_pw_set(username, password)
client.will_set(will_topic, payload=will_message, qos=0, retain=True)

client.on_connect = on_connect
client.on_message = on_message

client.connect(broker, port, keepalive=60)
threading.Thread(target=client.loop_forever, daemon=True).start()
threading.Thread(target=heartbeat_loop, daemon=True).start()

command_interface()

