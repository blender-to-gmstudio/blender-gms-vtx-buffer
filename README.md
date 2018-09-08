# Blender to GameMaker:Studio Exporter
This exporter supports multiple materials and is meant for all kinds of models.
## Description / Planned features
* Generates one or more files with vertex buffer contents
* Optionally performs (destructive) preparation steps
* Generates an accompanying json file that describes all exported content
* Stuff to be supported: 
  * Customizable vertex format (Done)
  * Static scenery (Done)
  * Dynamic scenery (mesh data + offset per mesh/object in json file)
  * Nice-to-have: skeletons (i.e. armatures) => WIP
  * Morphs & per-frame stuff, including interpolation (Done)
  * Vertex formats per object
  * Extensive mapping of Blender data blocks to GameMaker functionality:
    * Scene => Room
    * Camera => Camera
    * Curve => Path
    * Speaker => Audio emitter
    * Render Layer => Layer
    * Mesh Object => Instance (of some kind of model object)
  * Top-down render of objects for easy viewing in a top-down 2D editor (using a left-handed coordinate system)
  * A clean way to invert axes for both objects and mesh data
## Installing the plugin in Blender
* In Blender, go to `File` > `User Preferences`
* Go to tab `Add-ons` and select `Install from File...`
* Navigate to the directory that contains the file `io_export_gms_vbx.py`
* Confirm
* Next tick the checkbox next to `Import-Export: Export GM:Studio Vertex Buffer`
* Click `Save User Settings`
* The plugin is now ready to be used
## Installing the presets
* Copy all the included .py files to the directory `%USERPROFILE%\AppData\Roaming\Blender Foundation\Blender\2.78\scripts\presets\operator\export_scene.gms_vbx\`
* Replace 2.78 by your Blender version if you're using a different version
## Usage
* Select one or more objects that you want to export
* Export using a custom defined format or using a format that comes with an export preset
* Load the vertex buffer in GM:Studio
### Static scenery
This preset can be used to export static scenery using a lightweight vertex format.

### Batched scenery
This preset can be used to export a batch of models where each vertex is tagged with an object index.
Each individual model can later be transformed using a matrix shader uniform.

### Morph animations
This preset can be used to export a full animation.
Each batch is a combination of the current frame and the next frame.
Position and normal values can be interpolated in the shader.
