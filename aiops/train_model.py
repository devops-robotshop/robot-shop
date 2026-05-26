"""
AIOps Random Forest Training — Strict No-Leakage Version
=========================================================
Quy trình đúng:
  1. Load tất cả CSV raw (hỗ trợ nhiều file)
  2. SPLIT thành Train / Val / Test TRƯỚC
  3. Chỉ AUGMENT tập Train
  4. Train → Validate → Test
  5. Xuất model + plots với tên có timestamp (không bao giờ ghi đè file cũ)
"""
 
import pandas as pd
import numpy as np
import glob
import os
import json
from datetime import datetime
 
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report, accuracy_score, confusion_matrix,
    precision_score, recall_score, f1_score,
)
from imblearn.over_sampling import SMOTE
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")
 
# ==========================================
# CẤU HÌNH
# ==========================================
TARGET_PER_CLASS = 1000      # Số mẫu mỗi nhãn sau SMOTE
NOISE_LEVEL      = 0.01      # Độ nhiễu Gaussian
TEST_VAL_RATIO   = 0.4       # 40% tách ra → chia đôi → 20% val + 20% test
RF_ESTIMATORS    = 150       # Tăng lên 150 cây (dataset có 11 features)
RF_MAX_DEPTH     = 15
RANDOM_STATE     = 42
 
 
# ==========================================
# TÊN FILE OUTPUT — GẮN TIMESTAMP
# ==========================================
RUN_TS = datetime.now().strftime("%Y%m%d_%H%M%S")
 
def out(name: str) -> str:
    """Tạo đường dẫn output với timestamp, không bao giờ trùng tên."""
    base, ext = os.path.splitext(name)
    return f"{base}_{RUN_TS}{ext}"
 
 
# ==========================================
# LOAD DATA — HỖ TRỢ NHIỀU FILE CSV
# ==========================================
def load_data(pattern: str = "data/dataset_label*.csv") -> pd.DataFrame:
    files = sorted(glob.glob(pattern))
    if not files:
        # fallback: tìm file tổng hợp
        fallback = "data/dataset_final.csv"
        if os.path.exists(fallback):
            files = [fallback]
        else:
            raise FileNotFoundError(
                f"Không tìm thấy file nào khớp với '{pattern}' hoặc '{fallback}'.\n"
                "Hãy đặt các file CSV vào cùng thư mục với script này."
            )
 
    print(f"[Load] Tìm thấy {len(files)} file:")
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        print(f"       {f}  →  {len(df)} dòng")
        dfs.append(df)
 
    combined = pd.concat(dfs, ignore_index=True)
    print(f"[Load] Tổng cộng: {len(combined)} dòng\n")
    return combined
 
 
# ==========================================
# TIỀN XỬ LÝ
# ==========================================
def preprocess(df: pd.DataFrame):
    df = df.fillna(0)
 
    DROP_COLS = ["timestamp", "label"]
    feature_cols = [c for c in df.columns if c not in DROP_COLS]
    X = df[feature_cols].copy()
    y = df["label"].astype(int)
 
    print(f"[Preprocess] Features ({len(feature_cols)}): {feature_cols}")
    print(f"[Preprocess] Phân phối nhãn:\n{y.value_counts().sort_index().to_string()}\n")
    return X, y, feature_cols
 
 
# ==========================================
# DATA AUGMENTATION — CHỈ DÙNG CHO TRAIN
# ==========================================
def augment_train(X_train, y_train, target=TARGET_PER_CLASS, noise=NOISE_LEVEL):
    counts = pd.Series(y_train).value_counts()
    print(f"[Augment] Tập Train gốc: {dict(counts.sort_index())}")
 
    # k_neighbors phải < min(class_count) - 1
    min_count = counts.min()
    k = max(1, min(5, min_count - 1))
    strategy = {cls: target for cls in counts.index}
 
    try:
        smote = SMOTE(sampling_strategy=strategy, k_neighbors=k, random_state=RANDOM_STATE)
        X_s, y_s = smote.fit_resample(X_train, y_train)
    except ValueError as e:
        print(f"[Augment] SMOTE lỗi ({e}), thử k=1...")
        smote = SMOTE(sampling_strategy=strategy, k_neighbors=1, random_state=RANDOM_STATE)
        X_s, y_s = smote.fit_resample(X_train, y_train)
 
    # Gaussian noise — giả lập dao động thực tế của sensor
    rng = np.random.RandomState(RANDOM_STATE)
    X_noisy = X_s + X_s * rng.normal(0, noise, X_s.shape)
 
    print(f"[Augment] Sau SMOTE+Noise: {dict(pd.Series(y_s).value_counts().sort_index())}")
    print(f"[Augment] Shape cuối: {X_noisy.shape}\n")
    return X_noisy, y_s
 
 
