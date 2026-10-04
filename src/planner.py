from .models.graph import Graph


class Planner():

    def __init__(self, graph: Graph):
        self.graph = graph

    def plan