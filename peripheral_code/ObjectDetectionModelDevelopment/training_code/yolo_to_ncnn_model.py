from ultralytics import YOLO

# Load the YOLO11 model
model = YOLO("../training_results/baseline_transfer_learning/train/weights/best.pt")

# Export the model to NCNN format
model.export(format="ncnn")  # creates '/yolo11n_ncnn_model'