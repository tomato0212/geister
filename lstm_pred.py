#%load_ext tensorboard

import datetime
import random
import numpy as np
import pandas as pd 
import tensorflow as tf 
from tensorflow import keras 
from tensorflow.keras import layers
from keras.models import Sequential
from keras.layers.core import Dense, Activation
from keras.layers.recurrent import LSTM
import itertools

# 前回の実行時のログをすべて消去
#rm -rf ./logs/

# データを読み込み
def read_board(board_his, board_now):
    bb = board_his
    bb_now = board_now

    bb = list(itertools.chain.from_iterable(bb))
    bb_now = list(itertools.chain.from_iterable(bb_now))

    # String 型の要素をLSTMに入力できるように int 型に変換する
    for i, v in enumerate(bb):
        if v == "*":
            bb[i] = 0
        elif v == "u":
            bb[i] = 1
        elif v == "R":
            bb[i] = 2
        elif v == "B":
            bb[i] = 3

    for i, v in enumerate(bb_now):
        if v == "*":
            bb_now[i] = 0
        elif v == "u":
            bb_now[i] = 1
        elif v == "R":
            bb_now[i] = 2
        elif v == "B":
            bb_now[i] = 3
    
    bb = np.array(bb)
    bb_now = np.array(bb_now)
    pred_bb = np.r_[bb, bb_now]
    pred_bb = pred_bb.reshape(2, 6, 6)

    return pred_bb

def color_pred(pred_bb):
    model_ss = tf.keras.models.load_model("model_1")
    predictions = model_ss.predict(pred_bb[0:2])
    result_pred_num = predictions[1]

    return result_pred_num.argmax() #-> 赤なら 0 , 青なら 1

"""
board, label = read_board()
pred_color = color_pred(board, label)
print("predicted is", pred_color)
print("True labal is", label[1])
"""

#model_ss.summary()

#log_dir = "logs/fit/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)

"""
# テストデータを用いて作成したモデルの評価（正解率と損失関数の2つ）
print("--------------------")
test_loss, test_acc = model_ss.evaluate(x_test, y_test)
print("test_loss = ", test_loss)
print("test_acc = ", test_acc)
print("--------------------")
"""