# CodeDog Program Maker

import progSpec
import codeDogParser
import buildDog

import pattern_Write_Main
import pattern_GUI_Toolkit
#import pattern_Gen_GUI

import stringStructs

##########  Library Shells
import Lib_GTK3
import Lib_Java
import Lib_CPP
import Lib_Swing
import Lib_Android
#import Lib_AndroidGUI

import CodeGenerator
import xlator_CPP
import xlator_Java
#import xlator_JavaScript
#import xlator_Swift


import re
import os
import sys
import errno
import platform
import copy

'''
def writeFile(path, fileName, outStr, fileExtension):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST: raise
    fileName += fileExtension
    fo=open(path + os.sep + fileName, 'w')
    fo.write(outStr)
    fo.close()
    '''

def stringFromFile(filename):
    f=open(filename)
    Str = f.read()
    f.close()
    return Str

def processIncludedFiles(fileString):
    pattern = re.compile(r'#include +([\w -\.\/\\]+)')
    return pattern.sub(replaceFileName, fileString)

def replaceFileName(fileMatch):
    includedStr = stringFromFile(fileMatch.group(1))
    includedStr = processIncludedFiles(includedStr)
    return includedStr


def ScanAndApplyPatterns(objects, tags):
    print "    Applying Patterns..."
    for item in objects[1]:
        if item[0]=='!':
            pattName=item[1:]
            patternArgs=objects[0][pattName]['parameters']
            print "        PATTERN:", pattName, ':', patternArgs

            if pattName=='Write_Main': pattern_Write_Main.apply(objects, tags, patternArgs[0])
            elif pattName=='Gen_EventHandler': pattern_Gen_EventHandler.apply(objects, tags, patternArgs[0])
            #elif pattName=='writeParser': pattern_Gen_ParsePrint.apply(objects, tags, patternArgs[0], patternArgs[1])
            elif pattName=='useBigNums': pattern_BigNums.apply(tags)
            elif pattName=='makeGUI': pattern_GUI_Toolkit.apply(objects, tags)
            else:
                print "\nPattern", pattName, "not recognized.\n\n"
                exit()

def AutoGenerateStructsFromModels(objects, tags):
    #TODO: Convert ranges and deduce field types if possible.
    print "    Generating Auto-structs..."
    for objName in objects[1]:
        if objName[0]!='!':
            autoFlag = 'autoGen' in objects[0][objName]
            stateType=objects[0][objName]['stateType']
            if(autoFlag and stateType=='struct'):
                print("        Object:", objName)
                thisModel=progSpec.findModelOf(objects, objName)
                newFields=[]
                for F in thisModel['fields']:
                    baseType=progSpec.TypeSpecsMinimumBaseType(objects, F['typeSpec'])
                    G = F.copy()
                    if baseType!=None:
                        G['typeSpec']=F['typeSpec'].copy()
                        G['typeSpec']['fieldType']=baseType
                    newFields.append(G)
                objects[0][objName]['fields'] = newFields
    #exit(2)


def GroomTags(tags):
    # Set tag defaults as needed
    tags[0]['featuresNeeded']['System'] = 'system'
    # TODO: default to localhost for Platform, and CPU, etc. Add more combinations as needed.
    if not ('Platform' in tags[0]):
        platformID=platform.system()
        if platformID=='Darwin': platformID="OSX_Devices"
        tags[0]['Platform']=platformID
    if not ('Language' in tags[0]):
        tags[0]['Language']="CPP"

    # Find any needed features based on types used
    for typeName in progSpec.storeOfBaseTypesUsed:
        if(typeName=='BigNum' or typeName=='BigFrac'):
            print 'NOTE: Need Large Numbers'
            progSpec.setFeatureNeeded(tags, 'largeNumbers', progSpec.storeOfBaseTypesUsed[typeName])


def GenerateProgram(objects, buildSpec, tags, libsToUse):
    result='No Language Generator Found for '+buildSpec[1]['Lang']
    langGenTag = buildSpec[1]['Lang']
    if(langGenTag == 'CPP'):
        print "\n\n######################  G E N E R A T I N G   C + +   P R O G R A M . . ."
        xlator = xlator_CPP.fetchXlators()
        result=CodeGenerator.generate(objects, [tags, buildSpec[1]], libsToUse, xlator)
    elif(langGenTag == 'Java'):
        print "\n\n######################  G E N E R A T I N G   J A V A   P R O G R A M . . ."
        xlator = xlator_Java.fetchXlators()
        result=CodeGenerator.generate(objects, [tags, buildSpec[1]], libsToUse, xlator)
    else:
        print "ERROR: No language generator found for ", langGenTag
    return result

