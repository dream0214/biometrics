# -*- coding: utf-8 -*-
"""1771078_정드림_멀티모달_2차_코드_모델1개.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1H6rJ4BBIvLVpdSgVR5IQxYSZ5ys-VxdL
"""

from glob import glob
import imageio
import cv2
import numpy as np
import pandas as pd
from PIL import Image
from google.colab import files
import imgaug.augmenters as iaa
import imgaug.imgaug

from sklearn.model_selection import train_test_split,StratifiedKFold,KFold,cross_validate
from sklearn.metrics import make_scorer, accuracy_score,recall_score,precision_score,f1_score,classification_report

import keras
from keras import backend as K
from keras import layers,optimizers
from keras.layers import Input,Add,Dense,Activation, Flatten,Conv2D,AveragePooling2D, MaxPooling2D, GlobalMaxPooling2D, MaxPooling2D, Dropout,ZeroPadding2D
from keras.layers.normalization import BatchNormalization
from keras.models import Model,load_model,Sequential
from keras.initializers import glorot_uniform
from keras.callbacks import EarlyStopping,ModelCheckpoint

import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


#https://machinelearningknowledge.ai/keras-implementation-of-resnet-50-architecture-from-scratch/

import os,sys
from google.colab import drive

drive.mount('/content/mnt')

!unzip /content/mnt/MyDrive/dataset/04_multimodal_training.zip -d /content/mnt/MyDrive/dataset/multimodal_training
!unzip /content/mnt/MyDrive/dataset/04_multimodal_test.zip -d /content/mnt/MyDrive/dataset/multimodal_test

#path 정의
trainpath='/content/mnt/MyDrive/dataset/multimodal_training/'
testpath='/content/mnt/MyDrive/dataset/multimodal_test/'

#test data 숫자 길이 맞추기(0 채우기)
file_names=os.listdir(testpath)
for file_name in file_names:
  src=os.path.join(testpath,file_name)
  dst=file_name.zfill(11)
  dst=os.path.join(testpath,dst)
  os.rename(src,dst)

#face training data 불러와서 augmentation

facetraindata=glob(trainpath+'*face*')
facetraindata.sort()

faceimgheight=56
faceimgwidth=46

faceseq = iaa.Sequential([
    iaa.Fliplr(0.5),
    iaa.Multiply((0.7, 1.3)),
    iaa.Affine(
        translate_percent = {"x":(-0.1,0.1),"y":(-0.1,0.1)}
    )
    ])

def readFaceTrainingImages(data):
  images=[]
  for i in range(len(data)):
    img = cv2.imread(data[i])
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img,(faceimgwidth,faceimgheight))
    images.append(img)
    for j in range(3):
      img2 = faceseq.augment_image(img)
      images.append(img2)
  return images

facetrainingimages=[]
facetrainingimages=readFaceTrainingImages(facetraindata)

face_arr = np.asarray(facetrainingimages)
face_arr = face_arr.astype('float32')
face_arr=face_arr.reshape(-1,faceimgwidth,faceimgheight,3) ####
face_arr=face_arr/255
print(face_arr.shape)

#iris training data 불러와서 augmentation

iristraindata=glob(trainpath+'*iris*')
iristraindata.sort()

irisimgheight=224
irisimgwidth=224

def iris_augment(img):
  img=tf.image.random_flip_left_right(img)
  img=tf.image.random_flip_up_down(img)
  img=tf.keras.preprocessing.image.random_shift(img,0.2,0.2,fill_mode='constant')
  cval='black'
  #img=tf.keras.preprocessing.image.random_brightness(img,[-0.2,0.2])
  #img=tf.image.per_image_standardization(img)
  return img


irisseq = iaa.Sequential([
    iaa.Fliplr(0.5),
    iaa.Flipud(0.5),
    iaa.Multiply((0.9, 1.1)),
    iaa.Affine(
        scale = (0.9,1.1),
        rotate = (-45, 45),
        translate_percent = {"x":(-0.1,0.1),"y":(-0.1,0.1)}
    )
    ])

