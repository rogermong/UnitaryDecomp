##

##	Check if this is run by nose or pytest
import sys
PyTSuite = None
if 'nose' in sys.modules.keys(): PyTSuite = 'nose'
if 'pytest' in sys.modules.keys(): PyTSuite = 'pytest'; import pytest

################################################################################
##	Begin test script
import numpy as np
import scipy as sp
from UnitaryChain import *
from stringtools import joinstr


sqrt2 = np.sqrt(2)

I2 = np.eye(2, dtype=float)
PauliX = np.array([[0,1.],[1.,0]])
PauliY = np.array([[0,-1j],[1j,0]])
PauliZ = np.array([[1.,0],[0,-1.]])
Hadamard = np.array([[1,1],[1,-1]], dtype=float) / sqrt2
Tgate = np.diag([1,(1+1j)/sqrt2])

##	A list of 2x2 test matrices
Mx2list = [
	I2, PauliX, PauliY, PauliZ, Hadamard, Tgate,
	]
##	A list of 3x3 test matrices
Mx3list = [
	np.arange(9).reshape(3,3),
	np.array([[2,0,-1],[1,1,-2],[0,-1,3]]),
	np.arange(-5,4).reshape(3,3).transpose(),
	np.array([[0,0,-1],[1,1.5,0],[0,0.5j,0.5]]),
	np.array([[0,0,-1],[1,0,0],[0,0,0]]),
	]
Arr234list = [
	np.arange(24).reshape(2,3,4),
	np.arange(24).reshape(2,3,4) - 11,
	]
MxLists = [None, None, Mx2list, Mx3list]
ArrayDict = { (2,2): Mx2list, (3,3): Mx3list, (2,3,4): Arr234list, }


################################################################################
##	Tests

def check_adjoint_op(par):
	"""Check that ad_M1(M2) = [M1,M2].
	functions tested:  UnitaryChain.adjoint_op_MxRep
"""
	Msize, M1i, M2i, tol = par
	print("check_adjoint_op: {}x{}, ({},{})".format(Msize,Msize,M1i,M2i))
	Mlist = MxLists[Msize]
	M1 = Mlist[M1i]
	M2 = Mlist[M2i]
	v2 = M2.reshape(-1)
	ad1 = adjoint_op_MxRep(M1)
	assert ad1.shape == (Msize**2,Msize**2)
	commute = M1 @ M2 - M2 @ M1
	diff = ad1 @ v2 - commute.reshape(-1)
	assert np.max(np.abs(diff)) <= tol

#TODO set up Parametrized tests
#	def test_adjoint_op():
#		for i in range(len(Mx2list)):
#			for j in range(len(Mx2list)):
#				yield check_adjoint_op, (2,i,j,1e-16)
#		for i in range(len(Mx3list)):
#			for j in range(len(Mx3list)):
#				yield check_adjoint_op, (3,i,j,1e-16)


def check_DexpM(par):
	"""Compare U = exp(X + s*dX) with 1st order formula.
	That is, left inverse exp(-X) U to nexprel(ad_X) s*dX,
	and right inverse U exp(-X) to exprel(ad_X) s*dX.
	functions tested:  UnitaryChain.adjoint_op_MxRep, UnitaryChain.Mx_exprel , UnitaryChain.Mx_nexprel
"""
	Msize, Xi, dXi, dscales, reltol = par
	print("check_DexpM: {}x{}, ({},{}), ds={}".format(Msize,Msize,Xi,dXi,dscales))
	X = MxLists[Msize][Xi]
	dX = MxLists[Msize][dXi]
	invU0 = sp.linalg.expm(-X)
	Id = np.eye(Msize)
	adX = adjoint_op_MxRep(X)
	exp_adX = Mx_exprel(adX)
	iexp_adX = Mx_nexprel(adX)
	estim_2nd_order_size = np.max(np.abs(dX))**2 * np.max(np.abs(exp_adX) + np.abs(iexp_adX))
	for s in dscales:
		U = sp.linalg.expm(X + dX * s)
		dU_iU0 = (U @ invU0 - Id) / s
		iU0_dU = (invU0 @ U - Id) / s
		r_1st_order = exp_adX @ dX.reshape(-1)
		l_1st_order = iexp_adX @ dX.reshape(-1)
		#print(X, "\n", dX, "\n", X + dX * s, "\n", U, "\n", dU_iU0, "\n")
		diff_r = np.max(np.abs( dU_iU0.reshape(-1) - r_1st_order ))
		diff_l = np.max(np.abs( iU0_dU.reshape(-1) - l_1st_order ))
		#print("dU (U^{-1}):", dU_iU0.reshape(-1), r_1st_order, diff_r, diff_r/s)
		#print("(U^{-1}) dU:", iU0_dU.reshape(-1), l_1st_order, diff_l, diff_l/s)
		print("\t{},{}\t dU (U^{{-1}}): {:.5e}, {:.5f}\t (U^{{-1}}) dU: {:.5e}, {:.5f}".format( Xi, dXi, diff_r, diff_r/s/estim_2nd_order_size, diff_l, diff_l/s/estim_2nd_order_size ))
		assert diff_r < reltol * s * estim_2nd_order_size
		assert diff_l < reltol * s * estim_2nd_order_size

