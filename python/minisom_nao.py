from numpy import genfromtxt, zeros, product, setdiff1d, arange
from parameters import param

import plot_som as ps
import sys
import os
import pdb

from minisom import MiniSom

#TODO
import pylab as pl

def get_path():
	"""
	Path to .dat file generated by NAO's babbling is given by a user in 
	terminal. If valid, return. 
	"""
	nrarg = len(sys.argv)

	if nrarg<2:
		raise Exception('Missing data path')

	path = str(sys.argv[1])

	if not os.path.exists(path):
		raise Exception('Path doesn\'t exist')

	return path

def read_data(path):
	"""
	Return babbling coordinates for hands and joints.
		nrpts - take each nrpts-th coordinate for training
	"""
	
	hands = param['hands']
	joints = param['joints']
		
	data = {
		'hands': genfromtxt(path, skiprows=3, usecols=hands),
		'joints': genfromtxt(path, skiprows=3, usecols=joints)
		}

	return data 

def train_som(data):
	
	som = MiniSom(
		param['nr_rows'],
		param['nr_cols'], 
		data.shape[1], 
		data, 
		sigma=param['sigma'], 
		learning_rate=param['learning_rate'], 
		norm='minmax')
		
	#som.random_weights_init() # choose initial nodes from data points
	som.train_random(param['nr_epochs']) # random training
	
	return som

def hebbian_learning(som1, som2, data):
	s1, s2 = som1.weights.shape, som2.weights.shape
	hebb = zeros((param['nr_rows'], param['nr_cols'], param['nr_rows'], param['nr_cols']))
	
	for dp1, dp2 in zip(som1.data, som2.data):
		act1 = som1.activate(dp1)
		act2 = som2.activate(dp2)
				
		idx1 = som1.winner(dp1)#divmod(act1.argmax(), param['nr_rows'])
		idx2 = som2.winner(dp2)#divmod(act2.argmax(), param['nr_rows'])
		
		#pdb.set_trace()
		#print idx1, idx2, param['eta'] * act1[idx1] * act2[idx2]
		hebb[idx1[0], idx1[1], idx2[0], idx2[1]] += param['eta'] * act1[idx1] * act2[idx2]
		
	return hebb

# useful plotting, TODO extract to plot som
def plot(som_hands, som_joints):
	wi_0, w_0 = som_hands.get_weights()	
	wi_1, w_1 = som_joints.get_weights()

	ps.plot_3d(final_som=w_0, data=som_hands.data[::50], init_som=wi_0, nr_nodes=param['n_to_plot'], title='SOM Hands')
	ps.plot_3d(final_som=w_1, data=som_joints.data[::50], init_som=wi_1, nr_nodes=param['n_to_plot'], title='SOM Joints')


def plot_inactivated_nodes(som, inact):
	_, w = som.get_weights()	
	act = setdiff1d(arange(w.shape[0]), inact)
	
	fig = plt.figure()
	ax = fig.add_subplot(111, projection = '3d')
	data = som.data[::50]
	
	if data.shape[1] > 3:
		print "using only 3 dimensions for plotting"
		data = data[:,:3]
		
	# plot data points	
	d = ax.plot(data[:, 0], data[:,1], data[:,2], c='b', marker='*', linestyle='None', alpha=0.4, label='data')
	
	# plot activated nodes in green
	act_nod = w[act, :]
	a = ax.plot(act_nod[:, 0], act_nod[:, 1], act_nod[:, 2], c='g', marker='o', alpha = 0.6, label='neurons', markersize=4)
	
	#plot inactivated nodes in red
	in_w = w[inact, :]
	i = ax.plot(in_w[:, 0], in_w[:, 1], in_w[:, 2], c='r', marker='o', alpha = 0.6, label='inact. neurons', markersize=6, linestyle='None')
	plt.legend(nrpoints=1)
	
if __name__=="__main__":
	path = get_path()

	# get the coordinates learned during random motor babbling 
	data = read_data(path)

	# train self-organizing maps
	som_hands = train_som(data['hands'])
	som_joints = train_som(data['joints'])

	plot(som_hands, som_joints)
	inact = som_joints.activation_response(som_joints.data)
	coord_inact = where(inact.flatten()==0)[0]
	plot_inactivated_nodes(som_joints, coord_inact)
	
		
	# hebbian learning between maps
	hebb_weights = hebbian_learning(som_hands, som_joints, data)
	h = hebb_weights.reshape(25, 25)

	# print the strongest connections
