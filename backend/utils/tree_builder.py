from typing import List, Dict, Any, Optional

def build_process_tree(processes: List[Dict[str, Any]], risk_factors: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Build a hierarchical process tree from a flat list of processes.
    
    Args:
        processes: List of process dictionaries containing 'pid', 'ppid', 'name'
        risk_factors: Optional list of risk factors to map to processes
        
    Returns:
        Root node of the process tree (virtual root)
    """
    if not processes:
        return {"name": "No Processes Found", "children": [], "risk": "Low"}

    # 1. Create a map of PID -> Node for easy lookup
    node_map = {}
    
    # Pre-process risk factors to map by PID if possible
    pid_risks = {}
    if risk_factors:
        for factor in risk_factors:
            # check if factor has pid info (depends on implementation)
            # This is a basic implementation
            pass

    # Initialize all nodes
    for p in processes:
        # Create a clean node structure expected by frontend
        node = {
            "name": p.get("name", "Unknown"),
            "pid": p.get("pid"),
            "ppid": p.get("ppid"),
            "cmdline": p.get("cmdline", ""),
            "children": [],
            "risk": "Low",  # Default risk
            "details": {}   # Extra details
        }
        
        # Simple heuristic for risk if not provided
        name_lower = node["name"].lower()
        if name_lower in ["wcry.exe", "tasksche.exe", "mimikatz.exe", "nc.exe"]:
            node["risk"] = "Critical"
        elif name_lower in ["powershell.exe", "cmd.exe"] and node["ppid"] != explorer_pid(processes):
            # purely heuristic: cmd/powershell not from explorer (simplification)
            node["risk"] = "High" if "enc" in str(node.get("cmdline", "")).lower() else "Medium"
            
        node_map[node["pid"]] = node

    # 2. Build relationships
    # Create a virtual root to hold orphans or multiple roots
    virtual_root = {
        "name": "System Root",
        "pid": 0,
        "children": [],
        "risk": "Low"
    }
    
    # Assign children to parents
    for pid, node in node_map.items():
        ppid = node.get("ppid")
        
        # If parent exists in our map, add as child
        if ppid in node_map and ppid != pid: # prevent self-parenting loops
            node_map[ppid]["children"].append(node)
        else:
            # If parent doesn't exist (or is 0), add to virtual root
            virtual_root["children"].append(node)

    # 3. Simplify tree if virtual root has only one child (usually "System")
    if len(virtual_root["children"]) == 1:
        return virtual_root["children"][0]
        
    return virtual_root

def explorer_pid(processes):
    """Helper to find explorer.exe pid"""
    for p in processes:
        if p.get("name", "").lower() == "explorer.exe":
            return p.get("pid")
    return -1