def readIrisTrainingImages(data):
  images=[]
  for i in range(len(data)):
    img = cv2.imread(data[i])
    img=img[:,70:700]
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img,(irisimgwidth,irisimgheight))
    images.append(img)
    for j in range(3):
      img2=irisseq.augment_image(img)
      images.append(img2)
  return images

iristrainingimages=[]
iristrainingimages=readIrisTrainingImages(iristraindata)

iris_arr = np.asarray(iristrainingimages)
iris_arr = iris_arr.astype('float32')
iris_arr=iris_arr.reshape(-1,irisimgwidth,irisimgheight,3) ####
iris_arr=iris_arr/255
print(iris_arr.shape)

#face test data 가져오기(증강x)

def readFaceTestImages(data):
  images=[]
  for i in range(len(data)):
    img = cv2.imread(data[i])
    img = cv2.resize(img,(faceimgwidth,faceimgheight))
    images.append(img)
  return images

facetestdata=glob(testpath+'*face*')
facetestdata.sort()
facetestimages=[]
facetestimages=readFaceTestImages(facetestdata)

facetest_arr = np.asarray(facetestimages)
facetest_arr = facetest_arr.astype('float32')
facetest_arr=facetest_arr.reshape(-1,faceimgwidth,faceimgheight,3) ####
facetest_arr=facetest_arr/255
print(facetest_arr.shape)

#iris test data 가져오기(증강x)

def readIrisTestImages(data):
  images=[]
  for i in range(len(data)):
    img = cv2.imread(data[i])
    img=img[:,70:700]
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img,(irisimgwidth,irisimgheight))
    images.append(img)
  return images

iristestdata=glob(testpath+'*iris*')
iristestdata.sort()
iristestimages=[]
iristestimages=readIrisTestImages(iristestdata)

iristest_arr = np.asarray(iristestimages)
iristest_arr = iristest_arr.astype('float32')
iristest_arr=iristest_arr.reshape(-1,irisimgwidth,irisimgheight,3) ####
iristest_arr=iristest_arr/255
print(iristest_arr.shape)

#show face training set images

fig, axes = plt.subplots(4, 8, figsize=(20, 10), subplot_kw={'xticks':(), 'yticks':()})
for image, ax in zip(facetrainingimages, axes.ravel()):
  ax.imshow(image,cmap='gray')
plt.show()

#show face test set images

fig, axes = plt.subplots(4, 8, figsize=(20, 10), subplot_kw={'xticks':(), 'yticks':()})
for image, ax in zip(facetestimages, axes.ravel()):
  ax.imshow(image)
plt.show()

#show iris training set images

fig, axes = plt.subplots(4, 8, figsize=(20, 10), subplot_kw={'xticks':(), 'yticks':()})
for image, ax in zip(iristrainingimages, axes.ravel()):
  ax.imshow(image)
plt.show()

#show iris test set images

fig, axes = plt.subplots(4, 8, figsize=(20, 10), subplot_kw={'xticks':(), 'yticks':()})
for image, ax in zip(iristestimages, axes.ravel()):
  ax.imshow(image)
plt.show()

#train data의 label 만들기

label=[]
for i in range(64):
  for j in range(16):
      label.append(i)

print(label)

label_arr=np.array(label)
print(label_arr.shape)

#toy Resnet

face_input = keras.Input(shape=(46, 56, 3), dtype='float32', name='face_input')
x = layers.Conv2D(32, 3, activation="relu")(face_input)
x = layers.Conv2D(64, 3, activation="relu")(x)
block_1_output = layers.MaxPooling2D(3)(x)

x = layers.Conv2D(64, 3, activation="relu", padding="same")(block_1_output)
x = layers.Conv2D(64, 3, activation="relu", padding="same")(x)
block_2_output = layers.add([x, block_1_output])

x = layers.Conv2D(64, 3, activation="relu", padding="same")(block_2_output)
x = layers.Conv2D(64, 3, activation="relu", padding="same")(x)
block_3_output = layers.add([x, block_2_output])

