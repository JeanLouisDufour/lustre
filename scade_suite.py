import os, subprocess
from xprint import xopen, xclose, xprint

scade_path = r"C:\Program Files\Esterel Technologies\Esterel SCADE 6.2.1\SCADE Suite\bin"
scade_path_R18 = r"C:\Program Files\ANSYS Inc\v192\SCADE\SCADE\bin"
if not os.path.exists(scade_path_R18):
	scade_path_R18 = r"C:\Program Files\ANSYS Inc\v182\SCADE\SCADE\bin"
if not os.path.exists(scade_path_R18):
	scade_path_R18 = r"E:\python\kcg"
if not os.path.exists(scade_path_R18):
	scade_path_R18 = r"F:\python\kcg"
assert os.path.exists(scade_path_R18)

def flatten(folder, ends=()):
	"from ansc_etp_file import Etp_file, flatten"
	assert '' not in folder
	l = []
	for k,v in folder.items():
		if '' in v: ### FileRef
			if ends == () or k.endswith(ends):
				l.append(k)
		else:
			l.extend(flatten(v,ends))
	return l

def run_filter(scade_dirs, root_ops = ['Operator1'], target_dir = None, v66=False):
	"*.xscade ->  kcg_xml_filter_out.scade et kcg.log"
	if isinstance(root_ops, str): root_ops = [root_ops]
	if isinstance(scade_dirs, str): scade_dirs = [scade_dirs]
	scade_dir = scade_dirs[0]
	if target_dir == None: target_dir = scade_dir
	R18_exe, root_node = ('kcg66.exe', '-root') if v66 else ('kcg64.exe', '-node')
	s2c_exe = os.path.join(scade_path_R18, R18_exe) # ou 66
	"""
	stdout :
	SCADE (TM) C Code Generator KCG Version 6.4 (build i21)\r\n
	Copyright (C) Esterel Technologies SA 2002-2014 All rights reserved\r\n\r\n
	No warning was found\r\n
	No error was found\r\n
	No failure occurred\r\n
	"""
	inp_files = []
	for sd in scade_dirs:
		if sd.endswith('.xscade'):
			assert os.path.exists(sd)
			inp_files.append(sd)
		else:
			files = os.listdir(sd) ### sans les chemins
			etp_files = [os.path.join(sd,f) for f in files if f.endswith('.etp')]
			for etp_file in etp_files:
				etp = Etp_file(etp_file)
				xscade_folder = etp.roots.get('Model Files',{})
				xscade_files = flatten(xscade_folder, ('.xscade',))
				assert all(xf.endswith('.xscade') for xf in xscade_files)
				assert all(os.path.exists(os.path.join(sd,xf)) for xf in xscade_files)
				inp_files.extend( os.path.join(sd,xf) for xf in xscade_files )
	command = [s2c_exe, '-xml_filter', '-target_dir', target_dir, root_node, ','.join(root_ops)]+inp_files
	if True:
		print(' '.join(['running :'] + command))
	r = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	return (r.returncode, r.stdout.decode('cp1252'), r.stderr.decode('cp1252')) 

def file_concat(sl, dst_name='tmp.txt', comments=('/*','*/')):
	""
	import shutil, glob
	if not isinstance(sl, list): sl = [sl]
	assert all(isinstance(s,str) for s in sl)
	xl = []
	for s in sl:
		xl.extend(glob.glob(s))
	dst_fd = open(dst_name,'w')
	for x in xl:
		if comments:
			dst_fd.write('\n{}**** BEGIN {} ****{}\n'.format(comments[0],x,comments[1]))
		src_fd = open(x,'r')
		shutil.copyfileobj(src_fd, dst_fd)
		## on pourrait peut-etre tester si le dernier char de dst est un \n ...
		src_fd.close()
		if comments:
			dst_fd.write('\n{}**** END {} ****{}\n'.format(comments[0],x,comments[1]))
	dst_fd.close()
	return dst_name

def run_checker(scade_file, op = 'Operator1', v66=False):
	s2c_exe = os.path.join(scade_path, 's2c613.EXE')
	R18_exe, root_node = ('kcg66.exe', '-root') if v66 else ('kcg64.exe', '-node')
	s2c_exe = os.path.join(scade_path_R18, R18_exe)
	"""
	stdout :
	SCADE (TM) C Code Generator KCG Version 6.4 (build i21)\r\n
	Copyright (C) Esterel Technologies SA 2002-2014 All rights reserved\r\n\r\n
	No warning was found\r\n
	No error was found\r\n
	No failure occurred\r\n
	"""
	if isinstance(scade_file, list) or any(c in scade_file for c in '*?['):
		tmp_name = 'tmp.scade'
		sl = scade_file if isinstance(scade_file, list) else [scade_file]
		scade_file = file_concat(sl,tmp_name)
	command = [s2c_exe, root_node, op, scade_file]
	if True:
		print(' '.join(['running :'] + command))
	r = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	return (r.returncode, r.stdout.decode('cp1252'), r.stderr.decode('cp1252')) 

