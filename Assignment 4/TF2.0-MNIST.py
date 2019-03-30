# Build the model

from keras.layers.normalization import BatchNormalization
from keras.layers.convolutional import Conv2D, SeparableConv2D
from keras.layers.convolutional import AveragePooling2D, MaxPooling2D, ZeroPadding2D
from keras.layers.core import Activation, Dense
from CyclicLearningRate.clr_callback import *
from keras.layers import Flatten, Input, add
from keras.optimizers import Adam
from keras.callbacks import *
from keras.models import Model
from keras.regularizers import l2
from keras import backend as K

class ResNet:
	@staticmethod
	def residual_module(data, K, stride, chanDim, red=False, reg=0.0001, bnEps=2e-5, bnMom=0.9, bit=0):
		shortcut = data

		bn1 = BatchNormalization(axis=chanDim, epsilon=bnEps, momentum=bnMom)(data)
		act1 = Activation("relu")(bn1)
		conv1 = Conv2D(int(K * 0.25), (1, 1), use_bias=False, kernel_regularizer=l2(reg))(act1)

		bn2 = BatchNormalization(axis=chanDim, epsilon=bnEps, momentum=bnMom)(conv1)
		act2 = Activation("relu")(bn2)
		conv2 = Conv2D(int(K * 0.25), (3, 3), strides=stride, padding="same", use_bias=False, kernel_regularizer=l2(reg))(act2)

		bn3 = BatchNormalization(axis=chanDim, epsilon=bnEps, momentum=bnMom)(conv2)
		act3 = Activation("relu")(bn3)
		conv3 = Conv2D(K, (1, 1), use_bias=False, kernel_regularizer=l2(reg))(act3)

		if red and stride == (2,2):
			shortcut = MaxPooling2D((2,2))(bn1)

		shortcut = Conv2D(K, (1,1))(shortcut)
		x = add([conv3, shortcut])

		return x

	@staticmethod
	def build(width, height, depth, classes, stages, filters, reg=0.0001, bnEps=2e-5, bnMom=0.9):
		inputShape = (height, width, depth)
		chanDim = -1

		inputs = Input(shape=inputShape)
		x = BatchNormalization(axis=chanDim, epsilon=bnEps, momentum=bnMom)(inputs)
		x = Activation("relu")(x)
		x = Conv2D(filters[0], (5, 5), use_bias=False, padding="same", kernel_regularizer=l2(reg))(x)
		x = BatchNormalization(axis=chanDim, epsilon=bnEps, momentum=bnMom)(x)
		x = Activation("relu")(x)
		x = ZeroPadding2D((1, 1))(x)
		x = MaxPooling2D((3, 3), strides=(2, 2))(x)
    
		for i in range(0, len(stages)):
			stride = (1, 1) if i == 0 else (2, 2)
			x = ResNet.residual_module(x, filters[i + 1], stride, chanDim, red=True, bnEps=bnEps, bnMom=bnMom)

			for j in range(0, stages[i] - 1):
				x = ResNet.residual_module(x, filters[i + 1], (1, 1), chanDim, bnEps=bnEps, bnMom=bnMom)

		x = BatchNormalization(axis=chanDim, epsilon=bnEps, momentum=bnMom)(x)
		x = Activation("relu")(x)
		x = AveragePooling2D((8, 8))(x)
  
		x = Conv2D(200, (1,1), kernel_regularizer=l2(reg))(x)
		x = Flatten()(x)
		x = Activation("softmax")(x)

		model = Model(inputs, x, name="resnet")

		return model



