from lab2_ejercicioc import * 

from collections import deque
import networkx as nx
import matplotlib.pyplot as plt

class State:
    """Represents a state in the NFA"""
    def __init__(self, label=None):
        self.label = label  
        self.transitions = {}  
        self.epsilon_transitions = set() 
        self.id = id(self)
    
    def __repr__(self):
        return f"State({self.label})"

class NFA:
    """Represents an NFA with start and accept states"""
    def __init__(self, start, accept):
        self.start = start
        self.accept = accept
    
    @staticmethod
    def from_regex_node(node):
        """Convert a regex parse tree to NFA using Thompson's construction"""
        if node.value == '|':
            nfa_left = NFA.from_regex_node(node.left)
            nfa_right = NFA.from_regex_node(node.right)
            
            start = State('union_start')
            accept = State('union_accept')
            
            start.epsilon_transitions.add(nfa_left.start)
            start.epsilon_transitions.add(nfa_right.start)
            
            nfa_left.accept.epsilon_transitions.add(accept)
            nfa_right.accept.epsilon_transitions.add(accept)
            
            return NFA(start, accept)
        
        elif node.value == '.':
            nfa_left = NFA.from_regex_node(node.left)
            nfa_right = NFA.from_regex_node(node.right)
            
            nfa_left.accept.epsilon_transitions.add(nfa_right.start)
            
            return NFA(nfa_left.start, nfa_right.accept)
        
        elif node.value == '*':
            nfa_child = NFA.from_regex_node(node.left)
            
            start = State('star_start')
            accept = State('star_accept')
            
            start.epsilon_transitions.add(nfa_child.start)
            start.epsilon_transitions.add(accept)
            
            nfa_child.accept.epsilon_transitions.add(nfa_child.start)
            nfa_child.accept.epsilon_transitions.add(accept)
            
            return NFA(start, accept)
        
        elif node.value == '+':
            nfa_child = NFA.from_regex_node(node.left)
            
            start = State('plus_start')
            accept = State('plus_accept')
            
            start.epsilon_transitions.add(nfa_child.start)
            
            nfa_child.accept.epsilon_transitions.add(nfa_child.start)
            nfa_child.accept.epsilon_transitions.add(accept)
            
            return NFA(start, accept)
        
        elif node.value == '?':
            nfa_child = NFA.from_regex_node(node.left)
            
            start = State('optional_start')
            accept = State('optional_accept')
            
            start.epsilon_transitions.add(nfa_child.start)
            start.epsilon_transitions.add(accept)
            
            nfa_child.accept.epsilon_transitions.add(accept)
            
            return NFA(start, accept)
        
        else:
            start = State('char_start')
            accept = State('char_accept')
            start.transitions[node.value] = {accept}
            return NFA(start, accept)
    
    def simulate(self, input_string):
        """Simula el automata"""
        current_states = self._epsilon_closure({self.start})
        
        for char in input_string:
            next_states = set()
            for state in current_states:
                if char in state.transitions:
                    next_states.update(state.transitions[char])
            
            current_states = self._epsilon_closure(next_states)
            
            if not current_states:
                return False
        
        return any(state == self.accept for state in current_states)
    
    def _epsilon_closure(self, states):
        """Epsilon cerradura"""
        closure = set(states)
        stack = list(states)
        
        while stack:
            state = stack.pop()
            for eps_state in state.epsilon_transitions:
                if eps_state not in closure:
                    closure.add(eps_state)
                    stack.append(eps_state)
        
        return closure
    
    def to_graph(self):
        """AFN a grafo de NetworkX"""
        G = nx.MultiDiGraph()
        visited = set()
        stack = [self.start]
        
        while stack:
            state = stack.pop()
            if state.id in visited:
                continue
            visited.add(state.id)
            
            G.add_node(state.id, label="")
            
            # Add epsilon transitions
            for eps_state in state.epsilon_transitions:
                G.add_edge(state.id, eps_state.id, label='ε')
                if eps_state.id not in visited:
                    stack.append(eps_state)
            
            # Add character transitions
            for char, targets in state.transitions.items():
                for target in targets:
                    G.add_edge(state.id, target.id, label=char)
                    if target.id not in visited:
                        stack.append(target)
        
        return G
    
    def plot(self):
        """Visualizar"""
        G = self.to_graph()
        
        pos = nx.kamada_kawai_layout(G)
        
        node_colors = []
        for node in G.nodes():
            if node == self.start.id:
                node_colors.append('lightgreen')  # Inicio
            elif node == self.accept.id:
                node_colors.append('lightcoral')  # Terminal
            else:
                node_colors.append('skyblue')  # Estado
        
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=700)
        
        edge_labels = {}
        for u, v, data in G.edges(data=True):
            edge_labels[(u, v)] = data['label']
        
        nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=20)
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

        
        plt.axis('off')
        plt.title("Visualización AFN")
        plt.show()

class RegexNode:
    """Para realizar el árbol sintáctico"""
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right
    
    def __repr__(self):
        return f"RegexNode({self.value})"

def postfix_to_tree(postfix):
    """Postfix a árbol"""
    stack = deque()
    
    for char in postfix:
        if char in ('.', '|'):  # Operadores
            right = stack.pop()
            left = stack.pop()
            stack.append(RegexNode(char, left, right))
        elif char in ('*', '+', '?'):  # Operadores unitarios
            child = stack.pop()
            stack.append(RegexNode(char, child))
        else:  # Operandos
            stack.append(RegexNode(char))
    
    if len(stack) != 1:
        raise ValueError("Postfix inválido")
    
    return stack.pop()

def regex_to_nfa(postfix_regex):
    """Postfix a AFN"""
    tree = postfix_to_tree(postfix_regex)
    return NFA.from_regex_node(tree)

# Example usage:
if __name__ == "__main__":
    filename = input("Nombre del archivo: ")
    try:
        with open(filename, 'r') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if line:  
                    try:
                        validate_regex(line)
                        postfix = shunting_yard(line)
                        print(f"Original: {line}")
                        print(f"Postfix: {postfix}")
                        nfa = regex_to_nfa(postfix)
                        nfa.plot()
                        while True:
                            ex = input("Expresión: ")
                            if ex == "":
                                break
                            print(nfa.simulate(ex))
                    except ValueError as e:
                        print(f"Expresión regular inválida: {e}")
                    print("="*50)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")