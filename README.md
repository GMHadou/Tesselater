# Tesselater
An open-source program to emulate geometrical tesselation errors in 3d printing and real world interaction.
Inspired by Will-It-Print

## 1-Introduction
This code was designed to be an open source form of predicting 3d printing errors based on given parameters and analysis of a determined mesh.The objective is both being functional enough to be used in individual
Scale manufacture and particular case study of errors in mesh.In the neear future more will be released concerning support correct and model otimization.For initial configuration and calculus,PLA was the material considerated and parameters are set to simulate aspects of a Ender-3 Printer.


## Parameters Explanation:

## 1.1-Warping:
Warping is defined by the deformation of the plastic layer over time after cooling.The warp of a print has an intrinsic relation to the material and format of a print,being proportional to a shrinkness constant of the specific material.In the analysis,the consideration is specifically designed to calculate and plot the warping effect on the first layer of the print,being directly proportional to the geometry of the first layer of the print,which causes the majority of fatal errors concerning warp since the model is dislocated when temperature is not adequate.Besides geometrical analysis and material comparison,further problems may be caused by
print-bed conditions,Inadequate room temperature for cooling,fan defect,wrong print temperatures and other effects.Be sure to ensure that the conditions to print in specific material are proper.Warping formula gives an explanation of how the percentage shown is calculated and is an apporximation based on a theoretical relation.
Warping Formula:
A concise formula developed to calculate variables based on user-defined configurations.

## 1.2-Small Parts:

When dealing with FDM of small parts with lots of details,it's important to consider Nozzle size and the Microstepping of the motors,since these two interfere in the minimal printable details.We check for those two
and give the possible cells that are prone to error.Note that it's important to check for the Roughness cells from Roughness parameter,since support fusion can provoke loss of detail in the overhang parts of the cells.

## 1.3-Roughness:

A method originally imported from Will It Print.It enables to see rough cells based on nozzle angle with the mesh(It also considers overhang_cells).Roughness interfere also with loss of detail.

## 1.4-Toppling:
Toppling is an interesting behavior of some prints,where it will tend to collapse after a due period of time.Toppling seems to have a close relation with the warping aspect,hence why it imports the warping percentage aspect of the print.It also looks for the center of mass disposition based on the inclination.Note that it always considers usage of supports,so if the model design intends to have a new support type or is somewhat required to be made without support,this might Throw in errors.

1.5-Shrinkage:

Inspired by Research:

[Read the paper here](https://link.springer.com/article/10.1007/s12008-021-00786-w)