#TODO set up Parametrized tests
#	def test_DexpM():
#		for i in range(1,4):
#			for j in range(1,4):
#				yield check_DexpM, (3, i, j, [1e-4, 1e-5, 1e-6, 1e-7], 1.2)
#		yield check_DexpM, (2, 1, 3, [1e-4, 1e-5, 1e-6, 1e-7], 1.2)
#		yield check_DexpM, (2, 2, 1, [1e-4, 1e-5, 1e-6, 1e-7], 1.2)


def check_rank1tensor_approx(par):
	arr_sh, arr_i, exp_overlap, tol = par
	a = ArrayDict[arr_sh][arr_i]
	a_norm = Frob_norm(a)
	print("tensor: {}[{}],  norm = {}".format( arr_sh, arr_i, a_norm ))
	assert a.shape == arr_sh
	ap = rank1tensor_approx(a)
	overlap = np.sum(a.conj() * ap) / a_norm
	print(joinstr(["  array =", a]) + "\n" + joinstr(["  approx =", ap]) + "\n  overlap = " + str(overlap))
	assert ap.shape == a.shape
	assert overlap > exp_overlap - tol
	assert abs(overlap.imag) < tol
	assert ap.dtype == np.promote_types(a.dtype, float)
	app = rank1tensor_approx(ap)
	diff = np.max(np.abs( app - ap ))
	print("  2nd run diff =", diff)
	assert app.shape == ap.shape
	assert app.dtype == ap.dtype
	assert diff < tol
	print()


t_rank1tensor_approx_list = [
	( check_rank1tensor_approx, ((2,2), 4, 0.5 , 1e-13) ),	# Hadamard
	( check_rank1tensor_approx, ((3,3), 0, 0.99, 1e-13) ),
	( check_rank1tensor_approx, ((3,3), 1, 0.81, 1e-13) ),
	( check_rank1tensor_approx, ((3,3), 2, 0.92, 1e-13) ),
	( check_rank1tensor_approx, ((3,3), 3, 0.72, 1e-13) ),
	( check_rank1tensor_approx, ((3,3), 4, 0.5 , 1e-13) ),
	]

if PyTSuite == 'pytest':
	@pytest.mark.parametrize("chk_func, chk_par", t_rank1tensor_approx_list)
	def test_rank1tensor_approx(chk_func, chk_par):
		chk_func(chk_par)
elif PyTSuite == 'nose':
	def test_rank1tensor_approx():
		for cp in t_rank1tensor_approx_list: yield cp



################################################################################
if __name__ == "__main__":
	print("==================== Test matrix identities ====================")
	np.set_printoptions(linewidth=2000, precision=4, threshold=10000, suppress=False)

	if 0:
		for t,c in test_adjoint_op(): t(c)
	#check_DexpM((2, 1, 3, [1e-4, 1e-5, 1e-6, 1e-7], 3.))
	if 0:
		for t,c in test_DexpM(): t(c)

	#check_rank1tensor_approx(((2,3,4), 0, 0.3, 1e-13))
	#TODO, write check_log_unitary

