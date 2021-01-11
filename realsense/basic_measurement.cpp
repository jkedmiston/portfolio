/*
Take a basic sample from an Intel Realsense D435, with setting custom configuration options for accuracy. 
- A-factor is covered here: https://dev.intelrealsense.com/docs/white-paper-subpixel-linearity-improvement-for-intel-realsense-depth-cameras
 */
#include <iostream>
#include <librealsense2/rs.hpp> // Include RealSense Cross Platform API
#include <opencv2/opencv.hpp>   // Include OpenCV API
#include <librealsense2/rs_advanced_mode.hpp> // Settings from JSON
#include <opencv2/imgcodecs.hpp>

// from cv-helpers
static cv::Mat frame_to_mat(const rs2::frame& f)
{
  // Convert rs2::frame to cv::Mat
  using namespace cv;
  using namespace rs2;
  
  auto vf = f.as<video_frame>();
  const int w = vf.get_width();
  const int h = vf.get_height();
  
  if (f.get_profile().format() == RS2_FORMAT_BGR8)
    {
      return Mat(Size(w, h), CV_8UC3, (void*)f.get_data(), Mat::AUTO_STEP);
    }
  else if (f.get_profile().format() == RS2_FORMAT_RGB8)
    {
      auto r_rgb = Mat(Size(w, h), CV_8UC3, (void*)f.get_data(), Mat::AUTO_STEP);
      cv::Mat r_bgr;
      cvtColor(r_rgb, r_bgr, COLOR_RGB2BGR);
      return r_bgr;
    }
  else if (f.get_profile().format() == RS2_FORMAT_Z16)
    {
      return Mat(Size(w, h), CV_16UC1, (void*)f.get_data(), Mat::AUTO_STEP);
    }
  else if (f.get_profile().format() == RS2_FORMAT_Y8)
    {
      return Mat(Size(w, h), CV_8UC1, (void*)f.get_data(), Mat::AUTO_STEP);
    }
  else if (f.get_profile().format() == RS2_FORMAT_DISPARITY32)
    {
      return Mat(Size(w, h), CV_32FC1, (void*)f.get_data(), Mat::AUTO_STEP);
    }
  
  throw std::runtime_error("Frame format is not supported yet!");
}

// Converts depth frame to a matrix of doubles with distances in meters
static cv::Mat depth_frame_to_meters( const rs2::depth_frame & f, std::string cvtype )
{
  cv::Mat dm = frame_to_mat(f);
  if(cvtype == "CV_64F"){
    dm.convertTo( dm, CV_64F );
  } else {
    dm.convertTo( dm, CV_32F );
  }
  dm = dm * f.get_units();
  return dm;
}

