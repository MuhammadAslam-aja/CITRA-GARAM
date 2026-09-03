import cv2 as cv
import numpy as np
import os
import matplotlib.pyplot as plt
import pandas as pd
import math as mt
from skimage.feature import graycomatrix, graycoprops
from skimage import io
from sklearn.metrics import accuracy_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import GridSearchCV, train_test_split, cross_val_score
from PIL import Image


def dataImage(image):
    base_dir = os.getcwd().replace('\\', '/') + '/upload/klasifikasi/'
    files_dir = os.path.join(base_dir, image)
    return files_dir

def Preprocessing(image):
    gambar = cv.imread(image)
    if gambar is None:
        raise ValueError(f"Cannot load image: {image}")

    # Convert to grayscale
    tmp = cv.cvtColor(gambar, cv.COLOR_BGR2GRAY)
    target_resolusi = (600, 600)

    # Improved thresholding for salt images
    # Use adaptive threshold for better salt grain detection
    # First, apply Gaussian blur to reduce noise
    blurred = cv.GaussianBlur(tmp, (5, 5), 0)
    
    # Use Otsu's thresholding for automatic threshold selection
    _, mask = cv.threshold(blurred, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)
    
    # Morphological operations to clean up the mask
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (7, 7))
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)
    mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel)

    # Create RGBA image
    b, g, r = cv.split(gambar)
    rgba = [b, g, r, mask]
    dst = cv.merge(rgba, 4)

    # Find contours and get the largest one
    contours, hier = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        # If no contours found, use the entire image
        x, y, w, h = 0, 0, gambar.shape[1], gambar.shape[0]
        cropped = dst
        mask_cropped = mask
    else:
        selected = max(contours, key=cv.contourArea)
        x, y, w, h = cv.boundingRect(selected)
        
        # Add padding around the bounding box
        padding = 10
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(gambar.shape[1] - x, w + 2*padding)
        h = min(gambar.shape[0] - y, h + 2*padding)
        
        cropped = dst[y:y+h, x:x+w]
        mask_cropped = mask[y:y+h, x:x+w]

    gray = cv.cvtColor(cropped, cv.COLOR_BGRA2GRAY)

    # Resize to target resolution
    resultGray = cv.resize(gray, target_resolusi)
    resultOri = cv.resize(cropped[:, :, :3], target_resolusi)  # Remove alpha channel

    return [resultOri, resultGray]