def ChooseLibs(objects, buildSpec, tags):
    print "\n\n######################   C H O O S I N G   L I B R A R I E S"
    # TODO: Why is fetchTagValue called with tags, not [tags]?
    libList = progSpec.fetchTagValue([tags], 'libraries')
    Platform= progSpec.fetchTagValue([tags, buildSpec[1]], 'Platform')
    Language= progSpec.fetchTagValue([tags, buildSpec[1]], 'Lang')
    CPU     = progSpec.fetchTagValue([tags, buildSpec[1]], 'CPU')
    print "PLATFORM, LANGUAGE, CPU:", Platform, ',', Language, ',', CPU

    compatibleLibs=[]
    for lib in libList:
        libPlatforms=progSpec.fetchTagValue([tags], "libraries."+lib+".platforms")
        libBindings =progSpec.fetchTagValue([tags], "libraries."+lib+".bindings")
        libCPUs     =progSpec.fetchTagValue([tags], "libraries."+lib+".CPUs")
        libFeatures =progSpec.fetchTagValue([tags], "libraries."+lib+".features")
        #print "LIB:", lib
        #print libPlatforms
        #print libBindings
        #print libCPUs
        #print libFeatures

        LibCanWork=True
        if not (libPlatforms and Platform in libPlatforms): LibCanWork=False;
        if not (libBindings and Language in libBindings): LibCanWork=False;
      #  if not (libCPUs and CPU in libCPUs): LibCanWork=False;

        if(LibCanWork):
            print lib, "works for this system."
            compatibleLibs.append([lib, libFeatures])

    # TODO: This should cause error if a need isn't met. And, it should resolve when multiple libraries can meet a need.
    featuresNeeded = progSpec.fetchTagValue([tags], 'featuresNeeded')
    print "Features Needed:", featuresNeeded
    progSpec.libsToUse={}
    for need in featuresNeeded:
        print "    ", need
        for LIB in compatibleLibs:
            if(need in LIB[1]):
                progSpec.libsToUse[LIB[0]] = True
                print "        ", LIB[0]

    print "USING LIBS: ", progSpec.libsToUse
    for Lib in progSpec.libsToUse:
        if   (Lib=="GTK3"): Lib_GTK3.use(objects, buildSpec, [tags, buildSpec[1]], Platform)
        elif (Lib=="SDL2"): Lib_SDL2.use(objects, buildSpec, [tags, buildSpec[1]], Platform)
        elif (Lib=="Java"): Lib_Java.use(objects, buildSpec, [tags, buildSpec[1]], Platform)
        elif (Lib=="CPP"):  Lib_CPP.use(objects, buildSpec, [tags, buildSpec[1]], Platform)
        elif (Lib=="Swing"):  Lib_Swing.use(objects, buildSpec, [tags, buildSpec[1]], Platform)
        elif (Lib=="Android"):  Lib_Android.use(objects, buildSpec, [tags, buildSpec[1]], Platform)
        elif (Lib=="AndroidGUI"):  Lib_AndroidGUI.use(objects, buildSpec, [tags, buildSpec[1]], Platform)

    return progSpec.libsToUse

def GenerateSystem(objects, buildSpecs, tags):
    print "\n\n######################   G E N E R A T I N G   S Y S T E M"
    ScanAndApplyPatterns(objects, tags)
    AutoGenerateStructsFromModels(objects, tags)
    stringStructs.CreateStructsForStringModels(objects, tags)
    GroomTags([tags, buildSpecs])

    for buildSpec in buildSpecs:
        buildName=buildSpec[0]
        print "    Generating code for build", buildName

  #      progSpec.removeFieldFromObject(objects, "GLOBAL",  "initialize");
  #      progSpec.removeFieldFromObject(objects, "GLOBAL", "deinitialize");
        progSpec.MarkItems=True
        libsToUse=ChooseLibs(objects, buildSpec, tags)
        outStr = GenerateProgram(objects, buildSpec, tags, libsToUse)
        fileName = tagStore['FileName']
        langGenTag = buildSpec[1]['Lang']
        if(langGenTag == 'CPP'): fileExtension='.cpp'
        elif(langGenTag == 'Java'): fileExtension='.java'
        else: print "ERROR: unrecognized language ", langGenTag
#        writeFile(buildName, fileName, outStr, fileExtension)
        #GenerateBuildSystem()###################################################
        libFiles=[]
        for lib in libsToUse:
            tmpLibFiles=(progSpec.fetchTagValue([tags, buildSpecs], 'libraries.'+ lib +'.libFiles'))
            libFiles+=tmpLibFiles
        #TODO: need debug mode and minimum version

        buildDog.build("-g", '14',  fileName, libFiles, buildName, outStr)
        progSpec.rollBack(objects)
    # GenerateTests()
    # GenerateDocuments()
    return outStr


#############################################    L o a d / P a r s e   P r o g r a m   S p e c

if(len(sys.argv) < 2):
    print "No Filename given.\n"
    exit(1)

file_name = sys.argv[1]
codeDogStr = stringFromFile(file_name)
codeDogStr = processIncludedFiles(codeDogStr)


# objectSpecs is like: [ProgSpec, objNames]
print "######################   P A R S I N G   S Y S T E M  (", file_name, ")"
[tagStore, buildSpecs, objectSpecs] = codeDogParser.parseCodeDogString(codeDogStr)
tagStore['dogFilename']=file_name

outputScript = GenerateSystem(objectSpecs, buildSpecs, tagStore)
print "\n\n######################   D O N E"
