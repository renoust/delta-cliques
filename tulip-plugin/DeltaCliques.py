from tulip import *
import tulipplugins
from CliqueMaster import CliqueMaster
from Clique import Clique
import sys

class NullDevice():
	def write(self, s):
		pass

class DeltaCliques(tlp.Algorithm):
	
	def getTripletFromLinkStream(self, e):
		ends = self.graph.ends(e)		
		return [self.time_stamp[e], self.node_prop[ends[0]], self.node_prop[ends[1]], e] 
	
	def getTripletFromMultipleGraph(self, e):
		ends = self.graph.ends(e)
		return [self.time_stamp[e], ends[0], ends[1], e] 
	
	def getTripletFromSimpleGraph(self, e):
		#in this case, time_stamp is a vector
		timeSteps = self.time_stamp[e]
		ends = self.graph.ends(e)
		return [[t, ends[0], ends[1], e] for t in timeSteps]
	
	def tripletGen(self):
		# make sure to ignore loops
		# equal entries will be ignored (only the first in set 
		# will be kept, no influence on the computation)
		
		# maybe here we'd later want to set some time/duration filters etc.
	
		for e in self.graph.getEdges():
			if self.graph_type == "Multiplex graph":
				yield self.getTripletFromMultipleGraph(e)
			if self.graph_type == "Simple graph":
				for triplet in self.getTripletFromSimpleGraph(e):
					yield triplet
			if self.graph_type == "Link stream":
				yield self.getTripletFromLinkStream(e)

	def findCliqueEdgesFromMultiplexGraph(self, clique):
	
		nodes = [n for n in clique._X]
		time_in = clique._tb
		time_out = clique._te
	
		edges = []
	
		iSg = self.graph.inducedSubGraph(nodes)
		for e in iSg.getEdges():
			tE = self.time_stamp[e]
			if tE < time_in:
				continue
			if tE > time_out:
				continue 
			edges.append(e)
		self.graph.delSubGraph(iSg)
			
		return [nodes, edges]
			

	def findCliqueEdgesFromSimpleGraph(self, clique):
		
		nodes = [n for n in clique._X]
		time_in = clique._tb
		time_out = clique._te
	
		edges = []
	
		iSg = self.graph.inducedSubGraph(nodes)
		for e in iSg.getEdges():
			tE = sorted(self.time_stamp[e])
			if min(tE) > time_in and max(tE) < time_out:
				continue
			edges.append(e)
	
		self.graph.delSubGraph(iSg)
			
		return [nodes, edges]
	
	def findCliqueEdgesFromLinkStream(self, clique):
		
		nodes = clique._X
		time_in = clique._tb
		time_out = clique._te
	
		edges = []
	
		tlpnodes = [n for n in self.graph.getNodes() if self.node_prop[n] in nodes]
		iSg = self.graph.inducedSubGraph(tlpnodes)
		final_nodes = []
		for e in iSg.getEdges():
			tE = self.time_stamp[e]
			if tE < time_in:
				continue
			if tE > time_out:
				continue 
			edges.append(e)
			final_nodes.extend(self.graph.ends(e))
	
		self.graph.delSubGraph(iSg)
			
		return [final_nodes, edges]
	
	
	def mapCliquesBack(self, listOfCliques):
		
		listOfCliques = [c for c in listOfCliques]	
		vect_prop = self.graph.getDoubleVectorProperty("__delta_clique_d_"+str(self.delta)+"__")
		nbKCliques = self.graph.getDoubleProperty("__number_of_clique_d_"+str(self.delta)+"__")
		nbCliques = len(listOfCliques)
	
		nodeToClique = {n:[0 for c in range(nbCliques)] for n in self.graph.getNodes()}
		edgeToClique = {e:[0 for c in range(nbCliques)] for e in self.graph.getEdges()}
		
		for i in range(nbCliques):
			c = listOfCliques[i]
			
			if	self.graph_type == "Link stream":
				sg = self.findCliqueEdgesFromLinkStream(c)
			if	self.graph_type == "Simple graph":
				sg = self.findCliqueEdgesFromSimpleGraph(c)
			if	self.graph_type == "Multiplex graph":
				sg = self.findCliqueEdgesFromMultiplexGraph(c)
		
			for n in sg[0]:
				nodeToClique[n][i] = 1 
			for e in sg[1]:
				edgeToClique[e][i] = 1
	
			if self.one_boolean_property_per_clique:
				prop = self.graph.getBooleanProperty("__delta_clique_d_"+str(self.delta)+"_c_"+str(i)+"__")
				for n in sg[0]:
					prop[n] = True
				for e in sg[1]:
					prop[e] = True
			
		for n in nodeToClique:
			vect_prop[n] = nodeToClique[n]
			nbKCliques[n] = sum(nodeToClique[n])
	
		for e in edgeToClique:
			vect_prop[e] = edgeToClique[e]
			nbKCliques[e] = sum(edgeToClique[e])
	
	
	
	def __init__(self, context):
		tlp.Algorithm.__init__(self, context)
		self.addIntegerParameter("Delta", "", "3", True)
		self.addStringCollectionParameter("Input graph type", "", "Link stream;Multiplex graph;Simple graph", True)
		self.addDoublePropertyParameter("Time double property - Link stream / Multiplex graph", "", "__timeStamp__", False)
		self.addPropertyParameter("Time vector property - Simple graph", "", "__timeStampList__", False)
		self.addStringPropertyParameter("Node class - link stream", "", "__original_node__", False)
		self.addBooleanParameter("Boolean property output", "One boolean property per clique", "false", False)
		
	def check(self):
		# This method is called before applying the algorithm on the input graph.
		# You can perform some precondition checks here.
		# See comments in the run method to know how to access to the input graph.

		# Must return a tuple (boolean, string). First member indicates if the algorithm can be applied
		# and the second one can be used to provide an error message
		return (True, "")

	def run(self):
		#graphTypes = ["Link stream", "Multiplex graph", "Simple graph"]
		self.delta = self.dataSet["Delta"]
		self.graph_type = self.dataSet["Input graph type"].getCurrentString()
		self.node_prop = self.dataSet["Node class - link stream"]
		self.one_boolean_property_per_clique = self.dataSet["Boolean property output"]

		#graphType = "Link stream"
		#if graph.getName() in graphTypes:
		#	graphType = graph.getName()
		#node_prop = graph.getStringProperty("__original_node__")
	
		if self.graph_type == "Link stream" or self.graph_type == "Multiplex graph":
			self.time_stamp = self.dataSet["Time double property - Link stream / Multiplex graph"]
			#timeStamp = graph.getDoubleProperty("__timeStamp__")
	
		elif self.graph_type == "Simple graph":
			self.time_stamp = self.dataSet["Time vector property - Simple graph"]
			#timeStamp = graph.getDoubleVectorProperty("__timeStampList__")
			
	
		
		# Initiate
		Cm = CliqueMaster()
		times = dict()
		nodes = dict()
		nb_lines = 0
		
		# Read stream
		# maybe just rewrite an individual accessor for 1 triplet 
		# instead of the whole conversion
		# (needs the edge object for effective return)
	
		for contents in self.tripletGen():
		    #print contents		
		    t = contents[0]
		    u = contents[1]
		    v = contents[2]
		    link = frozenset([u, v])
		    time = (t, t)
		    
		    Cm.addClique(Clique((link, time), set([])))
			
		    # Populate data structures
		    if link not in times:
		        times[link] = []
		    times[link].append(t)
		
		    if u not in nodes:
		        nodes[u] = set()
		
		    if v not in nodes:
		        nodes[v] = set()
		
		    nodes[u].add(v)
		    nodes[v].add(u)
		    nb_lines = nb_lines + 1
	
		Cm._times = times
		Cm._nodes = nodes
		
		tmp_std_err = sys.stderr
		sys.stderr = NullDevice() 
		results = Cm.getDeltaCliques(self.delta)
		sys.stderr = tmp_std_err 
			
		self.mapCliquesBack(results)		
		
		return True

# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("DeltaCliques", "Delta Cliques", "Benjamin Renoust & Jordan Viard", "18/06/2015", "Computes the delta cliques in a link stream", "1.0", "Link Stream")