# fungsi untuk pemanggilan nilai fitur glcm
def GLCM(gray):
    """
    Improved GLCM feature extraction for salt texture analysis
    """
    # Reduce gray levels for better texture analysis of salt
    # Salt images typically don't need 256 gray levels
    gray_levels = 64
    gray_reduced = (gray // (256 // gray_levels)).astype(np.uint8)
    
    # Multiple distances and angles for comprehensive texture analysis
    distances = [1, 2, 3]  # Different pixel distances
    angles = [0, np.pi/4, np.pi/2, 3*np.pi/4]  # 0°, 45°, 90°, 135°
    
    # Calculate GLCM
    glcm = graycomatrix(gray_reduced, 
                       distances=distances, 
                       angles=angles,
                       symmetric=True, 
                       normed=True, 
                       levels=gray_levels)
    
    # Extract texture features
    contrast = graycoprops(glcm, 'contrast')
    dissimilarity = graycoprops(glcm, 'dissimilarity')
    homogeneity = graycoprops(glcm, 'homogeneity')
    energy = graycoprops(glcm, 'energy')
    correlation = graycoprops(glcm, 'correlation')
    
    # Calculate mean values across all distances and angles
    # This provides more robust features
    data_glcm = {
        'contrast': float(np.mean(contrast)),
        'dissimilarity': float(np.mean(dissimilarity)),
        'homogeneity': float(np.mean(homogeneity)),
        'energy': float(np.mean(energy)),
        'correlation': float(np.mean(correlation)),
        # Additional texture measures
        'contrast_std': float(np.std(contrast)),
        'homogeneity_std': float(np.std(homogeneity)),
        'energy_std': float(np.std(energy))
    }

    return data_glcm

# fungsi untuk pemanggilan nilai fitur hsv
def HSV(image):
    """
    Improved HSV feature extraction for salt quality analysis
    """
    if len(image.shape) == 3 and image.shape[2] == 4:
        # Remove alpha channel if present
        image = image[:, :, :3]
    
    # Convert to HSV color space
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    hue, sat, val = cv.split(hsv)
    
    # Create mask to focus on salt grains (avoid pure white/black pixels)
    # This helps exclude background and focus on actual salt
    mask = cv.inRange(val, 30, 220)  # Exclude very dark and very bright pixels
    
    # Calculate statistics for masked regions
    if np.sum(mask) > 0:
        hue_values = hue[mask > 0]
        sat_values = sat[mask > 0]
        val_values = val[mask > 0]
    else:
        # Fallback to entire image if mask is empty
        hue_values = hue.flatten()
        sat_values = sat.flatten()
        val_values = val.flatten()
    
    # Calculate comprehensive statistics
    data_hsv = {
        'hue_mean': float(np.mean(hue_values)),
        'hue_std': float(np.std(hue_values)),
        'hue_median': float(np.median(hue_values)),
        'sat_mean': float(np.mean(sat_values)),
        'sat_std': float(np.std(sat_values)),
        'sat_median': float(np.median(sat_values)),
        'val_mean': float(np.mean(val_values)),
        'val_std': float(np.std(val_values)),
        'val_median': float(np.median(val_values)),
        # Additional color features
        'sat_range': float(np.max(sat_values) - np.min(sat_values)),
        'val_range': float(np.max(val_values) - np.min(val_values)),
        'brightness_uniformity': float(1.0 / (1.0 + np.std(val_values)))  # Higher for uniform brightness
    }

    return data_hsv


def RGB(image):
    """
    Improved RGB feature extraction for salt analysis
    """
    if len(image.shape) == 3 and image.shape[2] == 4:
        # Remove alpha channel if present
        image = image[:, :, :3]
    
    # Convert to RGB color space
    rgb = cv.cvtColor(image, cv.COLOR_BGR2RGB)
    red_channel = rgb[:, :, 0]
    green_channel = rgb[:, :, 1]
    blue_channel = rgb[:, :, 2]
    
    # Create mask to focus on salt grains
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    mask = cv.inRange(gray, 30, 220)
    
    # Calculate statistics for masked regions
    if np.sum(mask) > 0:
        red_values = red_channel[mask > 0]
        green_values = green_channel[mask > 0]
        blue_values = blue_channel[mask > 0]
    else:
        red_values = red_channel.flatten()
        green_values = green_channel.flatten()
        blue_values = blue_channel.flatten()
    
    # Calculate comprehensive RGB statistics
    data_rgb = {
        'red_mean': float(np.mean(red_values)),
        'red_std': float(np.std(red_values)),
        'red_median': float(np.median(red_values)),
        'green_mean': float(np.mean(green_values)),
        'green_std': float(np.std(green_values)),
        'green_median': float(np.median(green_values)),
        'blue_mean': float(np.mean(blue_values)),
        'blue_std': float(np.std(blue_values)),
        'blue_median': float(np.median(blue_values)),
        # Color ratios for salt quality assessment
        'rg_ratio': float(np.mean(red_values) / (np.mean(green_values) + 1e-6)),
        'rb_ratio': float(np.mean(red_values) / (np.mean(blue_values) + 1e-6)),
        'gb_ratio': float(np.mean(green_values) / (np.mean(blue_values) + 1e-6))
    }

    return data_rgb

def knn(data_uji, x, y, k):
    """
    Improved KNN implementation with confidence calculation
    """
    # Calculate Euclidean distance to all training samples
    jarak = []
    for i in range(len(x)):
        d = euclidean_distance(data_uji, x[i])
        jarak.append((d, y[i]))

    # Sort distances from smallest to largest
    jarak.sort()

    # Get k-nearest neighbors
    neighbors = jarak[:k]

    # Count class frequencies
    kelas_terbanyak = {}
    total_distance = 0
    for neighbor in neighbors:
        distance, class_label = neighbor
        total_distance += distance
        
        if class_label in kelas_terbanyak:
            kelas_terbanyak[class_label] += 1
        else:
            kelas_terbanyak[class_label] = 1

    # Get the most frequent class
    kelas_prediksi = max(kelas_terbanyak, key=kelas_terbanyak.get)

    # Calculate confidence metrics
    hasil_jarak = jarak[0][0]  # Distance to nearest neighbor
    confidence = kelas_terbanyak[kelas_prediksi] / k * 100
    
    # Additional confidence based on distance distribution
    avg_distance = total_distance / k
    distance_confidence = max(0, 100 - (avg_distance * 10))  # Adjust multiplier as needed
    
    # Combined confidence
    hasil_akurasi = (confidence + distance_confidence) / 2

    hasil_jarak = round(hasil_jarak, 4)
    hasil_akurasi = round(min(hasil_akurasi, 100), 2)  # Cap at 100%

    return kelas_prediksi, hasil_jarak, hasil_akurasi

# fungsi perhitungan jarak
def euclidean_distance(a, b):
    """
    Updated distance calculation for new feature set
    """
    # Basic HSV features
    d = ((a['hue_mean'] - b[0])**2 +
         (a['hue_std'] - b[1])**2 +
         (a['sat_mean'] - b[2])**2 +
         (a['sat_std'] - b[3])**2 +
         (a['val_mean'] - b[4])**2 +
         (a['val_std'] - b[5])**2 +
         # GLCM features
         (a['contrast'] - b[6])**2 +
         (a['dissimilarity'] - b[7])**2 +
         (a['homogeneity'] - b[8])**2 +
         (a['energy'] - b[9])**2 +
         (a['correlation'] - b[10])**2)
    
    # Add additional features if available
    if len(b) > 11:
        # Additional HSV features
        d += ((a.get('hue_median', 0) - b[11])**2 +
              (a.get('sat_median', 0) - b[12])**2 +
              (a.get('val_median', 0) - b[13])**2 +
              (a.get('brightness_uniformity', 0) - b[14])**2)
    
    return d**0.5

# fungsi untuk melakukan upload dataset
def runDataset(img):
    """
    Updated dataset processing function
    """
    try:
        # Run preprocessing
        result_preprocess = Preprocessing(img)
        nilai_glcm = GLCM(result_preprocess[1])
        nilai_hsv = HSV(result_preprocess[0])
        nilai_rgb = RGB(result_preprocess[0])

        result_dataset = {
            'nilai_hsv': nilai_hsv,
            'nilai_glcm': nilai_glcm,
            'nilai_rgb': nilai_rgb,
            'preprocessed_images': result_preprocess
        }

        return result_dataset
    
    except Exception as e:
        print(f"Error processing image {img}: {str(e)}")
        raise e


def runKlasifikasi(img, dataTrain):
    """
    Updated classification function with improved feature set
    """
    k = 5  # Increased k for better stability

    try:
        # Run preprocessing
        proses = Preprocessing(img)
        nilai_glcm = GLCM(proses[1])
        nilai_hsv = HSV(proses[0])

        # Prepare test data with core features
        data_uji = {
            'hue_mean': nilai_hsv['hue_mean'],
            'hue_std': nilai_hsv['hue_std'],
            'sat_mean': nilai_hsv['sat_mean'],
            'sat_std': nilai_hsv['sat_std'],
            'val_mean': nilai_hsv['val_mean'],
            'val_std': nilai_hsv['val_std'],
            'contrast': nilai_glcm['contrast'],
            'dissimilarity': nilai_glcm['dissimilarity'],
            'homogeneity': nilai_glcm['homogeneity'],
            'energy': nilai_glcm['energy'],
            'correlation': nilai_glcm['correlation'],
            'hue_median': nilai_hsv.get('hue_median', 0),
            'sat_median': nilai_hsv.get('sat_median', 0),
            'val_median': nilai_hsv.get('val_median', 0),
            'brightness_uniformity': nilai_hsv.get('brightness_uniformity', 0)
        }

        # Prepare training data
        x = []
        y = []
        for i in dataTrain:
            # Core features (ensure compatibility with existing database)
            features = [
                i['hue_mean'], i['hue_std'], i['sat_mean'], i['sat_std'], 
                i['val_mean'], i['val_std'], i['contrast'], i['dissimilarity'], 
                i['homogeneity'], i['energy'], i['correlation']
            ]
            
            # Add additional features if available
            features.extend([
                i.get('hue_median', 0),
                i.get('sat_median', 0), 
                i.get('val_median', 0),
                i.get('brightness_uniformity', 0)
            ])
            
            x.append(features)
            y.append(i['kelas'])

        # Run KNN classification
        kelas_prediksi, hasil_jarak, hasil_akurasi = knn(data_uji, x, y, k)

        # Prepare result data
        new_data = {
            'hue_mean': data_uji['hue_mean'],
            'hue_std': data_uji['hue_std'],
            'sat_mean': data_uji['sat_mean'],
            'sat_std': data_uji['sat_std'],
            'val_mean': data_uji['val_mean'],
            'val_std': data_uji['val_std'],
            'contrast': data_uji['contrast'],
            'dissimilarity': data_uji['dissimilarity'],
            'homogeneity': data_uji['homogeneity'],
            'energy': data_uji['energy'],
            'correlation': data_uji['correlation'],
            'kelas': kelas_prediksi,
            'jarak': hasil_jarak,
            'akurasi': hasil_akurasi,
            # Additional metadata
            # 'confidence_level': 'High' if hasil_akurasi > 80 else 'Medium' if hasil_akurasi > 60 else 'Low'
        }

        return new_data

    except Exception as e:
        print(f"Error in classification: {str(e)}")
        raise e