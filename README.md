# Tesselater
An open-source program to emulate geometrical tesselation errors in 3d printing and real world interaction.
Inspired by Will-It-Print:
[Read the paper here](https://link.springer.com/article/10.1007/s12008-021-00786-w)

# 1-Introduction
This code was designed to be an open source form of predicting 3d printing errors based on given parameters and analysis of a determined mesh.The objective is both being functional enough to be used in individual
Scale manufacture and particular case study of errors in mesh.In the neear future more will be released concerning support correct and model otimization.For initial configuration and calculus,PLA was the material considerated and parameters are set to simulate aspects of a Ender-3 Printer.


## Parameters Explanation:

## 1.0-Curses.py:
The file where the main part is hosted and where it should initially run.

## 1.1-Warping:
Warping is defined by the deformation of the plastic layer over time after cooling.The warp of a print has an intrinsic relation to the material and format of a print,being proportional to a shrinkness constant of the specific material.In the analysis,the consideration is specifically designed to calculate and plot the warping effect on the first layer of the print,being directly proportional to the geometry of the first layer of the print,which causes the majority of fatal errors concerning warp since the model is dislocated when temperature is not adequate.Besides geometrical analysis and material comparison,further problems may be caused by
print-bed conditions,Inadequate room temperature for cooling,fan defect,wrong print temperatures and other effects.Be sure to ensure that the conditions to print in specific material are proper.Warping formula gives an explanation of how the percentage shown is calculated and is an apporximation based on a theoretical relation.
Warping Formula:
A concise formula developed to calculate variables based on user-defined configurations.

## 1.2-Small Parts:

When dealing with FDM of small parts with lots of details,it's important to consider Nozzle size and the Microstepping of the motors,since these two interfere in the minimal printable details.We check for those two
and give the possible cells that are prone to error.Note that it's important to check for the Roughness cells from Roughness parameter,since support fusion can provoke loss of detail in the overhang parts of the cells.

## 1.3-Roughness:

A method originally imported from Will It Print.It enables to see rough cells based on nozzle angle with the mesh(It also considers overhang_cells).Roughness also interferes with loss of detail.

## 1.4-Toppling:
Toppling is an interesting behavior of some prints,where it will tend to collapse after a due period of time.Toppling seems to have a close relation with the warping aspect,hence why it imports the warping percentage aspect of the print.It also looks for the center of mass disposition based on the inclination.Note that it always considers usage of supports,so if the model design intends to have a new support type or is somewhat required to be made without support,this might Throw in errors.As a disposition to check for warping errors we calculate a safe volume where shrinkage will not interfere in the piece falling over.The circle that forms underneath the mesh is a projection of the center of mass limited by a threshold that defines the acceptable off axis of the center of mass.At the start,warping will be presented in a new window,as it is necessary to distinguish first layer effects on Toppling.The center of mass shall be projected after the first window is closed,demonstrating underneath the mesh if the first layer obeys the logic of a centered circle(It will consider it stable if the circle projection is inside the first layer)

## 1.5-Shrinkage:
Shrinkage is not deduced,but rather taken as pre researched numbers according to a table reference.However,original variables for calculating the real shrinkage are present and could be used with a vision IA to give a very real value percentage of shrinkage.This part interferes with almost every other parameter of the code.Since it shows the affected surface,it could be used to determine the fitness of 3d printed pieces in mounts.

## 1.6-Extra Plotted tools:
Vector calculation,Center of mass and mesh infill correction are some of requisited variables to see when dealing with most in depth parts of 3d printing and mesh qualty control.
They're added here by themselves.

Additional technical info on the program is located on explanations.txt

# 2-Installation:
First download the Rar or clone the library,after that install the required libraries in requirements.txt and you should be ready to go.You could also install pyvista,pyvistaAqt and numpy if you're looking for a more compact approach.

         git clone https://github.com/GMHadou/Tesselater.git
         pip install -r requirements.txt
# 3-Interpretation and Usage

## 3.1-Warping Analysis:
Warping will show in a different image the difference expected in the mesh,being it the purple mesh shown with "pointy" edges towars a centroid above it,
symbolizing a behavior of warping very common in 3d printing.

## 3.2-Small Details:
If there's any cell that is smaller than the minimal Microstepping of the Printer,it will be shown in red.

## 3.3-Toppling:
Toppling will first show a Image showing the warping properties.On closure,it will display a Screen with a white mesh,with the general analysis of the 
Toppling and on the bottom it will displayed a green circle symbolizing the center of mass projection.

## 3.4-Roughness:
The Bar shows the number of roughness per cell density of the mesh.The most purple regions are the ones where Roughness take a severe toll.

## 3.5-Shrinkage:
The shrinkage orientation is explained on a text onscreen.

## 3.6-Overhangs,Center of Mass and Vector:
Optional Displays for more advanced modelling fixes.

# 4-Settings.py and Configs:
For simpliciry purposes when writing,the settings you're using on your printer as well as constants mid prints such as speed and Temperature are stocked in settings.py.As of today,they're set as
configurable floats(They can also be changed for material,like the constant of shrinkage).Future works shall introduce concepts of Real time analysis using softwares like Klipper and real time info.
For future reference in Percentage of Shrinkage in different materials for analysis(PLA,ABS,etc),please consult [this](https://filament2print.com/gb/blog/136_warping-contractions-3D-printing-parts.html):
![image](https://github.com/GMHadou/Tesselater/assets/106123785/c4893958-179b-4e9a-ba74-80970d967029)

# 5-Conclusion and Feedbacks:
The code is intended to help newcomers and intermidiate owners of 3D Printers.As the first version of this work in some aspects,it may be prone to a lot of bugs
and problems in calculus that will be adjusted.If you think something is wrong when testing and experimenting with this,be sure to communicate it in issues.










