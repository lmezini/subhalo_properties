import numpy as np
from astropy.io import ascii
from astropy.table import Table, Column
import sys
from numpy.linalg import norm,eig
import random
import glob
from helpers.io_utils import hlist2pandas


def uniform_random_rotation(x):
    """Apply a random rotation in 3D, with a distribution uniform over the
    sphere.

    Arguments:
        x: vector or set of vectors with dimension (n, 3), where n is the
            number of vectors

    Returns:
        Array of shape (n, 3) containing the randomly rotated vectors of x,
        about the mean coordinate of x.

    Algorithm taken from "Fast Random Rotation Matrices" (James Avro, 1992):
    https://doi.org/10.1016/B978-0-08-050755-2.50034-8
    """

    def generate_random_z_axis_rotation():
        """Generate random rotation matrix about the z axis."""
        R = np.eye(3)
        x1 = np.random.rand()
        R[0, 0] = R[1, 1] = np.cos(2 * np.pi * x1)
        R[0, 1] = -np.sin(2 * np.pi * x1)
        R[1, 0] = np.sin(2 * np.pi * x1)
        return R

    # There are two random variables in [0, 1) here (naming is same as paper)
    x2 = 2 * np.pi * np.random.rand()
    x3 = np.random.rand()

    # Rotation of all points around x axis using matrix
    R = generate_random_z_axis_rotation()
    v = np.array([np.cos(x2) * np.sqrt(x3), np.sin(x2) * np.sqrt(x3), np.sqrt(1 - x3)])
    H = np.eye(3) - (2 * np.outer(v, v))
    M = -(H @ R)
    x = x.reshape((-1, 3))
    mean_coord = np.mean(x, axis=0)

    return ((x - mean_coord) @ M) + mean_coord @ M


def transform(v1,v2,axis = None):
    #convert to coords of principal axis (v2)
    #Take transpose so that v1[0],v1[1],v1[2] are all x,y,z respectively
    v1 = v1.T
    v_new = np.zeros(np.shape(v1))

    #loop over each of the 3 coorinates
    if axis == None:
        for i in range(3):
            v_new[i] += v1[0]*v2[i,0]+v1[1]*v2[i,1]+v1[2]*v2[i,2]
        return v_new
    else:
        v_new[0] += v1[0]*v2[axis,0]+v1[1]*v2[axis,1]+v1[2]*v2[axis,2]
        return v_new


def rotate_position(host_I, pos, rvir):
    """Transform particle position to randomly rotated coordinate system

    Args:
        host_I (_type_): host halo inertia tensor
        pos (_type_): particle position coordinates (x,y,z)
        rvir (_type_): halo virial radius

    Returns:
        _type_: 2d projected distance of particle from halo center
    """
    hw, hv = get_eigs(host_I, rvir)
    new_pos = transform(pos, hv).T

    new_hv = uniform_random_rotation(hv)

    hA = new_hv[0]
    hB = new_hv[1]

    new_pos = transform(pos,hv).T
    hA2 = np.repeat(hA,len(new_pos)).reshape(3,len(new_pos)).T
    hB2 = np.repeat(hB,len(new_pos)).reshape(3,len(new_pos)).T
    para1 = (new_pos*hA2/norm(hA)).sum(axis=1)
    para2 = (hA/norm(hA)).T

    t = np.arccos(abs((new_pos*hA2).sum(axis=1)/(norm(new_pos,axis=1)*norm(hA))))
    #p = np.arccos((perp*hB2).sum(axis=1)/(norm(hB)*norm(perp,axis=1)))

    return t


def get_eigs(I,rvir):
    #return eigenvectors and eigenvalues
    w,v = eig(I)
    #sort in descending order
    odr = np.argsort(-1.*w)
    #sqrt of e values = a,b,c
    w = np.sqrt(w[odr])
    v = v.T[odr]
    #rescale so major axis = radius of original host
    ratio = rvir/w[0]
    w[0] = w[0]*ratio #this one is 'a'
    w[1] = w[1]*ratio #b
    w[2] = w[2]*ratio #c

    return w,v

