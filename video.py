## Author: Xiaowei Zhang
## Date: 2023-04-17
## This file is to detect objects in a video or webcam
from __future__ import division
import time
import torch 
import torch.nn as nn
from torch.autograd import Variable
import numpy as np
import cv2 
from detector.util import *
import argparse
import os 
import os.path as osp
from detector.darknet import Darknet
import pickle as pkl
import pandas as pd
import random
from torchview import draw_graph
import matplotlib.pyplot as plt

def arg_parse():
    """
    Parse arguements to the detect module
    
    """
    
    parser = argparse.ArgumentParser(description='YOLO v3 Detection Module')
    parser.add_argument("--bs", dest = "bs", help = "Batch size", default = 1)
    parser.add_argument("--confidence", dest = "confidence", help = "Object Confidence to filter predictions", default = 0.5)
    parser.add_argument("--nms_thresh", dest = "nms_thresh", help = "NMS Threshhold", default = 0.4)
    parser.add_argument("--cfg", dest = 'cfgfile', help = 
                        "Config file",
                        default = "cfg/yolov3.cfg", type = str)
    parser.add_argument("--weights", dest = 'weightsfile', help = 
                        "weightsfile",
                        default = "yolov3.weights", type = str)
    parser.add_argument("--reso", dest = 'reso', help = 
                        "Input resolution of the network. Increase to increase accuracy. Decrease to increase speed",
                        default = "416", type = str)
    parser.add_argument("--video", dest = "videofile", help = "Video file to run detection on", default = "0", type = str)
    
    return parser.parse_args()
    
args = arg_parse()
batch_size = int(args.bs)
confidence = float(args.confidence)
nms_thesh = float(args.nms_thresh)
start = 0
CUDA = torch.cuda.is_available()



num_classes = 80
classes = load_classes("data/coco.names")



#Set up the neural network
print("Loading network.....")
model = Darknet(args.cfgfile)
model.load_weights(args.weightsfile)
print("Network successfully loaded")

model.net_info["height"] = args.reso
inp_dim = int(model.net_info["height"])
assert inp_dim % 32 == 0 
assert inp_dim > 32

#If there's a GPU availible, put the model on GPU
if CUDA:
    model.cuda()

#Set the model in evaluation mode
model.eval()


def write(x, results, colors):
    c1 = tuple((int((x[1:3][0].item())), int(x[1:3][1].item())))
    print(c1)
    c2 = tuple((int((x[3:5][0].item())), int(x[3:5][1].item())))
    img = results
    cls = int(x[-1])
    color = random.choice(colors)
    label = "{0}".format(classes[cls])
    cv2.rectangle(img, c1, c2,color, 1)
    t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_PLAIN, 1 , 1)[0]
    c2 = c1[0] + t_size[0] + 3, c1[1] + t_size[1] + 4
    cv2.rectangle(img, c1, c2,color, -1)
    cv2.putText(img, label, (c1[0], c1[1] + t_size[1] + 4), cv2.FONT_HERSHEY_PLAIN, 1, [225,255,255], 1)
    return img



# assert cap.isOpened(), 'Cannot capture source'
# inputSizes = [32, 64, 128, 256, 416, 512, 608, 640, 768, 896, 1024, 1280]
# inputSizes = [640]
# average_fps = []
# if os.path.exists('results'):
#     os.system('rm -rf results')
# os.mkdir('results')
## create a folder to save the resulting video
def detect(inp_dim):
    # model.net_info["height"] = inp_dim
    #Detection phase
    videofile = args.videofile #or path to the video file. 
    ## 0 for webcam and path to video file otherwise
    if(videofile == "0"):
        cap = cv2.VideoCapture(int(videofile))
    else:
        cap = cv2.VideoCapture(videofile)
    # print(cap.get(3), cap.get(4))
    # tuple = (int(cap.get(3)),int(cap.get(4)))
    # result = cv2.VideoWriter('results/result'+str(count)+'.mp4', 
    #                      fourcc=cv2.VideoWriter_fourcc(*'mp4v'),
    #                      fps=10, frameSize=tuple)      
    frames = 0  
    start = time.time()
    saveImage = False
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:   
            img = prep_image(frame, inp_dim)
            im_dim = frame.shape[1], frame.shape[0]
            im_dim = torch.FloatTensor(im_dim).repeat(1,2)   
                        
            if CUDA:
                im_dim = im_dim.cuda()
                img = img.cuda()
            
            with torch.no_grad():
                output = model(Variable(img), CUDA)
            output = write_results(output, confidence, num_classes, nms_conf = nms_thesh)
            
            ## save the model graph once
            if not saveImage:
                model_graph = draw_graph(model, input_size=img.size(), device='cpu', save_graph=True, CUDA = CUDA, filename='model_graph.png')
                saveImage = True


            if type(output) == int:
                frames += 1
                print("FPS of the video is {:5.4f}".format( frames / (time.time() - start)))
                cv2.imshow("frame", frame)
                key = cv2.waitKey(1)
                if key & 0xFF == ord('q'):
                    break
                continue
            
            
            

            im_dim = im_dim.repeat(output.size(0), 1)
            scaling_factor = torch.min(416/im_dim,1)[0].view(-1,1)
            
            output[:,[1,3]] -= (inp_dim - scaling_factor*im_dim[:,0].view(-1,1))/2
            output[:,[2,4]] -= (inp_dim - scaling_factor*im_dim[:,1].view(-1,1))/2
            
            output[:,1:5] /= scaling_factor

            for i in range(output.shape[0]):
                output[i, [1,3]] = torch.clamp(output[i, [1,3]], 0.0, im_dim[i,0])
                output[i, [2,4]] = torch.clamp(output[i, [2,4]], 0.0, im_dim[i,1])
        
            
            

            classes = load_classes('data/coco.names')
            colors = pkl.load(open("pallete", "rb"))

            list(map(lambda x: write(x, frame, colors), output))
            
            cv2.imshow("frame", frame)
            key = cv2.waitKey(1)
            if key & 0xFF == ord('q'):
                break
            frames += 1
            print(time.time() - start)
            print("FPS of the video is {:5.2f}".format( frames / (time.time() - start)))

            # fps.append(frames / (time.time() - start))
            # result.write(frame)
        else:
            break
  
# for i, inp_dim in enumerate(inputSizes):
#     fps = []
#     args.reso = inp_dim
#     detect(inp_dim, fps, i)
#     average_fps.append(np.mean(fps))
#     print('input size: ', inp_dim, 'fps: ', np.mean(fps))
## plot input size vs fps
# plt.plot(inputSizes, average_fps)
# plt.xlabel('input size')
# plt.ylabel('fps')
# plt.show()
# cv2.waitKey(0)
# plt.savefig('inputSize_vs_fps.png')
# plt.close()
detect(inp_dim)
  