"""
Usage: dv64.exe [options] -node <node_name> <source_file1>..<source_fileN>

  -node <name>       root node name (mandatory)
  -po <name>         proof obligations
  -tecla-dump <file> basename of the output model and counter-examples in Tecla syntax
  -timeout <int>     timeout for proofs (in seconds)
  -xml <file>        name of the XML output file
  -strategy {prove|debug|induction}
                     strategy to use for the proof
  -start-depth <int> depth to start debugging from
  -stop-depth <int>  maximum proof depth to consider
  -int-size <int>    number of bits of the integer type
  -overflow          additional checks for integer arithmetical operations
  -div-by-zero       additional checks for division by zero
  -I <dir>           directory to add to the list of include directories
  -simu              (undocumented)
  -all-guarantee     (undocumented)
  -all-assume        (undocumented)
  -help              Display this list of options
  --help             Display this list of options

Usage: dv66.exe [options] -root <node_name> <source_file1>..<source_fileN>

  -root <name>       root node name (mandatory)
  -po <name>         proof obligations
  -tecla-dump <file> basename of the output model and counter-examples in Tecla syntax
  -timeout <int>     timeout for proofs (in seconds)
  -xml <file>        name of the XML output file
  -strategy {prove|debug|induction|check-constraints}
                     strategy to use for the proof
  -start-depth <int> depth to start debugging from
  -stop-depth <int>  maximum proof depth to consider
  -overflow          additional checks for integer arithmetical operations
  -div-by-zero       additional checks for division by zero
  -I <dir>           directory to add to the list of include directories
  -simu              (undocumented)
  -all-guarantee     (undocumented)
  -all-assume        (undocumented)
  -help              Display this list of options
  --help             Display this list of options
"""
def run_dv(scade_files, po = "Operator1.Output1", xml_file = r"C:\Temp\scade_dv.xml", tecla_file = r"C:\Temp\scade_dv.tecla", v66=False, verbose=True, timeout=60):
	"necessite une license"
	"dv64 -node Operator1 -po Output1 -strategy prove -xml foo.xml bar.scade"
	"dv66 -root Operator1 -po Output1 -strategy prove -xml foo.xml bar.scade"
	po_oo = po.split('.')
	assert len(po_oo)==2
	dv_name, root_node = ('dv66.exe', '-root') if v66 else ('dv64.exe', '-node')
	dv_exe = os.path.join(scade_path_R18, dv_name) # ou 66
	"""
	stdout :
	DV (6.4) 64-bit Version 18.2 (build i1)\r\n
	ProverSL Data Edition v4.1.30\r\n
	Starting proof with 0 po\r\n
	> Strategy: strategy_type_generic, Sub-strategy: strategy_type_pre_processing\r\n
	> Strategy: strategy_type_generic, Sub-strategy: strategy_type_expansion\r\n
	> Strategy: strategy_type_generic, Sub-strategy: strategy_type_saturation\r\n
	strategy_ok\r\n'
	"""
	if isinstance(scade_files, str): scade_files = [scade_files]
	command = [dv_exe, root_node, po_oo[0], '-po', po_oo[1], '-strategy', 'prove',
			'-xml', xml_file, '-tecla-dump', tecla_file, '-timeout', str(timeout),
			] + scade_files
	if verbose:
		print(' '.join(['running :'] + command))
	r = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	return (r.returncode, r.stdout.decode('cp1252'), r.stderr.decode('cp1252')) 

