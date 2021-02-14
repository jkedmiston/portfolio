Open notes on setting up this repository/application.

# To install `pkg-config`
* apt-get install -y pkg-config

# Realsense
## OpenCV linking
The list of opencv libraries which can be linked in is large. A list of libraries to try add in order is [here](https://stackoverflow.com/questions/9094941/compiling-opencv-in-c). For example, in that article is suggested the sequence: 
```
  -lopencv_core
  -lopencv_imgproc
  -lopencv_highgui
  -lopencv_imagecodecs
  -lopencv_ml
  -lopencv_video
  -lopencv_features2d
  -lopencv_calib3d
  -lopencv_objdetect
  -lopencv_contrib
  -lopencv_legacy
  -lopencv_flann
```