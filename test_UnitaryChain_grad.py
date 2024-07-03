import numpy as np
from UnitaryChain import *


##	two qubit gates
CntrlX = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], dtype=float)
CntrlZ = np.diag([1.,1.,1.,-1.])
F4 = np.array([[1,1,1,1],[1,1j,-1,-1j],[1,-1,1,-1],[1,-1j,-1,1j]]) / 2.


def init_RNG(rand_seed):
	##	Initialize random number generator
	if np.version.version >= '1.17.0':
		return np.random.default_rng(rand_seed)
	else:
		return np.random.RandomState(rand_seed)




def check_grad_weight2_to_target(par):
	"""Check the function compute_grad_weight2_to_target()."""
	rand_seed, tol_factor = par
	print("check_grad_weight2_to_target(rand_seed = {}, tol_factor = {})".format( rand_seed, tol_factor ))
	RNG = init_RNG(rand_seed)

	UC0 = two_qubits_unitary(F4);
	UC0.set_coef(penalty=1.)
	UC0.subdivide_at_step(0, 2)
	UC0.del_Vs(2)
	#print(UC0.str())
	print(UC0.check_consistency())

	W0 = UC0.weight2_to_target()
	gradW = UC0.compute_grad_weight2_to_target(UC0.U_to_target())
	H = Gaussian_Hermitian(4, RNG=RNG)
	HgradW = np.sum(gradW.conj() * H).real
	print("H . gradW =", HgradW)
	for eps in [1e-2, 1e-3, 1e-4, 1e-5, 1e-6]:
		UC = UC0.copy()
		UC.apply_expiH_to_V_at_step(1, H * eps)
		W = UC.weight2_to_target()
		dW = W - W0
		second_order_comp = dW/eps - HgradW
		#print("w0 = {} , w = {} , dw = {}".format( W0, W, dW ))
		print("\teps = {}  \t dW/eps = {} \t {}".format( eps, dW/eps, second_order_comp ))
		assert np.abs(second_order_comp) < eps * tol_factor
	print('\n')


def check_grad_weight2_at_step(par):
	rand_seed, tol_factor = par
	print("check_grad_weight2_at_step(rand_seed = {}, tol_factor = {})".format( rand_seed, tol_factor ))
	RNG = init_RNG(rand_seed)

	UC0 = two_qubits_unitary(F4 @ CntrlX);
	UC0.set_coef(Rabi1 = 0.3, Rabi2 = 1., penalty=5.)
	UC0.subdivide_at_step(0, 3)
	UC0.del_Vs(1)
	#print(UC0.str())
	UC0.check_consistency()

	w0ref = UC0.weight2_at_step(0)
	w1ref = UC0.weight2_at_step(1)
	gradHL_s0, gradHR_s0 = UC0.compute_grad_weight2_at_step(0)
	gradHL_s1, gradHR_s1 = UC0.compute_grad_weight2_at_step(1)
	print(gradHL_s0, "= gradHL")
	print(gradHR_s1, "= gradHR")
	H = Gaussian_Hermitian(4, RNG=RNG)
	#print(H, "= H")
	HgradHL = np.sum( gradHL_s0.conj() * H ).real
	HgradHR = np.sum( gradHR_s1.conj() * H ).real
	print("w0ref = {} \t w1ref = {}".format( w0ref, w1ref ))
	print("HgradHL = {} \t HgradHR = {}".format( HgradHL, HgradHR ))
	for eps in [1e-2, 1e-4, 1e-6, 1e-7]:
		UC = UC0.copy()
		UC.apply_expiH_to_V_at_step(1, H * eps)
		#UC.check_consistency()
		#print(UC.U(0) @ UC0.U(0).conj().T)
		w0 = UC.weight2_at_step(0)
		w1 = UC.weight2_at_step(1)
		dw0 = w0 - w0ref
		dw1 = w1 - w1ref
		print("\teps = {} \t dw0 = {} \t dw1 = {}".format( eps, dw0, dw1 ))
		second_order_comp = dw0 / eps - HgradHL
		#print( second_order_comp , eps * UC0.coef['penalty']**2 )
		assert np.abs(second_order_comp) < eps * UC0.coef['penalty']**2 * tol_factor
	print('\n')