def run_dv1(scade_files, po = "Operator1.Output1", xml_file = r"C:\Temp\scade_dv.xml", \
			tecla_file = r"C:\Temp\scade_dv.tecla", v66=False, verbose=True, timeout=60, retry = 3):
	""
	po0,po1 = po.split('.')
	t = time.time()
	(retcode, stdout, stderr) = run_dv(scade_file, po, xml_file, tecla_file, v66, verbose, timeout)
	t = time.time()-t
	if retcode == 0:
		assert stderr == '', stderr
		foo = 'po 0 {}: '.format(po1)
		i1 = stdout.find(foo)
		assert i1 >= 0
		i1 += len(foo)
		i2 = stdout.find('\r\n',i1)
		assert i2 >= 0
		status = stdout[i1:i2]
		assert status in cpt
		if status == 'po_error':
			assert 'PO uses non-linear arithmetic' in stdout[i2+2:]
	elif retcode == 1:
		if stderr != '':
			assert 'license' in stderr and 'not available' in stderr
			status = 'license not available'
			if retry > 0:
				xprint('************ license not available, sleeping 60s and then RETRY '+po+ ' ************')
				time.sleep(60)
				(retcode, stdout, stderr, status, t) = run_dv1 \
					(scade_file, po, xml_file, tecla_file, v66, verbose, timeout,retry-1)
		elif 'Strategy timed out' in stdout:
			status = 'timed out'
		elif 'Strategy error: Internal error' in stdout:
			status = 'Internal error'
		elif 'Strategy error: Instance contradictory' in stdout:
			status = 'Instance contradictory'
		elif 'Strategy error: Arithmetic exception' in stdout:
			status = 'Arithmetic exception'
		else:
			status = '?'
			xprint('************ ? stdout************')
			xprint(stdout)
			xprint('************ ? end ************')
	else:
		status = '??'
		xprint('************ ?? stdout ************')
		xprint(stdout)
		xprint('************ ?? stderr ************')
		xprint(stderr)
		xprint('************ ?? end ************')
	return (retcode, stdout, stderr, status, t)

