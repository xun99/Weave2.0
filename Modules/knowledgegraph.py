import IPython
from pyvis.network import Network
from knowledgebase import KB

class KG:
    """
    Visualises the knowledge graph when given knowledge base.
    """
    
    def visualise(kb, include = []):
        """
        for every entity in the input kb, a node is added
        for every relation in the kb an edge is added and labelled
        with the type of relation
        
        include: if needed, only a specific relation type will be included
        """
        net = Network(directed=True, width="700px", height="700px", bgcolor="#eeeeee", notebook = True)


        for e in kb.entities:
            net.add_node(e, shape="circle", color="#00ff1e")


        # edges
        for r in kb.relations:
            if len(include) > 0:
                if r['type'] in include:
                    net.add_edge(r["head"], r["tail"], title=r["type"], label=r["type"])


            else:
                net.add_edge(r["head"], r["tail"], title=r["type"], label=r["type"])

        # save network
        net.repulsion(
            node_distance=200,
            central_gravity=0.2,
            spring_length=200,
            spring_strength=0.05,
            damping=0.09
        )
        
        net.set_edge_smooth('dynamic')
        return net
        
