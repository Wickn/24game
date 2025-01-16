import time
import socket as s
from threading import Thread
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import json

class NetworkProcess(QWidget):
    network_signal = pyqtSignal(list)
    evaluation_signal = pyqtSignal(str)
    winning_signal = pyqtSignal(str)
    standing_signal = pyqtSignal(dict)

    def __init__(self,p):
        super().__init__()
        self.parent = p
        self.running = True

        t = Thread(target=self.run)
        t.start()

        self.button = self.parent.btns

        self.network_signal.connect(self.change_button)
        self.evaluation_signal.connect(self.show_eval)
        self.winning_signal.connect(self.winner)
        self.standing_signal.connect(self.get_your_standing)
    
    def run(self):
        self.pHost = s.gethostbyname(s.gethostname())
        self.pPort = 8081

        # 
        # RUN 24server.py TO GET SERVER IP
        #
        # TYPE IP INTO self.sHost
        #

        self.sHost = "192.168.1.224"

        self.sPort = 8080 # DO NOT TOUCH

        self.TCP_client = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.TCP_client.connect((self.sHost, self.sPort))

        #establish connection
        payload = "connect"
        self.TCP_client.send(payload.encode())

        has_run = False
        suits = {
                "spades": "\n♠",
                "hearts": "\n♥",
                "clubs": "\n♦",
                "diamonds": "\n♣"
            }
        while self.running:
            if has_run == False:
                self.give_cards()
                self.get_standings()
                has_run = True

            svar = self.TCP_client.recv(2048).decode()
            if "player_cards: " in svar:
                self.shvar = svar.replace("player_cards: ","").replace(" ","")
                
                self.cards = self.shvar.split(",")

                self.parent.game.restart()

                for i, card in enumerate(self.cards):
                    rank, suit = card.split("-")
                    suit_symbol = suits.get(suit, suit)
                    self.network_signal.emit([i, f"{rank}{suit_symbol}"])

            elif "eval" in svar:
                message = svar.split(",")
                if "win" in message[3]:
                    self.winner(message)
                elif self.pHost == message[1]:
                    self.show_eval(message[3])
            
            elif "points" in svar:
                self.player_standing = json.loads(svar)
                self.standing_signal.emit(self.player_standing)
                # player_points = {
                #     "playerIP": {
                #         "id": x,
                #         "points": y
                #     }
                # }

        self.TCP_client.close()
            

    def change_button(self, message):
        self.button[message[0]].setText(message[1])
    

    def show_eval(self, eval):
        self.parent.math_field.append(eval)
    
    def winner(self, message):
        # region SetEnabled(False)
        self.parent.add_btn.setEnabled(False)
        self.parent.sub_btn.setEnabled(False)
        self.parent.mult_btn.setEnabled(False)
        self.parent.div_btn.setEnabled(False)
        self.parent.par_open_btn.setEnabled(False)
        self.parent.par_closed_btn.setEnabled(False)
        self.parent.del_btn.setEnabled(False)
        self.parent.eval_btn.setEnabled(False)
        for i in range(4):
            self.parent.btns[i].setEnabled(False)
        # endregion
        self.parent.math_field.append(f"Player {message[2]} wins!")
    
    def give_cards(self):
        payload = "give cards"
        self.TCP_client.send(payload.encode())

    def evaluate_play(self, play):
        payload = f"eval {play}"
        self.TCP_client.send(payload.encode())
    
    def send_cards(self):
        return self.cards

    def get_standings(self):
        payload = "standing"
        self.TCP_client.send(payload.encode())
    
    def get_your_standing(self, standings):
        for key, value in standings.items():
            if key == self.pHost:
                player_id = value["id"]
                player_points = value["points"]
            else:
                opponent_id = value["id"]
                opponent_points = value["points"]
            
        try:
            self.parent.identity.setText(f"You are player {player_id}. You have {player_points} point(s).\nPlayer {opponent_id} has {opponent_points} point(s).")
        except:
            self.parent.identity.setText(f"You are player {player_id}. You have {player_points} point(s).\nYour opponent has not yet joined")

    def stop(self):
        payload = "disconnect"
        self.TCP_client.send(payload.encode())
        self.running = False
        self.TCP_client.close()
    
class GameLogic(QWidget):
    def __init__(self,p):
        super().__init__()
        self.parent = p

        self.expression = "​" #special no width character
        self.card_nums = []
        self.used_cards = []

        self.operators = ["*","/","+","-"]
        self.numbers = ["1","2","3","4","5","6","7","8","9","0"]
    
    def restart(self):
        self.cards = self.parent.network.send_cards()
        self.expression = "​" #special no width character
        self.card_nums = []
        for card in self.cards:
            card = card.replace("-clubs","")
            card = card.replace("-spades","")
            card = card.replace("-diamonds","")
            card = card.replace("-hearts","")
            card = card.replace("A","1")
            self.card_nums.append(card)
        # region SetEnable(True)
        self.parent.add_btn.setEnabled(True)
        self.parent.sub_btn.setEnabled(True)
        self.parent.mult_btn.setEnabled(True)
        self.parent.div_btn.setEnabled(True)
        self.parent.par_open_btn.setEnabled(True)
        self.parent.par_closed_btn.setEnabled(True)
        self.parent.del_btn.setEnabled(True)
        self.parent.eval_btn.setEnabled(True)
        for i in range(4):
            self.parent.btns[i].setEnabled(True)
        # endregion

        self.parent.network.get_standings()
        
    def add_sym(self, sym):
        #if new character is an operator and if last character is an operator
        if sym in self.operators and self.expression[-1] in self.operators: 
            pass

        #if new character is an operator and if first character is an operator
        elif sym in self.operators and self.expression[0:] == "": 
            pass
        
        #if new character is a number and if previous character is a number
        elif sym in self.numbers and self.expression[-1] in self.numbers:
            pass
        
        else:
            if sym in ["1","2","3","4"]:
                sym = str(self.card_nums[int(sym)-1])
                self.used_cards.append(sym)
            self.expression += sym
            self.parent.math_field.setText(self.expression)
        self.expression = self.expression.replace("​","") #special no width character
    
    def delete_sym(self):
        if self.expression == "":
            pass
        elif self.expression[-1] == "0":
            self.expression = self.expression[:-2]

        else:
            self.expression = self.expression[:-1]
        
        if self.expression == "":
            self.expression = "​" #special no width character
        self.parent.math_field.setText(self.expression)

    def evaluate(self):
        self.parent.network.evaluate_play(self.expression)

