# Scripts for Faster R-CNN 

These scripts should be placed into the faster-rcnn.pytorch folders using the same structure of folders.

## Installing [Faster-RCNN.pytorch](https://github.com/jwyang/faster-rcnn.pytorch)

First, we create a Conda environment for faster-rcnn.pytorch using:

```
$ conda create -n faster-rcnn.pytorch python=2.7
$ conda activate faster-rcnn.pytorch
$ conda install torchvision pytorch=0.4.0 cuda80 -c pytorch
```

Next, we clone the git repository and install dependencies.

```
$ git clone https://github.com/jwyang/faster-rcnn.pytorch.git
$ pip install cython cffi opencv-python scipy msgpack easydict matplotlib pyyaml tensorboardX lxml
$ export FRCN_ROOT=<folder_of_faster-rcnn.pytorch>
```

After, we compile libraries in `lib` folder. Before compiling, we have to check our GPUs in order to compile with support to them. In our case (2 GPUs NVIDIA K40 and 1 GPU NVIDIA Titan X), we edit the `make.sh` file adding the compilation for `sm_30` and `sm_35` (K40) and `sm_52` (Titan X), as presented below:

```
#sm_52 to Titan Xp and sm_3* to K40
CUDA_ARCH="-gencode arch=compute_52,code=sm_52 \
           -gencode arch=compute_30,code=sm_30 \
           -gencode arch=compute_35,code=sm_35"
```

Then, we compile using:

```
$ cd $FRCN_ROOT/lib
$ sh make.sh
```

## Training-Testing Faster-RCNN.pytorch

In order to test Faster-RCNN.pytorch, we can use the `VOC2007` dataset. To test with it, first, we download it in a folder `$ROOT_DATA/data`, where `$ROOT_DATA` is the folder that we further link to our `data` folder inside the `faster-rcnn.pytorch` folder. Here, we consider `ROOT_DATA=/usr/share/datasets/Roger/faster-rcnn.pytorch`. We run:

```
$ cd $ROOT_DATA
$ mkdir data/
$ cd data/

$ wget http://host.robots.ox.ac.uk/pascal/VOC/voc2007/VOCtrainval_06-Nov-2007.tar
$ wget http://host.robots.ox.ac.uk/pascal/VOC/voc2007/VOCtest_06-Nov-2007.tar
$ wget http://host.robots.ox.ac.uk/pascal/VOC/voc2007/VOCdevkit_08-Jun-2007.tar

$ tar xvf VOCtrainval_06-Nov-2007.tar
$ tar xvf VOCtest_06-Nov-2007.tar
$ tar xvf VOCdevkit_08-Jun-2007.tar
```

Create symlinks for the PASCAL VOC dataset using:

```
$ cd $FRCN_ROOT
$ mkdir data
$ cd data
$ ln -s $ROOT_DATA/VOCdevkit2007 VOCdevkit2007
```

Now, we can download the pre-trained models with:

```
$ cd $ROOT_DATA/data
$ mkdir pretrained_model
$ wget https://www.dropbox.com/s/iev3tkbz5wyyuz9/resnet101_caffe.pth?dl=0
$ wget https://www.dropbox.com/s/s3brpk0bdq60nyb/vgg16_caffe.pth?dl=0
$ $FRCN_ROOT/data
$ ln -s $ROOT_DATA/data/pretrained_model pretrained_model
```

With all data downloaded, we can train a model using the PASCAL VOC dataset using the command:

```
$ CUDA_VISIBLE_DEVICES=0 python trainval_net.py --dataset pascal_voc --net vgg16 --bs 4 --nw 1 --lr 0.01 --lr_decay_step 5 --cuda
```

Having our model trained, (e.g., `models/vgg16/pascal_voc/faster_rcnn_1_3_196452.pth`), we can test it using:

```
$ CUDA_VISIBLE_DEVICES=0 python test_net.py --dataset pascal_voc --net vgg16 --checksession 1 --checkepoch 3 --checkpoint 196452 --cuda
```


## Demo using images

Instead of testing the network to check their accuracy, we can perform a demo, testing files from folder `images` and generating images in the same folder with the termination `_det.jpg`. To do so, we can run for the model trained before:

```
$ CUDA_VISIBLE_DEVICES=0 python demo.py --net vgg16  --checksession 1 --checkepoch 3 --checkpoint 196452 --cuda --load_dir models/
```

