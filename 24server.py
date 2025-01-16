import random
import socket as s
from threading import Thread
import re
import json

def deal_cards():
    cards = "player_cards: "
    card_num = []
    one_suit = ["2","3","4", "5", "6", "7", "8", "9", "10", "A"]
    full_deck = one_suit*4
    suits = ["spades", "clubs", "hearts", "diamonds"]
    for i in range(4):
        number = random.choice(full_deck)
        suit = random.choice(suits)
        cards += f"{number}-{suit}, "
        card_num.append(number)
    return cards[:-2], card_num

def handle_player(socket,address):
    while True:
        try:
            data = socket.recv(2048).decode()
            if not data:
                break

            if "give cards" in data:
                cards, card_num = deal_cards()
                print(cards)
                for player in player_sockets:
                    player.send(cards.encode())
    
            elif "eval" in data:
                play = data.replace("eval ","")
                numbers_played = str(re.sub("[^0-9]"," ",play.replace("1","A"))).split()
                try:
                    result = str(round(eval(play)))

                    # has all cards been played?
                    if len(numbers_played) < 4:
                        result = "You need to use all cards!"
                    
                    # has a card been used twice?
                    elif sorted(numbers_played) != sorted(card_num):
                        result = "You must not use a card twice!"

                    elif result == "24":
                        result = "win"
                        player_points[address[0]]["points"] += 2
                    else:
                        result = f"{result} is NOT 24. Try again!"
                        player_points[address[0]]["points"] -= 1

                except Exception:
                    result = "Error; check your expression"
                
                result = f"eval,{address[0]},{player_points[address[0]]["id"]},{result}"

                for player in player_sockets:
                    player.send(result.encode())
            elif "standing" in data:
                json_string = json.dumps(player_points)
                for player in player_sockets:
                    player.send(json_string.encode())

        except Exception as e:
            print(f"Error with player {address}: {e}")
            break
        except KeyboardInterrupt:
            break
    print(f"Player disconnected: {address}")
    socket.close()
    del player_points[address]
    player_sockets.remove(socket)


sHost = s.gethostbyname(s.gethostname())
sPort = 8080

player_sockets = []
player_points = {}
# player_points = {
#     "playerIP": {
#         "id": x,
#         "points": y
#     }
# }


TCP_server = s.socket(s.AF_INET, s.SOCK_STREAM)
TCP_server.bind((sHost, sPort))
TCP_server.listen(2)
print(f"Server started on {sHost}:{sPort}")
while True:
    client_socket, addr = TCP_server.accept()
    print(f"Player connected: {addr}")
    player_sockets.append(client_socket)

    if addr in player_points:
        pass
    else:
        player_points[f"{addr[0]}"] = {}
        player_points[f"{addr[0]}"]["id"] = str(len(player_points))
        player_points[f"{addr[0]}"]["points"] = 0

    thread = Thread(target=handle_player, args=(client_socket, addr))
    thread.start()