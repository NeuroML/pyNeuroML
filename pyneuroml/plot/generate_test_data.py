from random import random
import math

t_max = 1

flat = open('flat.spikes','w')
noisy = open('noisy.spikes','w')
sines = open('sines.spikes','w')

rates = {0:100, 1:150}


for id in rates:
    rate = float(rates[id])
    isi = 1/rate
    t = isi
    while t<=t_max:
        flat.write('%i\t%s\n'%(id,t))
        noisy.write('%i\t%s\n'%(id,t+0.002*random()))
        t+=isi
        
for id in range(100):
    av_isi = .01
    t = av_isi
    while t<=t_max:
        av_isi = .01 + 0.005*math.sin(t/.1)
        sines.write('%i\t%s\n'%(id,t))
        t+= av_isi*(.8 + .4*random())
        
    



flat.close()
noisy.close()
sines.close()

    
    

