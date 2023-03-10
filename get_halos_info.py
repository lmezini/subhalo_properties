from __future__ import print_function
import os
import numpy as np
from helpers.SimulationAnalysis import readHlist
from urllib.request import urlopen
from io import StringIO
import sys
from astropy.io import ascii
#sys.stdout.flush()

names =['scale','ID','desc_scale','desc_id','num_prog','pid','upid','desc_pid',
    'phantom','sam_mvir','Mvir','Rvir','Rs', 'vrms', 'mmp', 'scale_of_last_MM',
    'Vmax', 'X','Y','Z','VX','VY','VZ','JX','JY','JZ','Spin','Breadth_first_ID',
    'Depth_first_ID','Tree_root_ID','Orig_halo_ID','Snap_num',
    'Next_coprogenitor_depthfirst_ID','Last_progenitor_depthfirst_ID',
    'Rs_Klypin','Mvir_all','M200b','M200c','M500c','M2500c','Xoff','Voff',
    'spin_bullock','b_to_a','c_to_a','A[x]','A[y]','A[z]','b_to_a(500c)',
    'c_to_a(500c)','A[x](500c)','A[y](500c)','A[z](500c)','T/|U|','Macc',
    'Mpeak','Vacc','Vpeak','Halfmass_Scale','Acc_Rate_Inst','Acc_Rate_100Myr',
    'Acc_Rate_Tdyn']
i = 0
halo_names = []
host_ids = []
with open('hlist_halo_ids.txt') as f:
    for l in f:
        this_halo, host_id = l.split()
        halo_names.append(this_halo)
        host_ids.append(int(host_id))

for halo in halo_names:
    hostvalues = ascii.read('/Users/lmezini/proj_2/rs_files/Halo{}/hlist.list'.format(halo),names=names)
    loc = int(np.where(hostvalues['ID']==int(host_ids[i]))[0][0])
    original_host = hostvalues[loc]

"""
all_halos = [f for f in os.listdir('/Users/lmezini/proj_2/rs_files/') if f.startswith('Halo')]# and os.path.isdir(os.path.join('/Users/lmezini/proj_2/rs_files/', f))]
print(all_halos)

for this_halo in sorted(all_halos):
    original_host = readHlist(StringIO(urlopen('http://www.slac.stanford.edu/~yymao/mw_PLAFAO5I69P4L8I4/{}/target_halo.txt'.format(this_halo)).read().decode("utf-8")))
    print(this_halo, original_host['id'][0])
"""
    host_values = host_values[host_values['Mvir'] >= 5.0e11]

    d = np.zeros(len(halo_names))
    for ax in 'xyz':
        d1 = (host_values[ax.upper()] - original_host[ax])
        d1 *= d1
        d += d1
    host = halos[d.argmin()]
    del d, d1, halos

    for i in range(48):
        if host['ID'] in readHlist('/home/cef41/Outputs/{}/halos_0.{}.ascii'.format(this_halo, i), ['ID'])['ID']:
            break
    block = i
    
    print(this_halo, host['ID'], block, '{:E}'.format(host['Mvir']/0.7))
    """
