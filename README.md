# Blender to GameMaker:Studio Exporter
This exporter supports multiple materials and is meant for all kinds of models.
## Description / Planned features
* Generates one or more files with vertex buffer contents
* Optionally performs (destructive) preparation steps => As few as possible
* Generates an accompanying json file that describes all exported content
* Stuff to be supported: 
  * Customizable vertex format (Done)
  * Static scenery (Done)
  * Dynamic scenery (mesh data + offset per mesh/object in json file) (Done)
  * Nice-to-have: skeletons (i.e. armatures) => WIP
  * Morphs & per-frame stuff, including interpolation (Done)
  * Vertex formats per object => Won't add, one vertex format per export
  * Top-down render of objects for easy viewing in a top-down 2D editor (using a left-handed coordinate system) => Won't add, different plugin for this
  * A clean way to invert axes for both objects and mesh data
## Installing the plugin in Blender
* In Blender < 2.8, go to `File` > `User Preferences`
* Go to tab `Add-ons` and select `Install from File...`
* Navigate to the directory that contains the file `blender-gms-vbx.zip`
* Confirm
* Tick the checkbox next to `Import-Export: Export GameMaker:Studio Vertex Buffer`
* Click `Save User Settings`
* The plugin is now ready to be used
## Usage
### In Blender
* Select one or more objects that you want to export
* Export using an export preset or create your own configuration
### In GameMaker:Studio
* Load the file in a buffer
* Define the vertex format, either in the code editor or load it from the .json file
* Create a vertex buffer from the buffer using the created vertex format
* Create a shader with vertex attributes that correspond to the vertex format
* Draw the model using the shader
### Vertex formats
TODO