particle_mass = 1.3e8 ##M_sun/h##                                           
host_vals = ascii.read('host_og_vals_rhap.table', format = 'commented_header')
host_I = np.load('inertia_tensor_stuff/rhap_host_inertia_tensor_no_norm_v2.npy')

rvirs = host_vals['rvir']
mvirs = host_vals['mvir']
hostx = host_vals['hostx']
hosty = host_vals['hosty']
hostz = host_vals['hostz']
hostvx = host_vals['hostvx']
hostvy =host_vals['hostvy']
hostvz = host_vals['hostvz']
host_shapes = host_vals['host_shapes']
host_spins = host_vals['host_spins']
host_cs = host_vals['host_cs']
hostJx = host_vals['hostJx']
hostJy = host_vals['hostJy']
hostJz = host_vals['hostJz']


ang_cut = np.linspace(1,90,90)

mass_frac_A_ang = np.zeros((len(host_vals),len(ang_cut)))
mass_frac_random = np.zeros((int(len(host_vals)*5),len(ang_cut)))

halo_names = []
host_ids = []

with open('halos_info_2.txt') as f:
    for l in f:
        this_halo, host_id, block, _ = l.split()
        halo_names.append(this_halo)
        host_ids.append(host_id)

m=0
for j,f in enumerate(halo_names):
    print(f)
    # load host                                                                 
    path = '/home/lom31/rhap_particles/rhapsody/{}/rockstar/'.format(f)
    hostvalues = hlist2pandas(path + '/out_199.list')
    hostvalues = Table.from_pandas(hostvalues)

    fname = '/home/lom31/rhap_particles/particle_tables/{}_sub_1rvir.particle_table'.format(f)
    particlevalues = ascii.read(fname, format = 'commented_header')
    ##Make sure chosen particles are within the virial radius##                 
    r = Column(np.sqrt(particlevalues['x']**2+particlevalues['y']**2+particlevalues['z']**2),name='r')

    particlevalues.add_column(r)

    whlimit = np.where(particlevalues['r']<=rvirs[j])
    particlevalues = particlevalues[whlimit]

    ##The following are arrays of floats##                                      
    ##Position in Mpc/h##                                                       
    x = particlevalues['x']
    y = particlevalues['y']
    z = particlevalues['z']
                                            
    ##Calculate Position##                                                      
    posx = (x - hostx[j])
    posy = (y - hosty[j])
    posz = (z - hostz[j])
    pos = np.array(list(zip(posx, posy, posz)))
    host_pos = [hostx[j],hosty[j],hostz[j]]

    hw, hv = get_eigs(host_I[j],rvirs[j])
        
    new_pos = transform(pos,hv).T
    hA = host_I[j][0]
    hA2 = np.repeat(hA,len(new_pos)).reshape(3,len(new_pos)).T
    hB = host_I[j][1]
    hB2 = np.repeat(hB,len(new_pos)).reshape(3,len(new_pos)).T
    hC = host_I[j][2]
    para1 = (new_pos*hA2/norm(hA)).sum(axis=1)
    para2 = (hA/norm(hA)).T
    para = np.array((para2[0]*para1,para2[1]*para1,para2[2]*para1))
    perp = new_pos-para.T

    t = np.arccos(abs((new_pos*hA2).sum(axis=1)/(norm(new_pos,axis=1)*norm(hA))))*180./np.pi
    p = np.arccos((perp*hB2).sum(axis=1)/(norm(hB)*norm(perp,axis=1)))
    for k in range(len(ang_cut)):
        mass_frac_A_ang[j][k]+=particle_mass*len(new_pos[t<ang_cut[k]])/mvirs[j]

    for n in range(5):
        rand_t = rotate_position(host_I[j],pos,rvirs[j])*180/np.pi
        for k in range(len(ang_cut)):
            mass_frac_random[m][k]+=particle_mass*len(new_pos[rand_t<ang_cut[k]])/mvirs[j]

        m+=1

    np.savez('rhap_mass_frac_ang_fixed_1rvir.npz',A = mass_frac_A_ang, rand = mass_frac_random)
