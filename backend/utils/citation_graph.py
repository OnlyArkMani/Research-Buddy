import networkx as nx
import plotly.graph_objects as go
from typing import List, Dict
import json

class CitationGraphVisualizer:
    """Create interactive citation network visualizations"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def add_papers(self, papers: List[Dict]):
        """Add papers to citation graph"""
        for paper in papers:
            paper_id = paper.get('id', paper.get('title'))
            self.graph.add_node(
                paper_id,
                title=paper.get('title', 'Unknown'),
                authors=paper.get('authors', 'Unknown'),
                year=paper.get('year', 0),
                citations=paper.get('citations', 0)
            )
    
    def add_citations(self, source_id: str, target_ids: List[str]):
        """Add citation relationships"""
        for target_id in target_ids:
            self.graph.add_edge(source_id, target_id)
    
    def generate_plotly_graph(self) -> str:
        """Generate interactive Plotly visualization"""
        # Calculate layout
        pos = nx.spring_layout(self.graph, k=0.5, iterations=50)
        
        # Create edge traces
        edge_x = []
        edge_y = []
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Create node traces
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        
        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            node_data = self.graph.nodes[node]
            node_text.append(f"{node_data['title']}<br>Citations: {node_data['citations']}")
            node_size.append(min(10 + node_data['citations'] / 10, 50))
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                size=node_size,
                color='lightblue',
                line=dict(width=2, color='darkblue')
            )
        )
        
        # Create figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title='Citation Network',
                showlegend=False,
                hovermode='closest',
                margin=dict(b=0, l=0, r=0, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
        )
        
        return fig.to_html(include_plotlyjs='cdn')
    
    def get_most_influential_papers(self, top_n: int = 5) -> List[Dict]:
        """Get most cited/connected papers"""
        pagerank = nx.pagerank(self.graph)
        sorted_papers = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for paper_id, score in sorted_papers[:top_n]:
            node_data = self.graph.nodes[paper_id]
            results.append({
                'id': paper_id,
                'title': node_data['title'],
                'influence_score': score,
                'citations': node_data['citations']
            })
        
        return results