class MainProcess(QMainWindow):
    def __init__(self):
        super().__init__()
        central = QWidget(self)
        self.setCentralWidget(central)

        self.banner = QLabel("Welcome to the 24 Game!")

        self.identity = QLabel("")

        self.math_field = QTextBrowser()

        self.grid = QGridLayout()
        self.btns = [QPushButton() for i in range(4)]
        for i, button in enumerate(self.btns):
            self.btns[i].clicked.connect(self.handle_button_click)
            row = i // 2
            col = i % 2
            self.grid.addWidget(button,row,col)
        
        #region Math Operations
        self.math_layout_top = QHBoxLayout()
        self.math_layout_mid = QHBoxLayout()
        self.math_layout_bot = QHBoxLayout()

        self.add_btn = QPushButton("+")
        self.sub_btn = QPushButton("-")
        self.mult_btn = QPushButton("*")

        self.div_btn = QPushButton("/")
        self.par_open_btn = QPushButton("(")
        self.par_closed_btn = QPushButton(")")

        self.del_btn = QPushButton("Delete")
        self.eval_btn = QPushButton("Submit")

        self.add_btn.clicked.connect(self.handle_button_click)
        self.sub_btn.clicked.connect(self.handle_button_click)
        self.mult_btn.clicked.connect(self.handle_button_click)

        self.div_btn.clicked.connect(self.handle_button_click)
        self.par_open_btn.clicked.connect(self.handle_button_click)
        self.par_closed_btn.clicked.connect(self.handle_button_click)

        self.del_btn.clicked.connect(self.handle_button_click)
        self.eval_btn.clicked.connect(self.handle_button_click)

        self.math_layout_top.addWidget(self.add_btn)
        self.math_layout_top.addWidget(self.sub_btn)
        self.math_layout_top.addWidget(self.mult_btn)

        self.math_layout_mid.addWidget(self.div_btn)
        self.math_layout_mid.addWidget(self.par_open_btn)
        self.math_layout_mid.addWidget(self.par_closed_btn)

        self.math_layout_bot.addWidget(self.del_btn)
        self.math_layout_bot.addWidget(self.eval_btn)
        #endregion

        self.givecard = QPushButton("New cards")
        self.givecard.clicked.connect(self.handle_button_click)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_application)

        layout = QVBoxLayout()
        
        #region Main Layout
        layout.addWidget(self.banner)
        layout.addWidget(self.identity)
        layout.addWidget(self.math_field)
        layout.addLayout(self.grid)
        layout.addLayout(self.math_layout_top)
        layout.addLayout(self.math_layout_mid)
        layout.addLayout(self.math_layout_bot)
        layout.addWidget(QLabel()) # spacer
        layout.addWidget(self.givecard)
        layout.addWidget(self.close_button)
        central.setLayout(layout)
        #endregion

        self.network = NetworkProcess(self)
        self.game = GameLogic(self)

    def handle_button_click(self):
        sender = self.sender()
        button_text = sender.text()
        
        if sender == self.givecard:
            self.network.give_cards()
            self.math_field.clear()
        
        #region Dictionary mapping
        choose_card = {
        self.btns[0]: lambda: self.game.add_sym("1"),
        self.btns[1]: lambda: self.game.add_sym("2"),
        self.btns[2]: lambda: self.game.add_sym("3"),
        self.btns[3]: lambda: self.game.add_sym("4")
        }
        
        actions = {
            '+': lambda: self.game.add_sym("+"),
            '-': lambda: self.game.add_sym("-"),
            '*': lambda: self.game.add_sym("*"),
            '/': lambda: self.game.add_sym("/"),
            '(': lambda: self.game.add_sym("("),
            ')': lambda: self.game.add_sym(")"),
            'Delete': lambda: self.game.delete_sym(),
            'Submit': lambda: self.game.evaluate()
        }
        #endregion

        if sender in self.btns:
            choose_card[sender]()

        if button_text in actions:
            actions[button_text]()

        
    def close_application(self):
        self.network.stop()
        self.close()


if __name__ == "__main__":
    app = QApplication([])
    gui = MainProcess()
    gui.setWindowTitle("24 Game")
    gui.setGeometry(100, 100, 300, 300)
    gui.show()
    app.exec()