def check_grad_total_weight2(par):
	"""Check the function compute_grad_weight2()."""
	rand_seed, tol_factor = par
	print("check_grad_total_weight2(rand_seed = {}, tol_factor = {})".format( rand_seed, tol_factor ))
	RNG = init_RNG(rand_seed)
	
	Utarget = np.kron( [[4,1],[-1,4]] , [[2j,1],[1,2j]] ) / np.sqrt(17 * 5) @ F4 @ np.diag([1,1,1,np.exp(1j*np.pi/6)])
	UC0 = two_qubits_unitary(Utarget)
	UC0.subdivide_at_step(0, 4)
	UC0.check_consistency()
	UC0.del_Vs(2)
	UC0.apply_U_to_V_at_step(1, CntrlZ)
	UC0.apply_U_to_V_at_step(3, CntrlX)
	UC0.check_consistency()
	#print(UC0.str())
	UC0.set_coef(Rabi1 = 0.3, Rabi2 = 1.2, penalty=2.1)
	print(UC0.str(verbose=1))

	W0 = UC0.weight_total()
	gradW = UC0.compute_grad_weight2(enforce_U2t_0weight=False)
	H = [None] + [ Gaussian_Hermitian(4, RNG=RNG) for i in range(1,4) ]
	HgradW = np.sum([ np.sum(gradW[i].conj() * H[i]).real for i in range(1,4) ])
	print("  H = None, {}, {}, {}".format( *[ str(H[i][0,:2]) + " ... " for i in range(1,4) ] ))
	print("  H . gradW =", HgradW)
	for eps in [1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7]:
		UC = UC0.copy()
		for i in range(1, 4): UC.apply_expiH_to_V_at_step(i, H[i] * eps)
		W = UC.weight_total()
		dW = W - W0
		second_order_comp = dW/eps - HgradW
		print("  eps = {:1.1e}   \t dW/eps = {} \t {} ~= {:.3f} * {} * {}".format( eps, dW/eps, second_order_comp, second_order_comp/UC0.coef['penalty']**2/eps, UC0.coef['penalty']**2, eps ))
		#print( second_order_comp , eps * UC0.coef['penalty']**2 )
		assert np.abs(second_order_comp) < eps * UC0.coef['penalty']**2 * tol_factor
	print('\n')



def test_grad_weight2():
	yield check_grad_weight2_to_target, (65, 40.)
	yield check_grad_weight2_to_target, (40, 40.)
	yield check_grad_weight2_to_target, (90, 40.)
	yield check_grad_weight2_to_target, (8102, 40.)
	yield check_grad_weight2_at_step, (42, 2.)
	yield check_grad_weight2_at_step, (52, 2.)
	yield check_grad_weight2_at_step, (62, 2.)
	yield check_grad_weight2_at_step, (72, 2.)
	yield check_grad_total_weight2, (36, 30.)
	yield check_grad_total_weight2, (46, 30.)
	yield check_grad_total_weight2, (56, 30.)
	yield check_grad_total_weight2, (66, 30.)
	yield check_grad_total_weight2, (76, 30.)
	yield check_grad_total_weight2, (2076, 30.)



##	Maybe move this to another file
def test_subdiv():
	print("test_subdiv()")
	Rabi1 = 0.23; Rabi2 = 1.3; penalty = 3.7

	#print("== Load CtrlZ with 3-step construction.")
	UC = two_qubits_unitary(CntrlZ);
	UC.set_coef(Rabi1 = Rabi1, Rabi2 = Rabi2, penalty = penalty)
	UC.load_from_Ulist([ np.kron( [[1,-1],[1,1]], [[1,-1],[1,1]] )/2. ,
		np.array([ [1,0,0,1j], [0,1,1j,0], [0,1j,1,0], [1j,0,0,1] ])/np.sqrt(2) ,
		np.kron( [[1,1],[-1,1]], [[1,1],[-1,1]] ) / 2. , ])
	UC.check_consistency()
	print(UC.str(verbose = 2))

	def assert_close(a, b, tol=1e-13):
		assert abs(a-b) <= tol
	exp_weight2 = [ Rabi1**2 / 2, Rabi2**2 / 2, Rabi1**2 / 2 ]

	assert_close( UC.weight2_at_step(0) , exp_weight2[0] )
	assert_close( UC.weight2_at_step(1) , exp_weight2[1] )
	assert_close( UC.weight2_at_step(2) , exp_weight2[2] )
	assert_close( UC.weight2_to_target() , 0. )
	UC.subdivide_every_step([2,3,1])
	UC.check_consistency()
	print(UC.str(verbose = 2))
	assert UC.N == 6
	assert_close( UC.weight2_at_step(0) , exp_weight2[0] / 4 )
	assert_close( UC.weight2_at_step(1) , exp_weight2[0] / 4 )
	assert_close( UC.weight2_at_step(2) , exp_weight2[1] / 9 )
	assert_close( UC.weight2_at_step(3) , exp_weight2[1] / 9 )
	assert_close( UC.weight2_at_step(4) , exp_weight2[1] / 9 )
	assert_close( UC.weight2_at_step(5) , exp_weight2[2] )
	assert_close( UC.weight2_to_target() , 0. )
	print("\n")



################################################################################
if __name__ == "__main__":
	print("==================== Test matrix identities ====================")
	np.set_printoptions(linewidth=2000, precision=4, threshold=10000, suppress=False)

	if 1:		# test derivative
		for t,c in test_grad_weight2(): t(c)
		test_subdiv()

