import numpy as np
import pandas as pd
import cv2
import pywt
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, Flatten, Dense
from tensorflow.keras.optimizers import Adam

def cwt_transform(signal):
    scales = np.arange(1, 128)
    coef, _ = pywt.cwt(signal, scales, 'morl')
    return coef

def train_model(dataset_path):
    df = pd.read_csv(dataset_path)

    # ✅ Step 1: Group BPM classes into ranges (e.g., 10–19 → class 1)
    df['bpm_class'] = df['bpm_class'].apply(lambda x: int(float(x)) // 10)

    # ✅ Step 2: Group voltage signals per subject
    grouped = df.groupby(['subject_id', 'bpm_class'])['voltage'].apply(list).reset_index()

    X, y = [], []

    for index, row in grouped.iterrows():
        try:
            signal = row['voltage']
            if len(signal) < 50:
                continue

            signal = np.array(signal, dtype=float)

            # ✅ Normalize signal
            signal = (signal - np.mean(signal)) / np.std(signal)

            cwt_img = cwt_transform(signal)
            resized_img = cv2.resize(cwt_img, (64, 64))
            X.append(resized_img)
            y.append(row['bpm_class'])
        except Exception as e:
            print(f"Skipping row {index}: {e}")
            continue

    if len(X) == 0:
        raise ValueError("❌ No valid voltage data found in dataset.")

    X = np.array(X).reshape(-1, 64, 64, 1)
    y = np.array(y)

    # ✅ Step 3: Encode class labels
    encoder = LabelEncoder()
    y = encoder.fit_transform(y)
    np.save('trained_model/label_classes.npy', encoder.classes_)

    # ✅ Step 4: Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    # ✅ Step 5: Improved CNN architecture
    model = Sequential([
        Conv2D(32, (3, 3), activation='relu', input_shape=(64, 64, 1)),
        Conv2D(64, (3, 3), activation='relu'),
        Flatten(),
        Dense(128, activation='relu'),
        Dense(len(np.unique(y)), activation='softmax')
    ])

    model.compile(optimizer=Adam(learning_rate=0.001), loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    # ✅ Step 6: Train longer
    model.fit(X_train, y_train, epochs=30, batch_size=16, verbose=1)

    # ✅ Step 7: Evaluate and save
    _, accuracy = model.evaluate(X_test, y_test, verbose=0)

    os.makedirs('trained_model', exist_ok=True)
    model.save('trained_model/cnn_model.h5')

    return accuracy