x = layers.Conv2D(64, 3, activation="relu")(block_3_output)
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dense(256, activation="relu")(x)
x = layers.Dropout(0.5)(x)
face_output = layers.Dense(64)(x)


iris_input = keras.Input(shape=(224, 224, 3),dtype='float32', name='iris_input')
y = layers.Conv2D(32, 3, activation="relu")(iris_input)
y = layers.Conv2D(64, 3, activation="relu")(y)
block_1_output = layers.MaxPooling2D(3)(y)

y = layers.Conv2D(64, 3, activation="relu", padding="same")(block_1_output)
y = layers.Conv2D(64, 3, activation="relu", padding="same")(y)
block_2_output = layers.add([y, block_1_output])

y = layers.Conv2D(64, 3, activation="relu", padding="same")(block_2_output)
y = layers.Conv2D(64, 3, activation="relu", padding="same")(y)
block_3_output = layers.add([y, block_2_output])

y = layers.Conv2D(64, 3, activation="relu", padding="same")(block_3_output)
y = layers.Conv2D(64, 3, activation="relu", padding="same")(y)
block_4_output = layers.add([y, block_3_output])

y = layers.Conv2D(128, 3, activation="relu")(block_4_output)
y = layers.GlobalAveragePooling2D()(y)
y = layers.Dense(256, activation="relu")(y)
y = layers.Dropout(0.5)(y)
iris_output = layers.Dense(64)(y)


z = keras.layers.concatenate([face_output, iris_output])
model_output = layers.Dense(64,activation=tf.nn.softmax,name='model_output')(z)

model = keras.Model(inputs=[face_input, iris_input], outputs=model_output)
model.summary()

keras.utils.plot_model(model, "mini_resnet.png", show_shapes=True)

batch_size=32
epochs=30
lr=0.005

model.compile(optimizer=keras.optimizers.RMSprop(lr),
              loss='sparse_categorical_crossentropy',metrics=['acc'])

kfold = KFold(n_splits=4,shuffle=True)
i=0
for train_index, validate_index in kfold.split(iris_arr,label_arr):
  i+=1; print('<',i,' step>')
  iris_train, iris_val = iris_arr[train_index], iris_arr[validate_index]
  face_train, face_val = face_arr[train_index], face_arr[validate_index]
  y_train, y_val = label_arr[train_index], label_arr[validate_index]
  
  history=model.fit({"face_input":face_train,"iris_input":iris_train},y_train,
                    epochs=epochs,batch_size=batch_size,
                    validation_data=({"face_input":face_val,"iris_input":iris_val},y_val))

  epochs_range = range(epochs)
  plt.figure(figsize=(8, 8))
  plt.subplot(1, 2, 1)
  plt.plot(epochs_range, history.history['acc'], label='Training Accuracy')
  plt.plot(epochs_range, history.history['val_acc'], label='Validation Accuracy')
  plt.legend(loc='lower right')
  plt.title('Training and Validation Accuracy')

  plt.subplot(1, 2, 2)
  plt.plot(epochs_range, history.history['loss'], label='Training Loss')
  plt.plot(epochs_range, history.history['val_loss'], label='Validation Loss')
  plt.legend(loc='upper right')
  plt.title('Training and Validation Loss')
  plt.show()

y_pred = model.predict({"face_input":face_val,"iris_input":iris_val},
                         batch_size=batch_size, verbose=1)
y_pred_bool = np.argmax(y_pred, axis=1)
print(classification_report(y_val, y_pred_bool))

predictions=model.predict({"face_input":facetest_arr,"iris_input":iristest_arr})
correct_prediction=tf.argmax(predictions,1)
print(correct_prediction)

predictions=model.predict({"face_input":facetest_arr,"iris_input":iristest_arr})
correct_prediction=tf.argmax(predictions,1)
print(correct_prediction)

onemodeldf=pd.DataFrame(correct_prediction)
onemodeldf

onemodeldf.to_csv('onemodel2.txt')
files.download('onemodel2.txt')