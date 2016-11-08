"""
This component will sort files by their component and output node, this is useful for gathering all the images of a study in one folder to make a video

If you re-compute the computer and a file is taken away at this stage you need to delete empty folders or directories manually 

Created by Anton Szilasi - contact him for user requests or bug reports
-
Provided by Ladybug 0.0.63
    
    Args:
        inputFiles_: Connect all the file path inputs that you would like to be sorted
        _moveToFolder: Name a root directory where you would like all the sorted files to be placed
    Returns:
        fileLocations: ...
"""

ghenv.Component.Name = "Sort files by output and component"
ghenv.Component.NickName = 'Sort files by out and component'

import os
import Grasshopper
import Grasshopper.Kernel as gh
import ctypes.wintypes
import shutil

class myDictSet(dict):

    def __init__(self):
        self = dict()
    
    def add(self, key, value):
        
        if key in self.keys():
            
            self[key].add(value)
        
        else:
            # Create key
            self[key] = set()
            self[key].add(value)
            

class AutoVivification(dict):
    #Implementation of perl's autovivification feature
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value
            
def myprint(d):
  for k, v in d.iteritems():
    if isinstance(v, dict):
      myprint(v)
    else:
      print "{0} : {1}".format(k, v)
      
      
CSIDL_PERSONAL= inputFiles_  # My Documents
SHGFP_TYPE_CURRENT= 0   # Want current, not default value

buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)

ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0, SHGFP_TYPE_CURRENT, buf)

checkDuplicateComponents = myDictSet()

filePaths = AutoVivification()

for input in ghenv.Component.Params.Input:
    
    # Get the connected component of the output
    for source in input.Sources:

        attr = source.Attributes
        if (attr is None) or (attr.GetTopLevel is None):
            pass
            
        else:
            component = attr.GetTopLevel.DocObject
            
            # Check that there are not two components of the same type! 
            
            checkDuplicateComponents.add(component.ComponentGuid,component.InstanceGuid)
            
            if len(checkDuplicateComponents.get(component.ComponentGuid)) > 1:
                
                warning = "You cannot connect two components of the same type to this component!"
                print warning
                ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Error, warning)
                
                break 
                
            else:
                
                filePaths[component.Name][source.NickName] = source.VolatileData[0][0]
                
                
userName = os.getenv('USERNAME')

# Make main diva output component

if _moveToFolder != None:

    try:
        outputfolder = _moveToFolder+'\\Desktop\\divaOutputs'
        os.mkdir('C:\\Users\\'+str(userName)+'\\Desktop\\divaOutputs')
        
    except OSError:
        
        pass
        
else:
    
    try:
        outputfolder = 'C:\\Users\\'+str(userName)+'\\Desktop\\divaOutputs'
        os.mkdir('C:\\Users\\'+str(userName)+'\\Desktop\\divaOutputs')
        
    except OSError:
        
        pass

# Make folders for each output on each component and move the respective files into those components
for componentNames,values in filePaths.iteritems():
    
    # Make component folders within main output component
    
    try:
        os.mkdir(outputfolder+'\\'+componentNames)
        
        # File the folders 
    except OSError:
        pass

    for componentOutputName,componentOutput in values.iteritems():
        
        # New component out directory
        
        newDir = outputfolder+'\\'+componentNames+'\\'+componentOutputName
        
        try:
            
            os.mkdir(newDir)
            
            # File the folders 
        except OSError:
            pass
            
        # Move the files
        shutil.copy(str(componentOutput),newDir)
           