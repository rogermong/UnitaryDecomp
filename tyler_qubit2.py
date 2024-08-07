import numpy as np
from UnitaryChain import *
from stringtools import *
from solutionary import *

I2 = np.eye(2, dtype=float)
PauliX = np.array([[0,1.],[1.,0]])
PauliY = np.array([[0,-1j],[1j,0]])
PauliZ = np.array([[1.,0],[0,-1.]])
Hadamard = np.array([[1,1],[1,-1]], dtype=float) / np.sqrt(2)
##	Some example of two-body gates
CntrlZ = np.diag([1.,1.,1.,-1.])
CntrlX = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], dtype=float)
B = np.sqrt(2-np.sqrt(2))/2 * np.array([[1+np.sqrt(2), 0, 0, 1j], [0, 1, 1j*(1+np.sqrt(2)), 0], [0, 1j*(1+np.sqrt(2)), 1, 0], [1j, 0, 0, 1+np.sqrt(2)]])
SWAP = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=float)

np.set_printoptions(precision=4, linewidth=10000, suppress=True)

##	Target
#UC = two_qubits_unitary(np.array([[1,0,0,0],[0,0,1j,0],[0,1j,0,0],[0,0,0,1]]))		# iSWAP (conversion)
#UC = two_qubits_unitary(np.array([[1,0,0,0],[0,0,-1,0],[0,1,0,0],[0,0,0,1]]))		# conversion Y
#UC = two_qubits_unitary(np.array([[0,0,0,1j],[0,1,0,0],[0,0,1,0],[1j,0,0,0]]))		# gain
#UC = two_qubits_unitary(np.kron(PauliX,I2)*1j)		# Rabi 1
#UC = two_qubits_unitary(np.kron(I2,PauliY)*1j)		# Rabi 2
#UC = two_qubits_unitary(np.kron(PauliX,PauliX)*1j)		# conv + gain
##	Initialize random number generator
if np.version.version >= '1.17.0':
	RNG = np.random.default_rng(55)
else:
	RNG = np.random.RandomState(55)
#for i in range(10):
#	print( Gaussian_Hermitian(2, RNG=RNG) )

## Try to update Vs[i] (steps i-1 and i)

def rand_optimize(x, UC):
	UCbk = UC.copy()
	for itr in range(x):
	    for i in range(1, UC.N):
	        old_w = UCbk.weight_total()
	        smallU = random_small_Unitary(4, RNG=RNG, sigma=5.0)
	        UC.check_consistency()
	        UC.apply_U_to_V_at_point(i, smallU)
	        UC.check_consistency()
	        new_w = UC.weight_total()
	        # if new_w > old_w:
	        #		print("{} -> {}  (reject)".format( old_w, new_w ))
	        #    UC = UCbk.copy()
	        # else:
	        #		print("{} -> {}  (accept)".format( old_w, new_w ))
	        #    UCbk = UC.copy()
	print(UC.str())
	return UC


def grad_optimize(UC):
	grad_desc_step_size = 0.00075
	new_w = UC.weight_total()
	print("start:   \t{}".format( new_w ))
	for itr in range(5000):
		if itr % 1000 == 0:
			UC.unitarize_point("all")
		gradH = UC.compute_grad_weight2()
		old_w = new_w
		for stp in range(1, UC.N+1):
			UC.apply_expiH_to_V_at_point(stp, -gradH[stp] * grad_desc_step_size)
			new_w = UC.weight_total()
		if np.mod(itr, 50) == 0: print("iter {}:  \t{}".format( itr, new_w ))
		if new_w > old_w:
			print("Uh oh...")
		if new_w + 1e-8 > old_w: break
	
	print("="*20, "done", "="*20)
	print("UC coef: ", UC.coef, "\n")
	print(UC.str())
	return UC, grad_desc_step_size

def print_sol():
	print("UC coef: ", UC.coef)
	print("Step size: {} --- Randomizations: {} --- Subdivisions: {} parts of {}".format(grad_desc_step_size, rands, prim_sub, sub_sub))
	print("Weight 1: ", UC.weight1_total(), "\tWeight 2: ", UC.weight_total())
	print(UC.str(verbose=3))

def subdivide_optimize(prim_sub, sub_sub, UC):
	x = 0
	for x in range(prim_sub):
		# UC.subdivide_at_step(x, sub_sub)
		qubit = eval_mags(UC, x)
		print(qubit)
		if qubit != 0:
			UC.subdivide_at_step(x, sub_sub)
			print("-"*5, "subdivided step {} by {}".format(x, sub_sub), "-"*5)
		UC, grad_desc_step_size = grad_optimize(UC)
	return UC, grad_desc_step_size

def eval_mags(UC, s):
	norms = []
	jlogU = UC.jlogU(s)
	jlogUT = jlogU.conj()
	##	MxComp_weights2 = [ pe, R1, R1, pe, R1, 2*R2, 2*R2, pe, R1, 2*R2, 2*R2, pe, pe, pe, pe, pe ]
	R1_comps = np.array([0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0])
	R2_comps = np.array([0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0])
	pe_comps = np.ones(16) - R1_comps - R2_comps
	comps = [ R1_comps, R2_comps, pe_comps ]
	for c in range(2):
		MxComps = (2/np.pi) * np.array([ comps[c][i] * np.sum(UC.ConjMxComp_list[i] * jlogUT) for i in range(16) ]).real
		M = np.tensordot(MxComps, UC.MxComp_list, axes=[[0],[0]]) / 2
		norms.append(Frob_norm(zero_real_if_close(M)))
	return norms.index(max(norms))

UC = two_qubits_unitary(CntrlZ)
dictionary = new_solutionary()
dictionary.load("tyler_sols2.obj")
UC = dictionary.index(3).copy() # SOURCE INDEX
UC.set_coef(penalty=10.0)
print(UC.coef)
print(UC.str(verbose=3))

prim_sub = 3
sub_sub = 3
rands = 1

# UC.subdivide_at_step(0, prim_sub)
"""
for x in range(2):
	UC = rand_optimize(1, UC)
	UC, grad_desc_step_size = grad_optimize(UC)
"""

UC, grad_desc_step_size = subdivide_optimize(prim_sub, sub_sub, UC)
UC, grad_desc_step_size = grad_optimize(UC)

print_sol()

query = input("\n\nSave solution? (y/n): ")
if query == "y":
	name = input("Enter name for solution {}: ".format(dictionary.length())) # NAMING SCHEMA: [INDEX]-[GATE]-[SUBDIVISIONS]P[PENALTY], APPEND +[SOURCE_INDEX] AS RELEVANT
	dictionary.add(UC, name)
	print("Saved as solution {}".format(name))
	dictionary.save("tyler_sols2.obj")
