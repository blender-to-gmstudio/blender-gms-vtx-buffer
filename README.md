# Blender to GameMaker:Studio Exporter
This exporter supports multiple materials and is meant for all kinds of models.
## Description / Planned features
* Generates one or more files with vertex buffer contents
* Optionally performs (destructive) preparation steps => As few as possible
* Generates an accompanying json file that describes all exported content
* Features: 
  * Customizable vertex format (Done)
  * Static scenery (Done)
  * Dynamic scenery (mesh data + offset per mesh/object in json file) (Done)
  * Morphs & per-frame stuff, including interpolation (Done)
  * Skeletons (i.e. armatures) => WIP
  * A clean way to invert axes for both objects and mesh data => Have a look into orientation_helper
  * Shape keys
  * line lists for particles, etc. ??

## Installing the plugin in Blender
* In Blender, go to `Edit` > `Preferences`
* Go to tab `Add-ons` and select `Install from File...`
* Select the zip file `io_export_gms_vertex_buffer.zip` and confirm
* Tick the checkbox next to `Import-Export: Export GameMaker:Studio Vertex Buffer`
* Click `Save User Settings`
* The plugin is now ready to be used

### Installing presets
Preset files are Python files (.py) that contain an operator preset's code.
These files need to placed in the right directory for the operator to detect them.
To install a new preset: 
* Navigate to `%USERPROFILE%\AppData\Roaming\Blender Foundation\Blender\2.82\scripts\presets\operator`
* Create a new directory with the name `export_scene.gms_vtx_buffer`. This is the bl_idname of the operator.
* Place the preset file in this directory

## Usage
### In Blender
* Select one or more objects that you want to export
* Export using an existing export preset or create your own configuration

### In GameMaker:Studio
* Load the file in a buffer
* Define the vertex format, either in the code editor or load it from the .json file
* Create a vertex buffer from the buffer using the created vertex format
* Create a shader with vertex attributes that correspond to the vertex format
* Draw the model using the shader

To export the vertex format, tick `Export Object Data`.
This generates an additional .json file which contains a description of the vertex format.
The format description can be found under the key `blmod/mesh_data/format`.

The add-on does not currently come with any code for GameMaker.
Many examples will be added to and explained in the wiki.

### Advanced
More info and examples can be found in the wiki: https://github.com/blender-to-gmstudio/blender-gms-vtx-buffer/wiki

## Creating vertex formats
TODO