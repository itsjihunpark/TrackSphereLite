from ultralytics import YOLO

if __name__ == "__main__":

    model = YOLO("finetuned_best.pt")
    results = model.val(data="../assets/golfball_dataset_test.yaml", project="../training_results/baseline_from_coco_100_epoch_testing", device=[0])
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(results.box.map)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    model = YOLO( "scratch_best.pt")
    results = model.val(data="../assets/golfball_dataset_test.yaml",project="../training_results/baseline_from_scratch_100_epoch_testing", device=[0] )
    