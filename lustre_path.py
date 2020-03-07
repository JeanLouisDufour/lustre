# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 09:39:54 2020

@author: F074018
"""

def get_pack_at_absolute_path(path, prog):
	"return pack (donc dict) ou None"
	if isinstance(path, str):
		path = [path]
	pack = prog
	for p in path:
		pack = pack.get('package',{}).get(p)
		if pack == None:
			break
	return pack

G_prog = G_curr_pack = G_curr_path = None # liste de noms de packages

# INVARIANT :
# G_curr_pack == get_pack_at_absolute_path(G_curr_path)

def path_resolution(p):
	"""
	p est un path Lustre, c.a.d. soit "toto", soit ['::', ..., "toto"]
	return (pack, abs_path) ou (None, None)
	abs_path n'est pas un path Lustre mais une liste de noms de packages
	"""
	""" LRM § 3.2
A path is denoted by a list of identifiers separated by two colons: Id1::Id2::...
::Idn. This path is valid if every identifier refers to a package name, and if the package
Idn is declared into the package Idn-1, and so on. Resolving a path consists in
    PHASE 1 : Id1
searching for an occurrence of Id1 in the subpackages of the current context. If Id1
does not belong to this package list, then it is searched in the subpackages of the father
context or in the father of the father context, until it is found.
    PHASE 2 : Id2 ...
Once this package name is
found, the algorithm searches Id2 in Id1 subpackages, then Id3 in Id2 subpackages,
and so on.
	"""
	# Phase 0 : p : path Lustre -> path 'compile' (donc liste)
	if isinstance(p,str):
		id1 = p; id_tail = []; p = [id1]
	else:
		assert isinstance(p,list) and len(p)>=2 and p[0]=='::' \
			and all(s.isidentifier() for s in p[1:]), p
		id1 = p[1]; id_tail = p[2:]; p = p[1:]
	# Phase 1
	assert G_curr_pack == get_pack_at_absolute_path(G_curr_path, G_prog)
	pa1 = G_curr_pack.get('package',{}).get(id1)
	if pa1 != None:
		pa1_path = G_curr_path + [id1]
	else:
		for i in range(-1, -len(G_curr_path)-1,-1):
			ancestor_path = G_curr_path[:i]
			ancestor_pack = get_pack_at_absolute_path(ancestor_path, G_prog)
			pa1 = ancestor_pack.get('package',{}).get(id1)
			if pa1 != None:
				pa1_path = ancestor_path + [id1]
				break
	if pa1 == None:
		print("path_resolution: {} not found".format(p))
		return None,None
	# Phase 2
	for idx in id_tail:
		pa1 = pa1.get('package',{}).get(idx)
		pa1_path += [idx]
		if pa1 == None:
			print("path_resolution: {} not found".format(p))
			return None,None
	assert pa1 == get_pack_at_absolute_path(pa1_path, G_prog) \
		and pa1_path[-len(p):] == p
	return pa1, pa1_path