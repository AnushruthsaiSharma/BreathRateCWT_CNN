import numpy as np
import pandas as pd
import pywt
import cv2
import os
import matplotlib.pyplot as plt

def generate_signal(num_points=1024, freq=0.25, noise=0.05):
    t = np.linspace(0, 10, num_points)
    return 0.4 * np.sin(2 * np.pi * freq * t) + noise * np.random.randn(num_points)

def save_signal_and_cwt(i, output_dir='media/cwt_images'):
    os.makedirs(output_dir, exist_ok=True)
    signal = generate_signal()
    
    # Save raw txt
    txt_path = os.path.join(output_dir, f'signal_{i}.txt')
    np.savetxt(txt_path, signal, fmt="%.6f")

    # Save CSV
    df = pd.DataFrame({'time_index': np.arange(len(signal)), 'voltage': signal})
    df.to_csv(os.path.join(output_dir, f'signal_{i}.csv'), index=False)

    # CWT Image
    coef, _ = pywt.cwt(signal, np.arange(1, 128), 'morl')
    plt.figure(figsize=(6, 3))
    plt.imshow(coef, cmap='jet', aspect='auto')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'cwt_{i}.png'))
    plt.close()

# Generate 5 sample signals
for i in range(1, 6):
    save_signal_and_cwt(i)