if __name__ == '__main__':
	import time
	home_dir = os.getenv('USERPROFILE')
	zoom_falsifiable = False
	zoom_not_valid = True
	prjl = ['calculer_limites_et_regimes','determiner_modes_generaux']
	for prj in prjl:
		# prj = prjl[0]
		node = 'C_'+prj
		if False:
			kcg_path = r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\c90100_tc\PAR\determiner_modes_generaux\C_determiner_modes_generaux_KCG64\Cible\kcg*.scade'
			scen_dir = r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\c90100_tc\PAR\determiner_modes_generaux'
			#
			main_dir = r'F:\scade\Cas_etude_SafranHE_2_ATCU_S1807\MODEL'
			scade_dir = main_dir + r'\cvob_arrano1g4\c90100_modele\PAR\{}\sc'.format(prj)
			kcg_dir = scade_dir + r'\{}_KCG64'.format(node)
			kcg_path = kcg_dir + r'\kcg*export_probes.scade'
			tcml_dir = main_dir + r'\cvob_c90100_tc\c90100_tc\PAR'
			scen_dir = os.path.join(tcml_dir, prj)
			#
			scen_list = [s[:-6] for s in sorted(os.listdir(scen_dir)) if s.startswith('scen_') and s.endswith('.scade')]
			scen_path = scen_dir+'/scen*.scade'
			scade_file = file_concat([kcg_path,'tcml.scade',scen_path],'DV_'+prj+'.scade')
			prefix_log = './'
			subgoals_list = [[]] * len(scen_list)
		else:
			kcg_dir = home_dir + r'\Documents\scade\cea'
			scade_file = kcg_dir + r'\nDV_{}.scade'.format(prj)
			scen_list = []
			subgoals_list = []
			fd = open(scade_file)
			state = 0
			for li, line in enumerate(fd, start=1):
				if line.startswith('node scen_') and line.endswith('_DV(\n'):
					scen_list.append(line[5:-5])
					assert state == 0, (state, li)
					state = 1
				elif line.startswith('_OK : bool'):
					assert state == 1
					state = 2
					subgoals = []
					if ')' in line:
						state = 0
						subgoals_list.append(subgoals)
				elif state == 2:
					assert line.startswith('_m') and '_OK : bool' in line
					idx = line.find('_OK : bool')
					subgoals.append(line[:idx+3])
					if ')' in line:
						state = 0
						subgoals_list.append(subgoals)
			fd.close()
			prefix_log = kcg_dir + '\\'
		assert len(scen_list) == len(subgoals_list)
		(retcode, stdout, stderr) = run_checker(scade_file, scen_list[0]+'_DV')
		print('CHECKER :\nretcode = '+str(retcode))
		print('stdout = '+stdout); print('stderr = '+stderr)
		if True:
			xopen(prefix_log+'DV_'+prj+'_log.txt')
			cpt = {'po_falsifiable':0,'po_valid':0,'po_error':0,'po_indeterminate':0, \
				  'timed out':0, 'Internal error':0, 'Instance contradictory':0, \
				  'Arithmetic exception':0, 'license not available':0, '?':0, '??':0}
			for sc_i, sc in enumerate(scen_list):
				# if 'strk_n1_OEI_LIC_' not in sc: continue
				po = sc+'_DV._OK'
				(retcode, stdout, stderr, status, t) = run_dv1(scade_file, po=po, verbose=False)
				if (zoom_falsifiable and status == 'po_falsifiable') or (zoom_not_valid and status != 'po_valid'):
					# xprint('BEGIN ZOOM')
					for sg in subgoals_list[sc_i]:
						s_po = sc+'_DV.'+sg
						(s_retcode, s_stdout, s_stderr, s_status, s_t) = run_dv1(scade_file, po=s_po, verbose=False)
						xprint('\t{}: {} (time : {})'.format(s_po, s_status, s_t))
					# xprint('END ZOOM')
				cpt[status] += 1
				xprint('{}: {} (time : {})'.format(po, status, t))
			xprint(cpt)
			xclose()
	if False:
		## SHE LIB
		lib_dir = r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\MODEL\modele_Scade6\cvob_c050\c05050_int\SCStdLib_sources\DesignModel\SCStdLib'
		lib_fnl = ['DIGITAL.xscade','DIGITALZ.xscade','LINEAR.xscade','MATH.xscade','SCStdLib.xscade','SIGNAL.xscade'] 
		dir_src = [
			r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\MODEL\modele_Scade6\cvob_c050\c05050_srces\symboles\sc',
			] + [os.path.join(lib_dir,fn) for fn in lib_fnl]
		oper_list = ['Ztest_Max_table','Ztest_Table_2D']
		dir_target = r'C:/Users/F074018.SDS/Documents/python/scade'
		(retcode, stdout, stderr) = run_filter(dir_src,oper_list, dir_target)
		print('FILTER :\nretcode = '+str(retcode)); print('stdout = '+stdout); print('stderr = '+stderr)
		(retcode, stdout, stderr) = run_checker('kcg_xml_filter_out.scade', op='Ztest_Max_table,Ztest_Table_2D')
		print('CHECKER :\nretcode = '+str(retcode)); print('stdout = '+stdout); print('stderr = '+stderr)
	elif False:
		## SHE calculer_limites_et_regimes
		lib_dir = r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\MODEL\modele_Scade6\cvob_c050\c05050_int\SCStdLib_sources\DesignModel\SCStdLib'
		lib_fnl = ['DIGITAL.xscade','DIGITALZ.xscade','LINEAR.xscade','MATH.xscade','SCStdLib.xscade','SIGNAL.xscade'] 
		dir_src = [
			r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\MODEL\modele_Scade6\cvob_arrano1g4\c90100_modele\PAR\calculer_limites_et_regimes\sc',
			r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\MODEL\modele_Scade6\cvob_arrano1g4\c90100_modele\LIB\types_generaux\sc',
			r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\MODEL\modele_Scade6\cvob_arrano1g4\c90100_modele\LIB\parametrage\sc\activation_conditionnelle.xscade',
			r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\MODEL\modele_Scade6\cvob_arrano1g4\c90100_modele\LIB\parametrage\sc\param_commun.xscade',
			r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\MODEL\modele_Scade6\cvob_arrano1g4\c90100_modele\LIB\parametrage\sc\seq_G_calculer_param_generaux.xscade',
			r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\MODEL\modele_Scade6\cvob_arrano1g4\c90100_modele\API\automate_generique\sc\types_api.xscade',
			r'C:\Users\F074018.SDS\Documents\scade\Cas_etude_SafranHE_1\MODEL\modele_Scade6\cvob_c050\c05050_srces\symboles\sc',
			] + [os.path.join(lib_dir,fn) for fn in lib_fnl]
		oper_list = ['determiner_delta_max_sur_7_taches_rapides']
		oper_list = ['Ztest_calculer_limites_et_regimes']
		dir_target = r'C:/Users/F074018.SDS/Documents/python/scade'
		(retcode, stdout, stderr) = run_filter(dir_src,oper_list, dir_target)
		print('FILTER :\nretcode = '+str(retcode)); print('stdout = '+stdout); print('stderr = '+stderr)
		scade_file = 'kcg_xml_filter_out.scade'
		(retcode, stdout, stderr) = run_checker(scade_file, op=','.join(oper_list))
		print('CHECKER :\nretcode = '+str(retcode)); print('stdout = '+stdout); print('stderr = '+stderr)
		po = 'Ztest_calculer_limites_et_regimes.OK'
		(retcode, stdout, stderr) = run_dv(scade_file, po=po)
		print('DV :\nretcode = '+str(retcode)); print('stdout = '+stdout); print('stderr = '+stderr)
	elif False:
		## SHE calculer_limites_et_regimes DV
		scade_file = 'kcg_xml_filter_out.scade'
		po = 'Ztest_calculer_ipl.OK'
		po = 'Ztest_calculer_limites_et_regimes.OK'
		po = 'Ztest_determiner_delta_max_sur_7_taches_rapides.OK'
		po = 'Ztest_determiner_signaler_ecarts_moteur_anormaux.ecart_moteur_detecte_B_output'
		(retcode, stdout, stderr) = run_dv(scade_file, po=po)
		print('DV :\nretcode = '+str(retcode)); print('stdout = '+stdout); print('stderr = '+stderr)
	elif False:
		## model_file = 'sao_tb_dataflow_L65'
		(retcode, stdout, stderr) = run_filter(r'C:\Users\F074018.SDS\Documents\scade\R18\essai1')
		print('FILTER :\nretcode = '+str(retcode)); print('stdout = '+stdout); print('stderr = '+stderr)
		scade_file = r'C:/Users/F074018.SDS/Documents/python/pyverilog/kcg_xml_filter_out.scade'
		(retcode, stdout, stderr) = run_checker(scade_file)
		print('CHECKER :\nretcode = '+str(retcode)); print('stdout = '+stdout); print('stderr = '+stderr)
		(retcode, stdout, stderr) = run_dv(scade_file)
		print('DV :\nretcode = '+str(retcode)); print('stdout = '+stdout); print('stderr = '+stderr)
	elif False:
		dir_src = r'C:\Users\F074018.SDS\Documents\scade\R16\xeclib';
		oper_list = ['X_BUF'];
		dir_target = r'C:/Users/F074018.SDS/Documents/python/pyverilog'
		dir_src = [r'F:\scadeR16\SDS-0PWK\scadeR16\erts2018',
				r'C:\Program Files\ANSYS Inc\v182\SCADE\SCADE\libraries\libmathext\mathext.xscade']
		oper_list = ['boiler_simple_sm']
		dir_target = r'C:/Users/F074018.SDS/Documents/python/scade'
		(retcode, stdout, stderr) = run_filter(dir_src,oper_list, dir_target)
		print('FILTER :\nretcode = '+str(retcode)); print('stdout = '+stdout); print('stderr = '+stderr)
	elif False:
		(retcode, stdout, stderr) = run_checker('foo.scade', op='top')
		print('CHECKER :\nretcode = '+str(retcode)); print('stdout = '+stdout); print('stderr = '+stderr)

