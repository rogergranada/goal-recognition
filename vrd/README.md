# Installing and configuring Visual Relationship Detection with Deep Structural Ranking (VRD-DSR)

These steps install `VRD-DSR <https://github.com/GriffinLiang/vrd-dsr>`_ on the server. The server must have GPU and CUDA.


# Creating `vrd-dsr` Environment

First, we create a conda environment to keep libraries separated from the rest of the Python. Before cloning the repository, we also have to install its dependences. The main dependences are `cython`, `opencv`, `pytorch==0.2.0` and `tabulate`. In order to create the environment and install the dependences, run:

```
$ conda create -n vrd-dsr python=2.7
$ conda activate vrd-dsr
$ conda install -n vrd-dsr torchvision pytorch==0.3.1 -c pytorch
$ pip install cython
$ pip install opencv-python
```

After creating the environment, we can set the environment variables:

```
# Cuda
export CUDA_HOME=/usr/local/cuda-9.0
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
export PATH=$CUDA_HOME/bin:$PATH
#export DYLD_LYBRARY_PATH=$CUDA_HOME/lib:$DYLD_LIBRARY_PATH
export DNCCL_ROOT_DIR=$CUDA_HOME

# Anaconda
. /opt/anaconda2/etc/profile.d/conda.sh
conda activate vrd-dsr
export ANACONDA_HOME=/home/roger/.conda/envs/vrd-dsr

# Environment
export ROOT_DATA=/usr/share/datasets/Roger/vrd-dsr
export TOOL_ROOT=/home/roger/Workspace/vrd-dsr
```

# Cloning VRD-DSR and Compiling Faster R-CNN Module

In order to install all libraries, we have to clone the git repositories of the application and its dependency (Faster R-CNN). To do so, we run:

```
$ git clone https://github.com/GriffinLiang/vrd-dsr.git
$ cd vrd-dsr/
$ git clone https://github.com/GriffinLiang/faster-rcnn.pytorch.git
$ cd faster-rcnn.pytorch/
$ git checkout 773184a606
```

With repositories cloned, we can compile ROI pooling from `lib` folder using:

```
$ cd $TOOL_ROOT/lib
$ chmod +x make.sh
$ ./make.sh

$ cd $TOOL_ROOT/faster-rcnn.pytorch/lib
$ ./make.sh
```

