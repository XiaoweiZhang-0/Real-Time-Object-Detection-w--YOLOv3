* Author: Xiaowei Zhang
* Project description: YOLO (You Only Look Once) is a state-of-the-art, real-time object detection system that is popular for its speed and accuracy. This project focuses on implementing an object detector using the YOLOv3 architecture and the PyTorch deep learning framework and applying the detector to images and videos, including those from a webcam.
* Url to [report files](https://drive.google.com/drive/folders/1N6WW35kLKIbH9CwhPGWgbuD0UBcD9cSP?usp=share_linkhttps://drive.google.com/file/d/1cwULy_v2r9khjsWrX_s_JjWtLy7Se9SL/view?usp=share_li)
* Report files structure:

  * results folder contain the processed video files at different input image sizes [32, 64, 128, 256, 416, 512, 608, 640, 768, 896, 1024, 1280]
  * demo.mp4 is the demo presentation
  * model.png is the visualization of our model
  * original.MOV is our test video for hyperparameter tuning
  * Presentation.pptx is my presentation file
* Get the pretrained yolov3 weights uisng the command

  ```
  wget https://pjreddie.com/media/files/yolov3.weights
  ```
