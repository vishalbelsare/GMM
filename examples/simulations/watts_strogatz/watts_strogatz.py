#!/usr/bin/env python
# encoding: utf-8
"""
watts_strogatz.py

Purpose:  Recover the Watts-Strogatz "small world" random graph model with GMM
          see, Duncan J. Watts and Steven H. Strogatz, "Collective dynamics of small-world networks", Nature, 393, pp. 440–442, 1998.

Author:   Drew Conway
Email:    drew.conway@nyu.edu
Date:     2011-03-25

Copyright (c) 2011, under the Simplified BSD License.  
For more information on FreeBSD see: http://www.opensource.org/licenses/bsd-license.php
All rights reserved.
"""

import sys
import os
import networkx as nx
import gmm
from numpy import arange, random
from datetime import datetime
import smtplib
import csv


def watts_strogatz_simulation(test_graph, k, p, seed=None, verbose=False):
    """
    Given a set of Watts-Strogatz "small-world" random graphs, simulate using above growth rule
    """
    
    # Required to change the growth rule dynamically, so 
    # we define it inside the simulation function
    def watts_strogatz_growth(base, new):
        """
        Select k random nodes from new_nodes and connect each node to the nodes in base_nodes
        with probability p.  
        """

        # To keep new nodes from over-writing current ones rename the new nodes starting
        # from the last node in base
        new=nx.convert_node_labels_to_integers(new,first_label=max(base.nodes())+1)
        new_nodes=new.nodes()
        base_nodes=base.nodes()
        new_base=nx.compose(base,new)

        # Shuffle base nodes for random selection
        random.shuffle(base_nodes)

        #  We take only the first k nodes from the shuffled set of new nodes. Then, with probability p, 
        # connect those nodes to all nodes in base_nodes.
        for n in base_nodes[0:k]:
            edge_test=zip(random.uniform(size=len(new_nodes)), new_nodes)
            for d,m in edge_test:
                if (d <= p):
                    new_base.add_edge(m,n)
                    
        # Makes graph fully connceted in WS way
        while nx.number_connected_components(new_base)>1:
            mc_nodes=nx.connected_component_subgraphs(new_base)[0].nodes()
            cc_nodes=nx.connected_component_subgraphs(new_base)[1].nodes()
            new_edges=list()
            for i in range(k):
                random.shuffle(mc_nodes)
                random.shuffle(cc_nodes)
                new_edges.append((mc_nodes[0], cc_nodes[0]))
            new_base.add_edges_from(new_edges)
        new_base.name=""
        return(new_base)
    
    # Node ceiling of 1,00 nodes, ensures fully connceted graph
    def node_ceiling(G):
        if G.number_of_nodes()>=100:
            return False
        else:
            return True

    # Setup GMM
    watts_strogatz_model=gmm.gmm(test_graph)
    watts_strogatz_model.set_termination(node_ceiling)
    watts_strogatz_model.set_rule(watts_strogatz_growth)
    sim_name="GMM(p["+str(p)+"])_"+watts_strogatz_model.get_base().name
    gmm.algorithms.simulate(watts_strogatz_model,tau=4, poisson=True, seed=seed, new_name=sim_name)
    
    # Run simulation
    simualted_watts_strogatz=watts_strogatz_model.get_base()
    
    # Print the results to stdout
    if verbose:
        print(nx.info(simualted_watts_strogatz))
        print("")
        
    # Return a list of simulated graphs
    return(simualted_watts_strogatz)
    
def ws_gen(n, k, p):
    """ 
    Given some parameterization n, k, p, generate a random WS network and calucualte C(p) and L(p)
    """
    G=nx.watts_strogatz_graph(n, k, p)
    while nx.number_connected_components(G)>1:
        G=nx.watts_strogatz_graph(n, k, p)
    return({'p':p, 'cc':nx.average_clustering(G), 'avg.pl':nx.average_shortest_path_length(G)})
    
def ws_calc(path):
    """
    Given a path to a file graph generated by the GMM, calucualte C(p) and L(p)
    """
    G=nx.read_graphml(path)
    file_split=path.split('_')
    return({'p':float(file_split[4]), 'cc':nx.average_clustering(G), 'avg.pl':nx.average_shortest_path_length(G)})
    
def noticeEMail(starttime):
    """Sends an email message once the script is completed"""
    runtime=datetime.now() - starttime

    fromaddr='agconway@gmail.com'
    toaddr='agconway@gmail.com'

    server=smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login('agconway','diami2435343')

    senddate=datetime.strftime(datetime.now(), '%Y-%m-%d')
    subject="Your AWS job has completed"
    m="Date: %s\r\nFrom: %s\r\nTo: %s\r\nSubject: %s\r\nX-Mailer: My-Mail\r\n\r\n" % (senddate, fromaddr, toaddr, subject)
    msg='''

    Job runtime: '''+str(runtime)

    server.sendmail(fromaddr, toaddr, m+msg)

def main():
    starttime=datetime.now()
    """
    1. Generate a set of Watts-Strogatz graphs to experiment on
    """

    # Set seed for random graph
    random_seed=851982
    random.seed(random_seed)    # Seed the generator
    
    # Base Watts-Strogatz parameterization
    n_ws=100
    k_ws=3
    
    # Create a search space over probability of re-wiring and the size of the base structure
    probs=[.0001, .00025, .00075, .001, .0025, .0075, .01, .025, .075, .1, .25, .75, 1]
    
    """
    2. We now perform a grid-search over the space for probability of re-wiring a tie in the Watts-Strogatz
    model, and the size of the base structure from which the GMM will simlate a Watts-Strogatz netwotk
    using the above growth rule.
    
    Watts-Strogatz use average path length and clustering coeffecient to measure the results of their 
    model, so these metrics will be used to compare the GMM simualtions versus the networks produced
    using the Watts-Strogatz model.
    """
    
    # Number of full iterations over probabilty space
    num_iterations=20  
    
    # Run simulations and output
    graph_id=0
    for i in xrange(num_iterations):
        for p in probs:
            print("Iteration: "+str(graph_id))
            test_graph=nx.watts_strogatz_graph(20, k_ws, p)
            gmm_simulation=watts_strogatz_simulation(test_graph, k=k_ws, p=p, seed=random_seed, verbose=False)
            nx.write_graphml(gmm_simulation, "data/simulated/"+str(graph_id)+"_watts_strogatz_graph_"+str(p)+"_.graphml")
            graph_id+=1
            del gmm_simulation
            del test_graph  
    
    # Get base WS data and calculate C(p) and L(p)
    ws_data=list()
    for i in xrange(num_iterations):
        ws_data.extend(map(lambda p: ws_gen(n_ws, k_ws, p), probs))

    # Output results as a CSV
    csv_path="ws_df.csv"
    writer=csv.DictWriter(open(csv_path, "w"), fieldnames=ws_data[0].keys())
    for row in ws_data:
        writer.writerow(row)

    # Now calculate same statistics for GMM graphs
    dir_path="data/simulated/"
    files=os.listdir(dir_path)
    ws_sims=list()
    for f in files[1:]:
        ws_sims.append(ws_calc(dir_path+f))


    # Output results as CSV
    # Output results as a CSV
    sims_path="sims_df.csv"
    sim_writer=csv.DictWriter(open(sims_path, "w"), fieldnames=ws_sims[0].keys())
    for row in ws_sims:
        sim_writer.writerow(row)

    # Send email notification
    noticeEMail(starttime)
    
    

if __name__ == '__main__':
    main()

