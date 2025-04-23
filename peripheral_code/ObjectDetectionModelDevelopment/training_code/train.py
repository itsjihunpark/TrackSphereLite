from ultralytics import YOLO

if __name__ == "__main__":
    # Load a model
    # model = YOLO("../assets/yolo11n.pt")  # load a pretrained model (recommended for training)
    model = YOLO("yolo11n.yaml")
                
    # Train the model with 2 GPUs
    results = model.train(data="../assets/golfball_dataset.yaml", epochs=200, imgsz=640, device=[0], project="../training_results/baseline_from_scratch_200_epoch")
    
    # tensorboard --logdir C:\Users\Jihun\Documents\prj_TrackSphereLite\object_detection\training_results\{name of train folder} (e.g., baseline_from_scratch_100_epoch or baseline_transfer_learning_100_epoch or baseline_transfer_learning_200_epoch)