# ==========================================
# TRAIN
# ==========================================
def train(X_train_aug, y_train_aug):
    print("[Train] Huấn luyện Random Forest...")
    model = RandomForestClassifier(
        n_estimators=RF_ESTIMATORS,
        max_depth=RF_MAX_DEPTH,
        min_samples_leaf=2,       # chống overfit trên từng lá
        class_weight="balanced",  # đảm bảo công bằng giữa 3 nhãn
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train_aug, y_train_aug)
    print("[Train] Hoàn tất!\n")
    return model
 
 
# ==========================================
# ĐÁNH GIÁ
# ==========================================
def evaluate(model, X, y, split_name: str):
    y_pred = model.predict(X)
    acc = accuracy_score(y, y_pred)
    prec = precision_score(y, y_pred, average="weighted", zero_division=0)
    rec  = recall_score(y, y_pred, average="weighted", zero_division=0)
    f1   = f1_score(y, y_pred, average="weighted", zero_division=0)
 
    print(f"[{split_name}] Accuracy={acc:.4f}  Precision={prec:.4f}  Recall={rec:.4f}  F1={f1:.4f}")
    return {"split": split_name, "accuracy": acc, "precision": prec, "recall": rec, "f1": f1,
            "y_true": y.tolist(), "y_pred": y_pred.tolist()}
 
 
# ==========================================
# CROSS VALIDATION TRÊN TẬP TRAIN RAW
# ==========================================
def cross_validate(X_train_raw, y_train_raw):
    print("[CV] Chạy 5-fold Stratified CV trên tập train gốc (không augment)...")
    # Dùng model nhẹ hơn để CV nhanh
    cv_model = RandomForestClassifier(
        n_estimators=100, max_depth=15, random_state=RANDOM_STATE, n_jobs=-1
    )
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(cv_model, X_train_raw, y_train_raw, cv=skf, scoring="f1_weighted")
    print(f"[CV] F1 scores: {[round(s, 4) for s in scores]}")
    print(f"[CV] Mean F1 = {scores.mean():.4f}  ±  {scores.std():.4f}\n")
    return scores
 
 
# ==========================================
# VẼ CONFUSION MATRIX
# ==========================================
def plot_confusion(y_true, y_pred, title: str, filename: str):
    cm = confusion_matrix(y_true, y_pred)
    labels = ["Normal (0)", "Spike (1)", "Error (2)"]
    plt.figure(figsize=(7, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=labels, yticklabels=labels)
    plt.title(title)
    plt.xlabel("AI Dự Đoán")
    plt.ylabel("Thực Tế")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"[Plot] Confusion matrix → {filename}")
 
 
# ==========================================
# VẼ FEATURE IMPORTANCE
# ==========================================
def plot_feature_importance(model, feature_cols: list, filename: str):
    imp = pd.Series(model.feature_importances_, index=feature_cols).sort_values()
    colors = ["#1D9E75" if v > imp.median() else "#888780" for v in imp]
 
    plt.figure(figsize=(8, max(4, len(feature_cols) * 0.45)))
    bars = plt.barh(imp.index, imp.values, color=colors, edgecolor="none")
    plt.xlabel("Importance")
    plt.title("Feature Importance — Random Forest")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"[Plot] Feature importance → {filename}")
 
 
