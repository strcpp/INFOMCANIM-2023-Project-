![Alt Text](https://s12.gifyu.com/images/SWzCy.gif)

## About

A skeletal animation system built for the [UU Computer Animation course.](https://www.cs.uu.nl/docs/vakken/mcanim/)

[Click here for video presentation](https://www.youtube.com/watch?v=6Ezdmw6TeRs&ab_channel=ZerrinYumak)

Collaborated with a team of wonderful of individuals (who possess the talent to perform the Macarena).😊
## Features

* GLTF model/animation loading
* Multiple model scene
* Animation playback settings (speed, forward/backward, frame selection, play/stop)
* Skeletal animation via bone visualization
* Skinning via Linear Blend Skinning
* Custom animations captured at [UU motion capture lab](https://www.uu.nl/en/research/motion-capture-and-virtual-reality-lab)
* Multiple interpolation methods (Linear/hermite)
* A soundtrack player (for fun)
* Custom renderer built on moderngl (small opengl abstraction):
    * Model rendering
    * Skybox
    * Grid (with fog)
    * Line drawing for skeletons (variable thickness)
    * Simple phong shading
    * UI via IMGUI
* Utilizes the powerful [Numba](https://numba.pydata.org/) to speed things up

## Installation

### Linux/MacOS
```sh
pip install -r requirements.txt
```
### Windows
```sh
python -m pip install -r requirements.txt
```

## Run
```sh
python src/main.py
```
