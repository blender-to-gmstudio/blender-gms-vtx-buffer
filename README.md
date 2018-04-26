# Blender to GameMaker:Studio Vertex Buffer Exporter
This exporter supports multiple materials and is meant for all kinds of models.
## Description / Planned features
* Generates one or more files with vertex buffer contents
* Optionally performs (destructive) preparation steps
* Generates an accompanying json file that describes all exported content
* Stuff to be supported: 
  * Customizable vertex format (Done)
  * Static scenery (Done)
  * Dynamic scenery (mesh data + offset per mesh/object in json file)
  * Nice-to-have: skeletons
  * Morphs & per-frame stuff, including interpolation (Done)
## Installing the plugin in Blender

## Installing the presets
* Copy all the included .py files to the directory `%USERPROFILE%\AppData\Roaming\Blender Foundation\Blender\2.78\scripts\presets\operator\export_scene.gms_vbx\`
## Usage
* Select one or more object(s) that you want to export
* Export using a custom defined format or using a format that comes with an export preset
* Load the vertex buffer in GM:Studio
