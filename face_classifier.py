# -*- coding: utf-8 -*-
"""
Created on Mon Oct  1 11:00:25 2018

@author: 123
"""

# =============================================================================
# facenet+Knn的思路：
# 1、用facenet将所有图片生成128维向量，准备训练数据
# 2、建立KNN模型，进行训练和测试
# 3、用训练好的模型进行实时人脸识别
# =============================================================================

# 运行的时候有时会遇到name 'python' is not defined，通过restart kernel解决



import numpy as np
#import pickle
import time
from feature_extract import resize_image, facenet, img_to_encoding
from sklearn.model_selection import cross_val_score, ShuffleSplit, KFold, learning_curve
#from sklearn.neighbors import KNeighborsClassifier
from sklearn.externals import joblib
import matplotlib.pyplot as plt
from sklearn.svm import SVC
from logs import log
import h5py
import cv2


class Dataset:
    # http://www.runoob.com/python3/python3-class.html
    # 很多类都倾向于将对象创建为有初始状态的。
    # 因此类可能会定义一个名为 __init__() 的特殊方法（构造方法），类定义了 __init__() 方法的话，类的实例化操作会自动调用 __init__() 方法。
    # __init__() 方法可以有参数，参数通过 __init__() 传递到类的实例化操作上，比如下面的参数path_name。
    # 类的方法与普通的函数只有一个特别的区别——它们必须有一个额外的第一个参数名称, 按照惯例它的名称是 self。
    # self 代表的是类的实例，代表当前对象的地址，而 self.class 则指向类。
    def __init__(self, path_name): 
        # 训练集
        self.X_train = None
        self.y_train = None
        
        # 数据集加载路径
        self.path_name = path_name
    
    # 加载数据集
    def load(self):
#        # 加载数据集到内存，pickle方式，改用上下文管理器形式
#        with open(self.path_name + 'embeddings.pkl', 'rb') as file_embeddings:
#            X_embeddings = pickle.load(file_embeddings) # 考虑这里分批执行，否则可能内存不够，这里在img_to_encoding函数里通过predict的batch_size参数实现
#        # 加载128维特征向量
#        with open(self.path_name + 'labels.pkl', 'rb') as file_labels:
#            labels = pickle.load(file_labels)
#        hdf5方式加载数据
#        KeyError: "Unable to open object (object 'face_embeddings' doesn't exist)"
        with h5py.File(self.path_name + 'face_embeddings.hdf5', 'r') as f_faces:
            #        for key in f_faces.keys():
            #            print("keys: ", key)
#           读不到数据集，参考 https://www.pythonforthelab.com/blog/how-to-use-hdf5-files-in-python/
            X_embeddings = f_faces['face_embeddings'][:]
        with h5py.File(self.path_name + 'face_labels.hdf5', 'r') as f_labels:
            labels = f_labels['face_labels'][:]
        # 输出训练数据集的维数和数量
        print('X_train shape', X_embeddings.shape)
        print('y_train shape', labels.shape)
        print(X_embeddings.shape[0], 'train samples')
        # 这里对X_train就不再进一步normalization了，因为已经在facenet里有了l2_norm
        self.X_train = X_embeddings
        self.y_train = labels

# 定义并训练KNN Classifier模型
#class Knn_Model:
#    # 初始化构造方法
#    def __init__(self):
#        self.model = None
#    def cross_val_and_build_model(self, dataset):
#        k_range = range(1,31)
##        k_range = range(1,60)
#        k_scores = []
#        print("k vs accuracy:")
#        for k in k_range:
#            knn = KNeighborsClassifier(n_neighbors = k)
##            cv = KFold(n_splits = 10, shuffle = True, random_state = 0)
#            # https://github.com/scikit-learn/scikit-learn/issues/6361
#            # http://scikit-learn.org/stable/modules/cross_validation.html#computing-cross-validated-metrics
#            cv = ShuffleSplit(random_state = 0) # n_splits : int, default 10; test_size : float, int, None, default=0.1，设置了random_state = 0，每次的数据划分相同，训练结果也相同
##            score = cross_val_score(knn, dataset.X_train, dataset.y_train, cv = 10, scoring = 'accuracy').mean() # cv参数取整数的时候默认用KFold方法划分数据，这里两次运行的结果一样，可能说明KFold里的random_state参数设为了整数
#            score = cross_val_score(knn, dataset.X_train, dataset.y_train, cv = cv, scoring = 'accuracy').mean() # numpy.ndarray.mean
#            k_scores.append(score)
#            print(k, ":", score)
#        # 可视化结果
#        plt.plot(k_range, k_scores)
#        plt.xlabel('Value of K for KNN')
#        plt.ylabel('Cross-Validated Accuracy')
#        plt.show()
#        n_neighbors_max = np.argmax(k_scores) + 1
#        print("The best k is: ", n_neighbors_max)
#        print("The accuracy is: ", k_scores[n_neighbors_max - 1], "When n_neighbor is: ", n_neighbors_max)
#        
#        self.model = KNeighborsClassifier(n_neighbors = n_neighbors_max)
#        
#        # 目前k=1时最佳，准确率达到88%+，可能原因参考https://stackoverflow.com/questions/36637112/why-does-k-1-in-knn-give-the-best-accuracy
#        # Data tests have high similarity with the training data; The boundaries between classes are very clear
#        # In general, the value of k may reduce the effect of noise on the classification, but makes the boundaries between each classification becomes more blurred.
#        # 使用shuffle后准确率显著提升，k=1时达到98.9%+，我理解的是shuffle后训练集和测试集的数据类别分布更均衡，shuffle前可能数据的类别分布不均衡，导致准确率较低。
#    def train(self, dataset):
#        self.model.fit(dataset.X_train, dataset.y_train)
##        cv1 = ShuffleSplit(random_state = 0)
##        train_sizes, train_accuracies, test_accuracies = learning_curve(self.model, dataset.X_train, dataset.y_train, cv = cv1, scoring = 'accuracy', train_sizes=[0.1, 0.25, 0.5, 0.75, 1])
##        train_accuracies_mean = np.mean(train_accuracies, axis = 1)
##        test_accuracies_mean = np.mean(test_accuracies, axis = 1)
##        print('train accuracies: ', train_accuracies_mean) # train_accuracy都是1，因为knn本质是记住所有训练数据
##        print('test accuracies: ', test_accuracies_mean)
##        plt.plot(train_sizes, train_accuracies_mean, 'o-', color="r", label="Training")
##        plt.plot(train_sizes, test_accuracies_mean, 'o-', color="g", label="Cross-validation")
##        plt.xlabel("Training examples")
##        plt.ylabel("Accuracy")
##        plt.legend(loc="best")
##        plt.show()
#    def save_model(self, file_path):
#        #save model
#        joblib.dump(self.model, file_path)
#    def load_model(self, file_path):
#        self.model = joblib.load(file_path)
#    def predict(self, image):
#        image = resize_image(image)
#        image_embedding = img_to_encoding(np.array([image]), facenet)
#        start = time.time()
#        label = self.model.predict(image_embedding) # predict方法返回值是array of shape [n_samples]，因此下面要用label[0]从array中取得数值，https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsClassifier.html#sklearn.neighbors.KNeighborsClassifier.predict
#        log("Predicting one face using knn model took {} seconds.".format(time.time() - start))
#        return label[0]

