import socket 
import random
from contextlib import closing 
import time

# サーバーに接続するために関数
def Geister_Client(port, count):
    game_count = count # 試合数を記録
    result_dic = {"WIN":0, "LOSE":0, "DRAW":0}
    cnt_recode = count

    ip_num = "127.0.0.1"
    buffer_size = 4096
    server_info = (ip_num, port)

    while True:
        # 試合回数残り0なら終わる
        if game_count == 0:
            break
        
        # サーバーに接続
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect(server_info)

            # ガイスターサーバーから「SET?」を受信する
            server_response = client.recv(buffer_size).decode()
            print(server_response)
            
            # ガイスターサーバーに赤駒をセットするコマンドを送信し，サーバーから「OK」をもらう
            # 赤駒をどれに割り振るか決めるための処理
            Red_li = []
            while len(Red_li) < 4:
                n = random.randint(0, 7)
                if not chr(n + 65) in Red_li:
                    Red_li.append(chr(n + 65))
            red_send = "SET:"+Red_li[0]+Red_li[1]+Red_li[2]+Red_li[3]

            # 赤駒をどれに当てたかの確認
            print(red_send)

            # 赤駒の位置をサーバーに送るための処理
            client.send(bytes(red_send+"\r\n", encoding = "utf-8"))
            server_response = client.recv(buffer_size).decode()
            print("通信 = ", server_response) # 正しく遅れていれば "OK" と来るはず．

            server_response = client.recv(buffer_size).decode()
            print(server_response)

            while server_response.startswith("MOV?") == True:

                # 盤面を初期化
                Geister_Board = [["0" for i in range(6)] for j in range(6)]
                Board_Info = []

                # 駒の位置と色の情報を取得
                for i in range(4, 48, 3):
                    Koma_Info = server_response[i:i+3]
                    Board_Info.append(Koma_Info)
                    if Koma_Info[0] == "9" or Koma_Info[0] == "8":
                        continue
                    Geister_Board[int(Koma_Info[1])][int(Koma_Info[0])] = Koma_Info[2]

                print(server_response)
                # 盤面状況の観察用
                print("_", "_", "_敵_", "_", "_")
                for i in range(6):
                    print(Geister_Board[i])
                print("_", "_", "自身", "_", "_")
                        
                #MoveKoma, MoveDir = Human_agent() # 人間が操作するとき
                MoveKoma, MoveDir = Random_agent(server_response) # ランダムAIが操作するとき
                        
                # すべて問題ないのであれば送信
                client.send(bytes("MOV:"+MoveKoma+","+MoveDir+"\r\n", encoding = "utf-8"))
                print("MOV: "+MoveKoma+": "+MoveDir)

                server_response = client.recv(buffer_size).decode() # 正しく送れているかの確認である「OK」を受け取る
                print("送信 = ", server_response) 
                server_response = client.recv(buffer_size).decode() # 駒の位置と色を表す文字列を受け取る
            
            client.close()
            time.sleep(1)

            # 勝敗の確認と回数の計上
            result = Judge(server_response)
            result_dic[result] += 1

            game_count -= 1
            
            # 盤面を初期化
            Geister_Board = [["0" for i in range(6)] for j in range(6)]
            Board_Info = []

            """
            # 駒の位置と色の情報を取得
            for i in range(4, 48, 3):
                Koma_Info = server_response[i:i+3]
                Board_Info.append(Koma_Info)
                if Koma_Info[0] == "9" or Koma_Info[0] == "8":
                    continue
                Geister_Board[int(Koma_Info[1])][int(Koma_Info[0])] = Koma_Info[2]

            # 盤面状況の観察用
            print("_", "_", "_敵_", "_", "_")
            for i in range(6):
                print(Geister_Board[i])
            print("_", "_", "自身", "_", "_")
            print("\n") 
            """
            print("Game END.")

        # 入力された回数を実施した後の処理
    print("対戦回数 : ", cnt_recode)
    print("-----------------------")
    print(result_dic)

def Human_agent(): # 人がガイスターを操作するとき
    print("↓ どの駒を動かすかを [A ~ H] のどれか一つを入力 ↓")
    MoveKoma = input()
    print("↓ どの方向に動かすかを [N, E, S, W] のどれかを入力 ↓")
    MoveDir = input()
    if  97 <= ord(MoveKoma) < 105:
        MoveKoma = chr(ord(MoveKoma) - 32 )
    if ord(MoveDir) == 110 or ord(MoveDir) == 101 or ord(MoveDir) == 115 or ord(MoveDir) == 119:
        MoveDir = chr(ord(MoveDir) - 32)
    return MoveKoma, MoveDir

