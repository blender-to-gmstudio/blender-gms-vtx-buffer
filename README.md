# Blender to GameMaker Vertex Buffer Exporter

This exporter can be used to export all kinds of vertex formats.

## Description

* Generates a file with vertex buffer contents
* Applies transforms & modifiers
* Generates an accompanying JSON file that describes all exported content
* Features: 
  * Customizable vertex format, allowing for: 
    * Static geometry batches
    * Dynamic geometry batches (mesh data + offset per mesh/object in json file)
    * Batched morphs
  * Morphs & per-frame stuff, including interpolation
  * Basic export of any material/shader properties

## Installing the plugin in Blender

* In Blender, go to `Edit` > `Preferences`
* Go to tab `Add-ons` and select `Install from File...`
* Select the zip file `blender-gms-vtx-buffer-v1.0.13.zip` and confirm (the filename will be different for another version of the exporter)
* Tick the checkbox next to `Import-Export: Export GameMaker Vertex Buffer`
* Click `Save User Settings`
* The plugin is now ready to be used

### Installing presets

Preset files are Python files (.py) that contain an operator preset's code.
These files need to placed in the right directory for the operator to detect them.
To install a new preset: 
* Navigate to `%USERPROFILE%\AppData\Roaming\Blender Foundation\Blender\2.82\scripts\presets\operator`
* Create a new directory with the name `export_scene.gms_vtx_buffer`. This is the bl_idname of the operator.
* Place the preset file in this directory
The included presets can be installed from the add-on's preferences

## Usage
### In Blender

* Select one or more objects that you want to export
* Export using an existing export preset or create your own configuration

### In GameMaker

* Load the file as a buffer using [buffer_load](https://manual.gamemaker.io/monthly/en/GameMaker_Language/GML_Reference/Buffers/buffer_load.htm).
* Define the vertex format, either in the code editor or load it from the JON file.
* Create a vertex buffer from the buffer using the created vertex format.
* Create a shader with vertex attributes that correspond to the vertex format.
* Draw the model using the shader.

To export the vertex format, tick `Export Object Data`.
This generates an additional .json file which contains a description of the vertex format.
The format description can be found under the key `blmod/mesh_data/format`.

The add-on does not currently come with any code for GameMaker.
Many examples will be added to and explained in the wiki.

### Advanced

More info and examples can be found in the wiki: https://github.com/blender-to-gmstudio/blender-gms-vtx-buffer/wiki

## Creating vertex formats

See the wiki on [defining vertex formats](https://github.com/blender-to-gmstudio/blender-gms-vtx-buffer/wiki/Exporting-Models#defining-vertex-formats).
