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
path = "C:/program_dir/geister_ai/lstm_data/"
bb = pd.read_csv(path + "nega_nega_board.csv", encoding="utf-8", header=None)
ll = pd.read_csv(path + "nega_nega_label.csv", encoding="utf-8", header=None)

# dataframe を list 型に変換
bb = bb.values.tolist()
bb = list(itertools.chain.from_iterable(bb))
ll = ll[0].values.tolist()
label_data, board_data = [], []

# String 型の要素をLSTMに入力できるように int 型に変換する
for i in range(len(bb)):
    if bb[i] == "*":
        board_data.append(0)
    elif bb[i] == "u":
        board_data.append(1)
    elif bb[i] == "R":
        board_data.append(2)
    elif bb[i] == "B":
        board_data.append(3)
    else:
        None
board_data = np.array(board_data)
board_data = board_data.reshape(7994, 6, 6)

for i in range(len(ll)):
    if ll[i] == "R":
        label_data.append(0)
    elif ll[i] == "B":
        label_data.append(1)
    else:
        None
label_data = np.array(label_data)

# パラメータの設定
batch_size = 32

units = 2
output_size = 2

# データを訓練データとテストデータに分割
x_train = board_data[:7001]
y_train = label_data[:7001]
x_test = board_data[7001:]
y_test = label_data[7001:]

# モデルの構築
model = keras.Sequential(
    [
        keras.layers.LSTM(units, input_shape=(6, 6), return_sequences=True),
        keras.layers.LSTM(units, input_shape=(6, 6)),
        keras.layers.BatchNormalization(),
        keras.layers.Dense(output_size)
    ]
)

model.compile(
    loss = "binary_crossentropy",
    optimizer = "Adam",
    metrics = ["accuracy"],
)

model.summary()

log_dir = "logs/fit/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)

# 学習させる
model.fit(
    x_train, y_train, validation_data=(x_test, y_test), batch_size=batch_size, epochs=30, callbacks=[tensorboard_callback]
)

# テストデータで評価
print("--------------------")
test_loss, test_acc = model.evaluate(x_test, y_test)
print("test_loss = ", test_loss)
print("test_acc = ", test_acc)