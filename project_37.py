import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
train_df = pd.read_csv('C://Users//egorb//Downloads//MNIST_train.csv')
test_df = pd.read_csv('C://Users//egorb//Downloads//MNIST_test.csv')
train_binary = train_df[train_df['label'].isin([0, 1])]
X_train = train_binary.drop('label', axis=1).values
y_train = train_binary['label'].values
X_test = test_binary.drop('label', axis=1).values
y_test = test_binary['label'].values
pca_full = PCA(svd_solver='full')
pca_full.fit(X_train)
cumsum = np.cumsum(pca_full.explained_variance_ratio_)
M = np.where(cumsum > 0.9)[0][0] + 1
pca = PCA(n_components=M, svd_solver='full')
X_train_pca = pca.fit_transform(X_train)
X_test_pca = pca.transform(X_test)
first_image_pc1 = X_train_pca[0, 0]
model = GradientBoostingClassifier(
    n_estimators=500,
    learning_rate=0.8,
    random_state=23,
    max_depth=2
)
model.fit(X_train_pca, y_train)
y_pred = model.predict(X_test_pca)
accuracy = accuracy_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)
print("\nМатрица ошибок:")
print(cm)
tp = cm[1,1]
print(f"Минимальное количество компонент M = {M}")
print(f"Координата 1-й главной компоненты для 1-го изображения: {first_image_pc1:.3f}")
print(f"Точность модели: {accuracy:.3f}")
print(f"TP (True Positives) = {tp}")
