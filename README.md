# 🚀 YouTube View Predictor: A Multimodal Machine Learning Approach

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Machine%20Learning-orange)
![XGBoost](https://img.shields.io/badge/Model-XGBoost-green)
![Status](https://img.shields.io/badge/Status-Completed-success)

## 📌 Project Overview
This project is a Machine Learning pipeline designed to predict the view counts of YouTube videos. Instead of relying solely on basic metadata, this project takes a **multimodal approach** by combining YouTube API data (titles, tags, duration) with visual features extracted from video thumbnails (dominant colors, brightness, saturation). 

The goal is to understand what makes a video successful and build a robust model that handles the highly skewed nature of YouTube viewership (Power Law distribution).

## ✨ Key Features
* **API Integration:** Automated data extraction using the YouTube Data API v3.
* **Computer Vision / Image Processing:** Extraction of RGB color values and brightness levels directly from thumbnail URLs.
* **Advanced Feature Engineering:** Creation of new predictive features such as `title_length`, `days_since_upload`, and `link_count`.
* **Robust Data Preprocessing:** Applied **Box-Cox (Yeo-Johnson)** transformations to handle extreme outliers and normalize highly skewed data.

## 🧠 Methodology & Data Pipeline

Our workflow consists of 4 main steps:

1. **Raw Data Collection:** Fetched raw video metadata (titles, views, dates, thumbnails) using the YouTube API and saved it as a CSV file.
2. **Thumbnail Analysis:** Processed thumbnail images using a custom script to extract visual features (Colors, Saturation, Brightness) and saved them as a secondary dataset.
3. **Feature Engineering & Merging:** Combined API data with thumbnail data. Cleaned missing values and created calculated features.
4. **Model Training:** Trained and evaluated advanced gradient boosting models to predict the target variable (`views`).

## 📊 Feature Scaling & Transformation Strategy
YouTube view counts and follower metrics follow a heavy Power Law distribution (a few videos get millions of views, while most get very few). 

To solve this, we implemented a sophisticated scaling strategy:
* **Power Transformation (Yeo-Johnson):** Standard scalers (like MinMax) failed due to extreme outliers, squeezing normal data into a tiny range. We used the Yeo-Johnson method (an advanced Box-Cox transformation) to stabilize variance and force the features into a **Normal Distribution (Gaussian)**.
* **Normalization:** After fixing the distribution, we applied Min-Max Normalization to bring all numeric features to a standardized scale (0-1).
* **Inverse Transformation:** During evaluation, predictions were inverse-transformed to calculate the actual Mean Absolute Error (MAE) in real-world view counts.

## ⚙️ Models Used
* **XGBoost (Extreme Gradient Boosting)**
* **HistGradientBoostingRegressor**

## 📂 Repository Structure
```text
├── data/
│   ├── raw_youtube_data.csv       # Data fetched from API
│   ├── thumbnail_features.csv     # Extracted image data
│   └── final_merged_data.csv      # Ready for modeling
├── notebooks/
│   ├── 1_data_collection.ipynb
│   ├── 2_thumbnail_processing.ipynb
│   └── 3_modeling_and_scaling.ipynb
├── src/
│   └── (python scripts if any)
├── README.md
└── requirements.txt
