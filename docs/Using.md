# Using brikWork
The birkWork command line app is currently the only way to use brikWork short of importing the engine from your own python application. In the future the engine will be usable from a vs code plugin or small Qt app, depending on interest

Currently the command line app is only tested on Windows, with Linux coming down the line

## Installation

Currently there is no proper install script, just unzip all the contents of the release folder into a useful place, like `Documents\brikWork`

## Usage

The basic usage is to pass the layout file to the app
```none
> birkWork.exe layout.bwl 
```
You can do this on the command line like above, drag and drop the layout file onto brikWork.exe, or right click a layout file, select "Open With...", and select brikWork.exe

## layout files

Layout files use the extension .bwl 