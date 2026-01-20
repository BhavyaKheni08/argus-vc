from langgraph.graph import StateGraph, START, END

from src.modules.nodes import (
    AgentState,
    router_node,
    sherlock_node,
    researcher_node,
    cfo_node,
    critic_node,
    writer_node
)

# Initialize the graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("router", router_node)
workflow.add_node("sherlock", sherlock_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("cfo", cfo_node)
workflow.add_node("critic", critic_node)
workflow.add_node("writer", writer_node)

# Define Edges
# Start -> Router
workflow.add_edge(START, "router")

# Router -> Parallel Agents (Fan Out)
workflow.add_edge("router", "sherlock")
workflow.add_edge("router", "researcher")
workflow.add_edge("router", "cfo")

# Parallel Agents -> Critic (Fan In)
# By connecting all parallel nodes to 'critic', LangGraph waits for all to complete in the current superstep
# before executing the critic node if they are in the same stage (which they are, conceptually).
workflow.add_edge("sherlock", "critic")
workflow.add_edge("researcher", "critic")
workflow.add_edge("cfo", "critic")

# Critic -> Writer
workflow.add_edge("critic", "writer")

# Writer -> End
workflow.add_edge("writer", END)

# Compile the graph
app = workflow.compile()