"""
function [exe_pb,result,errors,warnings] = ansk_Scade_run_checker( ...
    model_file)
% 1) appel de SCADE.EXE -check model_file.etp
% (equivalent a SCCHECKER toto.etp)
% ces .EXE appellent STDTCL qui lui-meme appelle kcg613
% et kcg613 enchaine 2 jobs :
% - x2s613 *.xscade pour generer le .scade
% - s2c613 -config toto.txt pour le reste
% 2) appel de s2c613.EXE -node _test model_file.scade
global option_debug
ansk_path = mfilename('fullpath'); % ...\MATLAB\ansk\Vx\ansk_Scade_run_checker
seps = strfind(ansk_path,filesep);
sep = seps(end-1); % l'avant-dernier \
ansk_path = ansk_path(1:sep);
scade_exe = [ansk_path 'scade\bin\SCADE.EXE'];
scade_exe = ['"' scade_exe '"'];
etp_file = ['"' model_file '.etp"'];
command = [scade_exe ' -check ' etp_file];
if ~isempty(option_debug) && option_debug
    disp(['running : ' command])
end
[exe_pb,result] = system(command); % ,'-echo'
if ~exe_pb && ~isempty(result)
    [A count] = sscanf(result, ...
        'Checker ends with %d error(s) and %d warning(s).');
    assert(count==2);
else
    A = [0 0];
end
errors = A(1);
warnings = A(2);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
disp('VERIFICATION DU .scade')
s2c_exe = [ansk_path 'scade\bin\s2c613.EXE'];
s2c_exe = ['"' s2c_exe '"'];
scade_file = ['"' model_file '.scade"'];
command = [s2c_exe ' -node ' '_test' ' ' scade_file];
if ~isempty(option_debug) && option_debug
    disp(['running : ' command])
end
[s2c_exe_pb,s2c_result] = system(command) % ,'-echo'
disp('END VERIFICATION DU .scade')

end %function

"""