def Random_agent(server_response): # ランダムに手を生成するとき
    # 盤面の情報を取得する
    Board_list = ["*" for i in range(36)]
    My_Koma_list = []
    color_list = [[0, 0] for i in range(8)]
    res = list(server_response[4:])

    x = 0
    for i in range(0, 24, 3):
        My_Koma = res[i:i+3]
        My_Koma_list.append(res[i:i+3])
        x, y, color = int(My_Koma[0]), int(My_Koma[1])*6 , My_Koma[2]
        pos = x + y
        if pos > 35:
            continue
        x += 1
        Board_list[pos] = color
    #print(My_Koma_list)
    # 駒の名前と色をみる

    # 配列の並びは[x座標, y座標, 駒の色]
    flag = 0 # 手が正しいかを判定するためのフラグ
    out_list = [] # 打つことができない手を記録するためのリスト

    while flag == 0:
        # 駒をランダムに選択
        """
        0 ~ 7 > A ~ H
        """
        n = random.randint(0, 7)
        MoveKoma = chr(n + 65)
        koma_x, koma_y = int(My_Koma_list[n][0]), int(My_Koma_list[n][1])
        pos = koma_x + koma_y*6

        # 駒をランダムに上下左右に動かす
        """
        > NORTH なら y方向に -1
        > EAST なら x方向に +1 
        > SOUTH なら y方向に +1
        > WEST なら x方向に -1
        """
        Dir_list = ["NORTH", "EAST", "SOUTH", "WEST"] 
        n = random.randint(0, 3)
        MoveDir = Dir_list[n]
        
        for i in range(len(My_Koma_list)):
            if ["0", "0", "B"] == My_Koma_list[i]:
                MoveKoma = chr(i + 65)
                MoveDir = "WEST"
                flag += 1
                break
            elif ["5", "0", "B"] == My_Koma_list[i]:
                MoveKoma = chr(i + 65)
                MoveDir = "EAST"
                flag += 1
                break

        if flag == 1:
            break
        
        if [MoveKoma, MoveDir] in out_list:
            continue
        elif pos > 35:
            out_list.append([MoveKoma, MoveDir])
        # 手を打った時に盤面の外に出るか判定 
        else:
            if MoveDir == "NORTH" and pos <= 6:
                out_list.append([MoveKoma, MoveDir])
            elif MoveDir == "EAST" and pos % 6 == 5:
                out_list.append([MoveKoma, MoveDir])
            elif MoveDir == "SOUTH" and pos >= 30:
                out_list.append([MoveKoma, MoveDir])
            elif MoveDir == "WEST" and pos % 6 == 0:
                out_list.append([MoveKoma, MoveDir])
            else:
                # 選択された手が自身の駒と被らないか確認
                if MoveDir == "NORTH" and Board_list[pos-6] == "B" or MoveDir == "NORTH" and Board_list[pos-6] == "R":
                    out_list.append([MoveKoma, MoveDir])
                elif MoveDir == "EAST" and Board_list[pos+1] == "B" or MoveDir == "EAST" and Board_list[pos+1] == "R":
                    out_list.append([MoveKoma, MoveDir])
                elif MoveDir == "SOUTH" and Board_list[pos+6] == "B" or MoveDir == "SOUTH" and Board_list[pos+6] == "R":
                    out_list.append([MoveKoma, MoveDir])
                elif MoveDir == "WEST" and Board_list[pos-1] == "B" or MoveDir == "WEST" and Board_list[pos-1] == "R":
                    out_list.append([MoveKoma, MoveDir])
                else:
                    flag += 1
                    out_list = []

    return MoveKoma, MoveDir

def Judge(server_response):
    response = server_response
    if response[:3] == "WON":
        print("WIN")
        return "WIN"
    elif response[:3] == "LST":
        print("LOSE")
        return "LOSE"
    else:
        print("DRAW")
        return "DRAW"


print("↓ 先手なら 10000 を後手なら 10001 を入力 ↓")
port_number = int(input())
print("↓ 対戦回数を入力 ↓")
game_count = int(input())

Geister_Client(port_number, game_count)

print("")
print("Connecting End.")