# ==========================================
# MAIN
# ==========================================
def main():
    print("=" * 60)
    print("  AIOps RF Training  —  Strict No-Leakage Pipeline")
    print(f"  Run timestamp: {RUN_TS}")
    print("=" * 60 + "\n")
 
    # 1. Load
    df = load_data()
 
    # 2. Preprocess
    X, y, feature_cols = preprocess(df)
 
    # 3. SPLIT TRƯỚC — tập val & test là data THẬT, không augment
    X_train_raw, X_temp, y_train_raw, y_temp = train_test_split(
        X, y, test_size=TEST_VAL_RATIO, random_state=RANDOM_STATE, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=RANDOM_STATE, stratify=y_temp
    )
 
    n = len(y)
    print("[Split] Phân chia dữ liệu (data THẬT — trước augment):")
    print(f"  Train raw : {len(y_train_raw):4d} mẫu ({len(y_train_raw)/n*100:.0f}%)")
    print(f"  Val   raw : {len(y_val):4d} mẫu ({len(y_val)/n*100:.0f}%)")
    print(f"  Test  raw : {len(y_test):4d} mẫu ({len(y_test)/n*100:.0f}%)\n")
 
    # 4. Cross-validation trước khi augment
    cv_scores = cross_validate(X_train_raw, y_train_raw)
 
    # 5. AUGMENT — chỉ tập train
    X_train_aug, y_train_aug = augment_train(X_train_raw, y_train_raw)
 
    # 6. Train
    model = train(X_train_aug, y_train_aug)
 
    # 7. Đánh giá
    print("\n" + "-" * 60)
    print("KẾT QUẢ ĐÁNH GIÁ")
    print("-" * 60)
    val_metrics  = evaluate(model, X_val,  y_val,  "Validation (real)")
    test_metrics = evaluate(model, X_test, y_test, "Test       (real)")
 
    print("\n[Test] Classification Report chi tiết:")
    print(classification_report(test_metrics["y_true"], test_metrics["y_pred"],
                                target_names=["Normal", "Spike", "Error"], zero_division=0))
 
    # 8. Lưu model — TÊN CÓ TIMESTAMP
    model_file = out("rf_model.pkl")
    joblib.dump(model, model_file)
    print(f"[Save] Model → {model_file}")
 
    # 9. Lưu metrics JSON
    metrics_file = out("metrics_report.json")
    report = {
        "run_timestamp": RUN_TS,
        "dataset_size": len(y),
        "features": feature_cols,
        "n_features": len(feature_cols),
        "cv_f1_mean": round(float(cv_scores.mean()), 4),
        "cv_f1_std":  round(float(cv_scores.std()), 4),
        "validation": {k: round(v, 4) if isinstance(v, float) else v
                       for k, v in val_metrics.items() if k not in ("y_true", "y_pred")},
        "test":       {k: round(v, 4) if isinstance(v, float) else v
                       for k, v in test_metrics.items() if k not in ("y_true", "y_pred")},
    }
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[Save] Metrics JSON → {metrics_file}")
 
    # 10. Plots — TÊN CÓ TIMESTAMP
    plot_confusion(
        test_metrics["y_true"], test_metrics["y_pred"],
        title=f"Confusion Matrix — Real Test Set  ({RUN_TS})",
        filename=out("confusion_matrix.png"),
    )
    plot_feature_importance(model, feature_cols, filename=out("feature_importance.png"))
 
    print("\n" + "=" * 60)
    print("  TỔNG KẾT")
    print("=" * 60)
    print(f"  CV F1 (train raw)   : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"  Validation Accuracy : {val_metrics['accuracy']:.4f}")
    print(f"  Test Accuracy       : {test_metrics['accuracy']:.4f}")
    print(f"  Test F1-Score       : {test_metrics['f1']:.4f}")
    print(f"\n  Files được tạo (timestamp={RUN_TS}):")
    print(f"    {model_file}")
    print(f"    {metrics_file}")
    print(f"    {out('confusion_matrix.png')}")
    print(f"    {out('feature_importance.png')}")
    print("=" * 60)
 
 
if __name__ == "__main__":
    main()