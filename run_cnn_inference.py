from cnn_method import *
from cnn_preproc_function import *
from cnn_inference_method import *

import optparse
import numpy as np
import pandas as pd

import sklearn
from sklearn import preprocessing

import keras
import tensorflow as tf

from keras_model_configuration import *
from keras_metric import *

import datetime
import time
import os

from sklearn.externals import joblib

#OPTS PARSER
optparser = optparse.OptionParser()
optparser.add_option("-a", "--assetindex", default=0, help="assetindex")
optparser.add_option("-d", "--gpudevice", default="1", help="gpudevice")
opts = optparser.parse_args()[0]

assetindex = int(opts.assetindex)
gpudevice = opts.gpudevice

#GPU CONFIG
os.environ["TF_MIN_GPU_MULTIPROCESSOR_COUNT"] = "4"
os.environ["CUDA_VISIBLE_DEVICES"]=gpudevice
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
session = tf.Session(config=config)

#PARAMS:
main_folder = os.path.join("output","no_scale_models")
setups_folder = [j for j in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder,j))]
setup_folder_name = setups_folder[assetindex]

loss_criteria = "precision"
loss_mode = "max"
batch_size = 64

model_inference(main_folder, setup_folder_name, loss_criteria, loss_mode, batch_size)
