import scipy.spatial 

Nozzle_Size = 0.4
Nozzle_Flat = 0.8
Line_Width = 0.2
Layer_Height = 0.1
Minimum = Layer_Height + Nozzle_Size
Maximum = Layer_Height + Nozzle_Flat
Ideal = (Minimum + Maximum) / 2
Speed=80
Temperature = 195

if Temperature <= 210:
    Flow = 10
elif 210<Temperature<250:
    Flow = 12.5
else:
    Flow = 15

Max_Speed = Flow / (Line_Width * Layer_Height)
Speed_Quality = Max_Speed * 0.7

Warping_Tendency= abs(((Speed)*Layer_Height/(Line_Width))-(Speed_Quality)*Layer_Height/(Ideal))
print(Warping_Tendency)