int main(int argc, char * argv[]) try
{
  rs2::context ctx;
  rs2::device_list connected_devices = ctx.query_devices();
  rs2::device active_device = connected_devices[0];

  auto advanced_mode_dev = active_device.as<rs400::advanced_mode>();
  std::string json_config = "{\"aux-param-autoexposure-setpoint\" : \"1536\",\"aux-param-colorcorrection1\" : \"0.298828\",\"aux-param-colorcorrection10\" : \"-0\",\"aux-param-colorcorrection11\" : \"-0\",\"aux-param-colorcorrection12\" : \"-0\",\"aux-param-colorcorrection2\" : \"0.293945\",\"aux-param-colorcorrection3\" : \"0.293945\",\"aux-param-colorcorrection4\" : \"0.114258\",\"aux-param-colorcorrection5\" : \"-0\",\"aux-param-colorcorrection6\" : \"-0\",\"aux-param-colorcorrection7\" : \"-0\",\"aux-param-colorcorrection8\" : \"-0\",\"aux-param-colorcorrection9\" : \"-0\",\"aux-param-depthclampmax\" : \"65536\",\"aux-param-depthclampmin\" : \"0\",\"aux-param-disparityshift\" : \"0\",\"controls-autoexposure-auto\" : \"True\",\"controls-autoexposure-manual\" : \"8500\",\"controls-color-autoexposure-auto\" : \"True\",\"controls-color-autoexposure-manual\" : \"166\",\"controls-color-backlight-compensation\" : \"0\",\"controls-color-brightness\" : \"0\",\"controls-color-contrast\" : \"50\",\"controls-color-gain\" : \"64\",\"controls-color-gamma\" : \"300\",\"controls-color-hue\" : \"0\",\"controls-color-power-line-frequency\" : \"3\",\"controls-color-saturation\" : \"64\",\"controls-color-sharpness\" : \"50\",\"controls-color-white-balance-auto\" : \"True\",\"controls-color-white-balance-manual\" : \"4600\",\"controls-depth-gain\" : \"16\",\"controls-laserpower\" : \"150\",\"controls-laserstate\" : \"on\",\"ignoreSAD\" : \"0\",\"param-amplitude-factor\" : \"0.18\",\"param-autoexposure-setpoint\" : \"1536\",\"param-censusenablereg-udiameter\" : \"9\",\"param-censusenablereg-vdiameter\" : \"9\",\"param-censususize\" : \"9\",\"param-censusvsize\" : \"9\",\"param-depthclampmax\" : \"65536\",\"param-depthclampmin\" : \"0\",\"param-depthunits\" : \"1000\",\"param-disableraucolor\" : \"0\",\"param-disablesadcolor\" : \"0\",\"param-disablesadnormalize\" : \"0\",\"param-disablesloleftcolor\" : \"0\",\"param-disableslorightcolor\" : \"0\",\"param-disparitymode\" : \"0\",\"param-disparityshift\" : \"0\",\"param-lambdaad\" : \"800\",\"param-lambdacensus\" : \"26\",\"param-leftrightthreshold\" : \"24\",\"param-maxscorethreshb\" : \"2047\",\"param-medianthreshold\" : \"500\",\"param-minscorethresha\" : \"1\",\"param-neighborthresh\" : \"7\",\"param-raumine\" : \"1\",\"param-rauminn\" : \"1\",\"param-rauminnssum\" : \"3\",\"param-raumins\" : \"1\",\"param-rauminw\" : \"1\",\"param-rauminwesum\" : \"3\",\"param-regioncolorthresholdb\" : \"0.0499022\",\"param-regioncolorthresholdg\" : \"0.0499022\",\"param-regioncolorthresholdr\" : \"0.0499022\",\"param-regionshrinku\" : \"3\",\"param-regionshrinkv\" : \"1\",\"param-robbinsmonrodecrement\" : \"10\",\"param-robbinsmonroincrement\" : \"10\",\"param-rsmdiffthreshold\" : \"4\",\"param-rsmrauslodiffthreshold\" : \"1\",\"param-rsmremovethreshold\" : \"0.375\",\"param-scanlineedgetaub\" : \"72\",\"param-scanlineedgetaug\" : \"72\",\"param-scanlineedgetaur\" : \"72\",\"param-scanlinep1\" : \"60\",\"param-scanlinep1onediscon\" : \"105\",\"param-scanlinep1twodiscon\" : \"70\",\"param-scanlinep2\" : \"342\",\"param-scanlinep2onediscon\" : \"190\",\"param-scanlinep2twodiscon\" : \"130\",\"param-secondpeakdelta\" : \"325\",\"param-texturecountthresh\" : \"0\",\"param-texturedifferencethresh\" : \"0\",\"param-usersm\" : \"1\",\"param-zunits\" : \"1000\",\"stream-depth-format\" : \"Z16\",\"stream-fps\" : \"30\",\"stream-height\" : \"480\",\"stream-width\" : \"848\"}";
  advanced_mode_dev.load_json(json_config);
  
  rs2::config cfg;
  cfg.enable_stream(RS2_STREAM_DEPTH, 848, 480, RS2_FORMAT_Z16, 0); // for intel D435
  
  // Declare RealSense pipeline, encapsulating the actual device and sensors
  rs2::pipeline pipe;
  // Start streaming with default recommended configuration
  pipe.start();
  
  int ct =0;
  std::string filename;
  rs2::colorizer color_map;
  
  {
    rs2::frameset data = pipe.wait_for_frames(); // Wait for next set of frames from the camera
    rs2::frame depth = data.get_depth_frame().apply_filter(color_map);
    const int w = depth.as<rs2::video_frame>().get_width();
    const int h = depth.as<rs2::video_frame>().get_height();
    cv::Mat image(cv::Size(w, h), CV_8UC3, (void*)depth.get_data(), cv::Mat::AUTO_STEP);
    
    
    rs2::depth_frame depth_base = data.get_depth_frame();
    cv::Mat depth_in_meters = depth_frame_to_meters(depth_base, "CV_64F");
    // https://stackoverflow.com/questions/7899108/opencv-get-pixel-channel-value-from-mat-image



    /* 
       Basic BGR save of cv image 
     */
    char cvbuff[100];
    sprintf(cvbuff, "depth%d.bmp", ct);
    std::string cvfilename = cvbuff;
    cv::imwrite(cvfilename, image);


    /*
      Save a raw map of the depth frame 
     */
    char buff[100];
    sprintf(buff, "depth%d.txt", ct);
    filename = buff;
    
    std::ofstream fout(filename);
    for(int i=0; i < depth_in_meters.rows; ++i){
      for(int j = 0; j < depth_in_meters.cols; ++j){
        fout << depth_in_meters.at<double>(i,j) << "\t";
      }
      fout << std::endl;
    }
    ct += 1;
  }
  printf("wrote %s\n", filename.c_str());
  return EXIT_SUCCESS;
 }
 catch (const rs2::error & e)
   {
     std::cerr << "RealSense error calling " << e.get_failed_function() << "(" << e.get_failed_args() << "):\n    " << e.what() << std::endl;
     return EXIT_FAILURE;
   }
 catch (const std::exception& e)
   {
     std::cerr << e.what() << std::endl;
     return EXIT_FAILURE;
   }