# https://teamtreehouse.com/community/getting-a-syntax-error-at-main
# 注意这里遇到了一个bug，在下面的代码上提示invalid syntax，其实是因为上面的print语句少了最后一个圆括号
# The most likely reason for you to get a syntax error at the end of the following valid code
# is because you have a syntax error earlier in the code, 
# but it's not until the interpreter gets to the end of this statement that it realises that there is a problem. 
# A common syntax error you might have is a missing close parenthesis on the last line of your code before this statement.
        
# knn k-fold思路，对knn不同k值循环，每次循环使用k折交叉验证，画出不同k值对应的evaluate准确率曲线，找到准确率最高的k值
 
# svm分类思路：
class svm_Model:
    def __init__(self):
        self.model = None
    def build_model(self):
        self.model = SVC(kernel = 'linear', decision_function_shape = 'ovo')
    def train(self, dataset):
        self.model.fit(dataset.X_train, dataset.y_train)
#        https://morvanzhou.github.io/tutorials/machine-learning/sklearn/3-3-cross-validation2/
        cv = ShuffleSplit(random_state = 0)
        train_sizes, train_accuracies, test_accuracies = learning_curve(self.model, dataset.X_train, dataset.y_train, cv = cv, scoring = 'accuracy', train_sizes=[0.1, 0.25, 0.5, 0.75, 1])
        train_accuracies_mean = np.mean(train_accuracies, axis = 1)
        test_accuracies_mean = np.mean(test_accuracies, axis = 1)
        print('train accuracies: ', train_accuracies_mean)
        print('test accuracies: ', test_accuracies_mean)
        plt.plot(train_sizes, train_accuracies_mean, 'o-', color="r", label="Training")
        plt.plot(train_sizes, test_accuracies_mean, 'o-', color="g", label="Cross-validation")
        plt.xlabel("Training examples")
        plt.ylabel("Accuracy")
        plt.legend(loc="best")
        plt.show()
    def save_model(self, file_path):
        joblib.dump(self.model, file_path)
    def load_model(self, file_path):
        self.model = joblib.load(file_path)
    def predict(self, image):
        image = resize_image(image)
        image_embedding = img_to_encoding(np.array([image]), facenet)
        start = time.time()
        label = self.model.predict(image_embedding) # predict方法返回值是array of shape [n_samples]，因此下面要用label[0]从array中取得数值，https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsClassifier.html#sklearn.neighbors.KNeighborsClassifier.predict
        log("Predicting one face using svm model took {} seconds.".format(time.time() - start))
        return label[0]
       
if __name__ == "__main__":
#    pickle方式加载数据
    dataset = Dataset('./dataset_h5/')
    start = time.time()
    dataset.load()
    log("Loading pkl dataset took {} seconds.".format(time.time() - start))
#    hdf5方式加载数据
#    dataset = Dataset('./dataset_h5/')
#    start = time.time()
#    dataset.load()
#    日志重复输出问题，参考https://blog.csdn.net/huilan_same/article/details/51858817
#    log("Loading hdf5 dataset took {} seconds.".format(time.time() - start))
#    用一张图片测试knn和svm模型
    image = cv2.imread('./dataset/donghu/175.jpg')
#    model = Knn_Model()
#    model.cross_val_and_build_model(dataset)
#    model.train(dataset)
#    model.save_model('./model/knn_classifier.model')
#    start = time.time()
#    model.load_model('./model/knn_classifier.model')
#    log("Loading knn model took {} seconds.".format(time.time() - start))
#    start1 = time.time()
#    model.predict(image)
#    log("Predicting one face using knn model took {} seconds.".format(time.time() - start1))
    model = svm_Model()
    model.build_model()
    model.train(dataset)
    model.save_model('./model/svm_classifier.model')
    start = time.time()
    model.load_model('./model/svm_classifier.model')
    log("Loading svm model took {} seconds.".format(time.time() - start))
    start1 = time.time()
    model.predict(image)
    log("Predicting one face using svm model took {} seconds.".format(time.time() - start1))
