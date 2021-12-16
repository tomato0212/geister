# パッケージ
import socket 
import random
from contextlib import closing 
import time
import copy
import numpy as np 
import pandas as pd
import os 
# -----------------

IP = "127.0.0.1"
BUFFER_SIZE = 4096

INF = 100000
MAX_DEPTH = 4

WEIGHT_CNT = 100
WEIGHT_DIR = 1

DIR_Y = [-1, 0, 1, 0]
DIR_X = [0, 1, 0, -1]

class Geister():
    def __init__(self, port, game_count):
        # サーバー情報
        self.port = port

        # ファイル出力用のカウント変数
        self.game_count = game_count + 1

        # 相手の駒情報
        self.rnum = 4
        self.bnum = 4
        self.unum = 0

        # 自分の駒情報
        self.Rnum = 4
        self.Bnum = 4

        self.kiki = [0 for i in range(180)]

        self.BestMove = 0

        self.Board_list = ["*" for i in range(36)]

        #self.hist_board = [[[0 for i in range(36)] for j in range(36)]]
        
    # ガイスターサーバーに赤駒をセットするコマンドを送信し，サーバーから「OK」をもらう
    # 赤駒をどれに割り振るか決めるための処理
    def Red_Choice(self) -> str:
        Red_li = []
        while len(Red_li) < 4:
            n = random.randint(0, 7)
            if not chr(n + 65) in Red_li:
                Red_li.append(chr(n + 65))
        red_send = "SET:"+Red_li[0]+Red_li[1]+Red_li[2]+Red_li[3]
        return red_send
    # ----------------------------------

    # 駒を移動することができるマスの番号を生成，格納
    def Create_kiki(self):
        for i in range(180):
            self.kiki[i] = -1
        y_num, x_num = 0, 0
        for y in range(6):
            for x in range(6):
                y_num = y * 6 + x 
                x_num = 0
                for d in range(4):
                    ny = y + DIR_Y[d]
                    nx = x + DIR_X[d]
                    if 0 <= ny < 6 and 0 <= nx < 6:
                        self.kiki[5 * y_num + x_num] = ny * 6 + nx 
                        x_num += 1
    # ----------------------------------

    # 盤面の記録
    def Board_Recode(self, server_response) -> list:
        Board_Info = [["*" for i in range(6)] for j in range(6)]
        Koma_Info = [["*" for i in range(6)] for j in range(6)]

        for i in range(16):
            koma_x = int(server_response[3 * i])
            koma_y = int(server_response[3 * i + 1])
            koma_color = server_response[3 * i + 2]

            if 0 <= koma_x < 6 and 0 <= koma_y < 6:
                if koma_color == "R" or koma_color == "B" or koma_color == "u":
                    Board_Info[koma_y][koma_x] = koma_color
                    self.Board_list[koma_y*6 + koma_x] = koma_color
                if i < 8:
                    Koma_Info[koma_y][koma_x] = chr(i + ord("A"))
                else:
                    Koma_Info[koma_y][koma_x] = chr(i - 8 + ord("a"))
            elif koma_x == 9 and koma_y == 9:
                if koma_color == "r" and i >= 8:
                    self.rnum -= 1
                elif koma_color == "b" and i >= 8:
                    self.bnum -= 1
                elif koma_color == "r" and i < 8:
                    self.Rnum -= 1
                elif koma_color == "b" and i < 8:
                    self.Bnum -= 1
            if koma_color == "u":
                self.unum += 1

        return Board_Info, Koma_Info
    # ----------------------------------

    # 手を決める
    def ThinkMove(self) -> int:
        escape_flag = self.EscapeCommand()
        if escape_flag == 1:
            return INF
        else:
            eva = self.negamax(0, -INF - 1, INF + 1)
            return eva
    # ----------------------------------

    # 脱出できるかを確認し，できるならば脱出手を返す
    def EscapeCommand(self) -> int:
        #if teban == 0:
        if self.Board_list[0] == "B":
            self.BestMove = (0, 0, 3)
            return 1
        elif self.Board_list[5] == "B":
            self.BestMove = (0, 5, 1)
            return 1
        else:
            self.BestMove = (-1, -1, -1)
            return 0
    # ----------------------------------

    def negamax(self, depth, alpha, beta):
        player = depth % 2
        win_player = self.GetWinplayer(player)
        if win_player == 0:
            if player == 0:
                return INF - depth
            else:
                return -INF + depth
        elif win_player == 1:
            if player == 0:
                return -INF + depth
            else:
                return INF - depth
        
        if depth == MAX_DEPTH: # 最大まで探索した時
            b_eva = self.Evaluate(player)
            return b_eva

        fr_list = [0 for i in range(32)]
        to_list = [0 for i in range(32)]
        fr_list, to_list, movenum = self.MakeMoves(player, fr_list, to_list)
        
        for i in range(movenum):
            bb_tmp = copy.deepcopy(self.Board_list)
             
            self.Board_list = self.move(fr_list[i], to_list[i])
            
            res = -self.negamax(depth+1, -beta, -alpha)
            if alpha < res:
                alpha = res
                if depth == 0:
                    self.BestMove = self.MoveCommand(fr_list[i], to_list[i])
            if alpha >= beta:
                return beta
            self.Board_list = copy.deepcopy(bb_tmp)
        return alpha
    # ----------------------------------

    def MakeMoves(self, player, fr_list, to_list) -> list:
        cnt = 0
        for pos in range(36):
            if (player == 0 and self.Board_list[pos] != "R") and (player == 0 and self.Board_list[pos] != "B"):
                continue
            if player == 1 and self.Board_list[pos] != "u":
                continue
            i = pos * 5
            for j in range(5):
                if self.kiki[i + j] == -1:
                    break
                npos = self.kiki[i + j]
                if (player == 0 and self.Board_list[npos] == "R") or (player == 0 and self.Board_list[npos] == "B"):
                    continue
                if player == 1 and self.Board_list[npos] == "u":
                    continue
                fr_list[cnt] = pos 
                to_list[cnt] = npos
                cnt += 1
        return fr_list, to_list, cnt
    # ----------------------------------

    # 勝利条件を満たしているプレイヤーがいるか検証
    def GetWinplayer(self, player) -> int:
        nothing_r, nothing_b = 0, 0
        for i in range(36):
            if self.Board_list[i] == "R":
                nothing_r += 1
            elif self.Board_list[i] == "B":
                nothing_b += 1
        if nothing_r == 0:
            return 0
        elif nothing_b == 0:
            return 1
        elif (player == 0 and self.Board_list[0] == "B") or (player == 0 and self.Board_list[5] == "B"):
            return 0
        #不完全情報の場合
        elif (player == 1 and self.Board_list[30] == "u") or (player == 1 and self.Board_list[35] == "u"): 
            return 1
        else:
            return 2
    # ----------------------------------

    # 駒の動きについて
    def MoveCommand(self, fr, to) -> tuple:
        y, x = 0, 0
        y = fr // 6
        x = fr % 6
        for d in range(4):
            ny = y + DIR_Y[d]
            nx = x + DIR_X[d]
            if ny * 6 + nx == to:
                break
        return y, x, d
    # ----------------------------------
   
    # お互いの青駒の個数を数える
    def BlueCount(self) -> int:
        existB_cnt = 0
        for i in range(36):
            if "B" == self.Board_list[i]:
                existB_cnt += 1
        return existB_cnt
    # ----------------------------------

    # お互いの駒の距離を計算する
    def Distance(self) -> int:
        my_goaldist, enemy_goaldist = 0, 0
        y, x = 0, 0
        for i in range(36):
            if self.Board_list[i] == "R":
                y = i // 6
                x = i % 6
                my_goaldist += y + min(x, 5-x)
            elif self.Board_list[i] == "B":
                y = i // 6
                x = i % 6
                my_goaldist += y + min(x, 5-x)
            # 不完全情報の場合
            if self.Board_list[i] == "u":
                y = i // 6
                x = i % 6
                enemy_goaldist += 5 - y + min(x, 5-x)
        return my_goaldist, enemy_goaldist
    # ----------------------------------

    # 評価関数 teban = 0 -> 自分 | 1 -> 相手
    def Evaluate(self, player) -> int:
        s0, s1 = 0, 0
        existB_cnt = self.BlueCount()
        my_goaldist, enemy_goaldist = self.Distance()
        s0 = WEIGHT_CNT * existB_cnt - WEIGHT_DIR * my_goaldist
        s1 = WEIGHT_CNT * self.bnum - WEIGHT_DIR * enemy_goaldist
        if player == 0:
            return s0 - s1 
        if player == 1:
            return s1 - s0 
    # ----------------------------------

    # 駒を動かしたときの処理
    def move(self, fr, to) -> list:
        if self.Board_list[fr] == "R":
            bb = self.moveR(fr, to)
            return bb
        elif self.Board_list[fr] == "B":
            bb = self.moveB(fr, to)
            return bb
        elif self.Board_list[fr] == "u":
            bb = self.moveu(fr, to)
            return bb
    # ----------------------------------
    
    # 自身の赤駒を動かした場合
    def moveR(self, fr, to) -> list:
        tmp = self.Board_list
        tmp[fr] = "*"
        tmp[to] = "R"
        return tmp
    # ----------------------------------

    # 自身の青駒を動かした場合
    def moveB(self, fr, to) -> list:
        tmp = self.Board_list
        tmp[fr] = "*"
        tmp[to] = "B"
        return tmp
    # ----------------------------------

    # 駒があった場合
    def moveu(self, fr, to) -> list:
        tmp = self.Board_list
        tmp[fr] = "*"
        tmp[to] = "u"
        return tmp
    # ----------------------------------

    # 選択した手を送信用に変換する
    def Te_to_Send(self, y, x, d, Koma_Info) -> str:
        movestr = "NESW"
        t = ""
        t += "MOV:"
        t += Koma_Info[y][x]
        t += ","
        t += movestr[d]
        t += "\r\n"
        return t
    # ----------------------------------

    # 勝敗を確認
    def Judge(self, end_response) -> str:
        response = end_response
        if response.startswith("WON"):
            print("WIN")
            return "WIN"
        elif response.startswith("LST"):
            print("LOSE")
            return "LOSE"
        else:
            print("DRAW")
            return "DRAW"
    # ----------------------------------

    # 終了要因を確認
    def End_act(self, my_rnum, my_bnum, ene_rnum, ene_bnum, my_nige, ene_nige) -> str:
        # 青駒が全てなくなったか
        if ene_bnum == 0:
            return "aotori"
        elif my_bnum == 0:
            return "aotorare"
        # 赤駒が全てなくなったか
        elif ene_rnum == 0:
            return "akatori"
        elif my_rnum == 0:
            return "akatorase"
        # 青駒が脱出したか
        elif my_nige == 1:
            return "nige"
        elif ene_nige == 1:
            return "nigerare"
        else:
            return "draw"
    # ----------------------------------
    
    # ゲーム終了時の処理
    def end_response_reco(self, server_response):
        Rnum, Bnum, rnum, bnum, nige_flag, nigerare_flag = 4, 4, 4, 4, 0, 0
        for i in range(16):
            end_x = server_response[3 * i]
            end_y = server_response[3 * i + 1]
            end_col = server_response[3 * i + 2]

            if end_x == "9" and end_y == "9":
                if i < 8:
                    if end_col == "r":
                        Rnum -= 1
                    if end_col == "b":
                        Bnum -= 1
                else:
                    if end_col == "r":
                        rnum -= 1
                    if end_col == "b":
                        bnum -= 1
            if end_x == "8" and end_y == "8":
                if i < 8:
                    nige_flag = 1
                else:
                    nigerare_flag = 1
        return Rnum, Bnum, rnum, bnum, nige_flag, nigerare_flag
    # ----------------------------------

    def from_to(self, prev_board, now_board):
        enemy_fr, enemy_to = 0, 0
        for i in range(36):
            if prev_board[i] != now_board[i]:
                if prev_board[i] == "u":
                    enemy_fr = i
                if now_board[i] == "u":
                    enemy_to = i
        return enemy_fr, enemy_to
    
    def Game(self):

        # サーバーとの通信
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:

            # サーバーと接続
            server_info = (IP, self.port) 
            client.connect(server_info)
            
            server_response = client.recv(BUFFER_SIZE).decode()
            #print(server_response) <- サーバーからSET? が返ってくる
            # ----------------------------------


            # 赤駒を設定
            red_send = self.Red_Choice() 
            print(red_send) # 赤駒をどれに当てたかの確認

            # 赤駒の位置をサーバーに送るための処理
            client.send(bytes(red_send+"\r\n", encoding = "utf-8")) # <- 赤駒をサーバーに送信
            server_response = client.recv(BUFFER_SIZE).decode() # <- 正しく遅れていれば "OK" と来る．
            print("通信 = ", server_response) 
            # ----------------------------------

            server_response = client.recv(BUFFER_SIZE).decode() # <- MOV? から始まる文字列を受信

            # 駒がある場所から移動可能なマスを配列に記録
            self.Create_kiki()
            # ----------------------------------

            # 盤面を記録する配列を作成
            hist_board = [["*" for i in range(36)] for j in range(210)]
            if self.port == 10000:
                hist_cnt = 0
            if self.port == 10001:
                hist_cnt = 1

            moved_color_list = ["*" for i in range(210)]
            enemy_mov_list = [["*" for _ in range(2)] for i in range(210)]        

            while server_response.startswith("MOV?") == True:
                
                # MOV?以降の文字列を取得
                server_response = server_response[4:] 
                #print(server_response) <- 14R24B34B44B15B25R35R45R41u31u21u11u40u30u20u10u
                # ----------------------------------

                Board_Info, Koma_Info = self.Board_Recode(server_response) # 盤面の記録を行う
                #self.BitBoard() # existを作成するために盤面情報を配列にする
    
                # 盤面の表示
                print("-----------------------------", " 相手 ", "----------------------------")
                for i in range(6):
                    print(Koma_Info[i], " | ", Board_Info[i])
                print("-----------------------------", " 自分 ", "----------------------------")
                # ----------------------------------

                # ゲームの盤面の記録を行う 1行36列の行列で
                for i in range(6):
                    for j in range(6):
                        hist_board[hist_cnt][i * 6 + j] = Board_Info[i][j]
                if hist_cnt > 1:
                    enemy_fr, enemy_mov = self.from_to(hist_board[hist_cnt-2], hist_board[hist_cnt])
                    enemy_mov_list[hist_cnt][0] = enemy_fr 
                    enemy_mov_list[hist_cnt][1] = enemy_mov
                # ----------------------------------

                # 手を選択する処理 ↓ 
                res = self.ThinkMove() 
                hist_cnt += 1
                # ----------------------------------

                print(self.BestMove, "評価値 =", res)
                # 手の表示と送信用に加工する
                te = self.Te_to_Send(self.BestMove[0], self.BestMove[1], self.BestMove[2], Koma_Info)
                print(te)
                            
                moved_color_list[hist_cnt] = Board_Info[self.BestMove[0]][self.BestMove[1]]
                hist_cnt += 1

                # すべて問題ないのであれば送信
                client.send(bytes(te, encoding = "utf-8"))

                server_response = client.recv(BUFFER_SIZE).decode() # 正しく送れているかの確認である「OK」を受け取る
                print("送信 = ", server_response) 

                server_response = client.recv(BUFFER_SIZE).decode() # 駒の位置と色を表す文字列を受け取る (MOV? ~ )

                self.Board_list = ["*" for i in range(36)]
                self.rnum, self.bnum, self.Rnum, self.Bnum = 0, 0, 0, 0
                
                # ここに情報を更新するmyMoveを追加する

            client.close()
            time.sleep(500 / 1000)

            end_response = server_response[:4]
            server_response = server_response[4:]
            my_rnum, my_bnum, ene_rnum, ene_bnum, my_nige, ene_nige = self.end_response_reco(server_response)
            
            
            # 試合の盤面経過と動かした駒の色をcsv形式で出力
            df = pd.DataFrame(hist_board)
            label_df = pd.DataFrame(moved_color_list)
            moved_df = pd.DataFrame(enemy_mov_list)
            path = "try"
            df.to_csv(path+"/"+"nega_vs_nega_"+str(self.port)+"_"+str(self.game_count)+".csv", sep=",", encoding="utf-8", index=False, header=False)
            label_df.to_csv(path+"/"+"nega_vs_nega_"+str(self.port)+"_"+str(self.game_count)+"_label.csv", sep=",", encoding="utf-8",index=False, header=False)
            moved_df.to_csv(path+"/"+"nega_vs_nega_"+str(self.port)+"_"+str(self.game_count)+"_moved.csv", sep=",", encoding="utf-8",index=False, header=False)
            # ----------------------------------            

        self.endinfo = self.Judge(end_response)
        end_act = self.End_act(my_rnum, my_bnum, ene_rnum, ene_bnum, my_nige, ene_nige)
        return self.endinfo, end_act
    # ----------------------------------

result_dic = {"WIN":0, "LOSE":0, "DRAW":0} # 結果を格納する辞書
res_action_dic = {"akatori":0, "akatorase":0, "aotori": 0, "aotorare":0, "nige":0, "nigerare":0, "draw":0}

print("ポート番号, |空白|, 試合回数で入力")
port, game_count = map(int, input().split())
for i in range(game_count):
    G = Geister(port, i)
    result, act = G.Game()
    result_dic[result] += 1
    res_action_dic[act] += 1
    print("")
print("対戦回数 :", game_count)
print("----------------------------------")
print(result_dic)
print("----------------------------------")
print(res_action_dic)