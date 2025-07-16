import requests
import time
import json
from collections import deque
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network

def build_wiki_tree(api_url, start_title, max_depth=3):
    cache = {}
    root = {'title': start_title, 'children': []}
    
    # BFS queue: (node, depth, path_set)
    queue = deque([(root, 0, set([start_title]))])
    
    while queue:
        node, depth, path_set = queue.popleft()
        if depth >= max_depth:
            continue
        
        resolved_title, links = get_links_from_api(api_url, node['title'], cache)
        node['title'] = resolved_title  # Update to resolved title
        
        for link in links:
            # Skip pages that would create a cycle in this branch
            if link in path_set:
                continue
                
            child = {'title': link, 'children': []}
            node['children'].append(child)
            
            # Prepare new path set for the child branch
            new_path_set = set(path_set)
            new_path_set.add(link)
            queue.append((child, depth + 1, new_path_set))
    
    return root

def get_links_from_api(api_url, page_title, cache, delay=0.5):
    if page_title in cache:
        return cache[page_title]
    
    time.sleep(delay)  # Be polite to the server
    params = {
        'action': 'query',
        'titles': page_title,
        'prop': 'links',
        'pllimit': 20,        # Increase limit for more connections
        'format': 'json',
        'redirects': 1        # Automatically resolve redirects
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching '{page_title}': {e}")
        cache[page_title] = (page_title, [])
        return page_title, []
    
    if 'error' in data:
        print(f"API error for '{page_title}': {data['error']}")
        cache[page_title] = (page_title, [])
        return page_title, []
    
    pages = data['query']['pages']
    
    page_id = next(iter(pages))
    page_info = pages[page_id]
    
    if page_id == -1 or 'missing' in page_info:
        print(f"Page '{page_title}' does not exist")
        cache[page_title] = (page_title, [])
        return page_title, []
    
    resolved_title = page_info['title']
    links = [link['title'] for link in page_info.get('links', [])]
    
    cache[page_title] = (resolved_title, links)
    if resolved_title != page_title and resolved_title not in cache:
        cache[resolved_title] = (resolved_title, links)
    
    return resolved_title, links

def get_page_content(api_url, page_title, cache, delay=0.5):
    
    if page_title in cache:
        return None #cache[page_title]['content']
    
    time.sleep(delay)  # Be polite to the server
    params = {
        'action': 'parse',
        'page': page_title,
        'prop': 'wikitext',
        # 'title' : page_title,
        # 'text': page_title,
        # 'contentmodel': 'wikitext',
        # 'prop': 'text',
        #'explaintext': True,  # Get plain text extracts
        'format': 'json',
        'redirects': 1        # Automatically resolve redirects
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching content for '{page_title}': {e}")
        return ""
    
    # print(data['parse'].keys())
    # print(data['parse']['title'])
    # print(data['parse']['pageid'])
    # print(data['parse']['wikitext'])
    #pages = data['query']['pages']
    if "parse" in data:
        page_title = data['parse']['title']
        page_id = data['parse']['pageid']
        content = data['parse']['wikitext']["*"]
    else:
        print(f"Page '{page_title}' does not exist")
        print("page data not found")
        return ""
    
    return content

def build_wiki_graph(api_url, start_title, max_depth=3):
    cache = {}
    content_cache = {}
    G = nx.Graph()
    visited = set()
    enqueued = set([start_title])
    queue = deque([(start_title, 0)])
    
    while queue:
        current_title, depth = queue.popleft()
        if current_title in visited:
            continue
        
        content = get_page_content(api_url, current_title, cache)
        if content:
            content_cache[current_title] = content

        try:    
            resolved_title, links = get_links_from_api(api_url, current_title, cache)
        except Exception as e:
            print("error unpacking data \n {e}")
            print("what the function returned:")
            print(get_links_from_api(api_url, current_title, cache))
        
        visited.add(current_title)
        G.add_node(resolved_title, title=resolved_title)
        
        for link in links:
            # Add edge even if we don't traverse the link
            G.add_node(link, title=link)
            G.add_edge(resolved_title, link)
            
            # Only traverse new links within depth limit
            if depth + 1 < max_depth and link not in enqueued:
                enqueued.add(link)
                queue.append((link, depth + 1))
    
    return G,content_cache

def visualize_graph(G, output_file='wiki_graph.html'):
    net = Network(height='800px', width='100%', notebook=False, cdn_resources='in_line')
    net.from_nx(G)
    
    # Customize visualization
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": 200,
          "centralGravity": 0.001,
          "springLength": 200
        },
        "minVelocity": 0.75,
        "solver": "forceAtlas2Based"
      }
    }
    """)
    
    #// Save the graph with UTF-8 encoding
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write(net.generate_html())  # Ensure it's using the generate_html method
    
    
    #net.save_graph(output_file)
    return output_file

# Example usage
if __name__ == "__main__":
    wiki_name = "thedivision"  # Replace with your Fandom wiki name
    start_page = "Tom_Clancy's_The_Division_2"
    api_url = f"https://{wiki_name}.fandom.com/api.php"
    # tree = build_wiki_tree(api_url, start_page, max_depth=3)
    # print(tree)
    # Build the graph
    graph,content = build_wiki_graph(api_url, start_page, max_depth=3)
    #Save graph data
    with open('wiki_graph_data.json', 'w') as f:
        json.dump(nx.node_link_data(graph), f, indent=2)
    
    with open("wiki_content.json","w") as f:
        json.dump(content, f, indent=2)
    # Generate visualization
    output_file = visualize_graph(graph)
    print(f"Interactive graph saved to {output_file}")
    print(f"Graph data saved to wiki_graph_data.json")
    
    # Optional: Simple matplotlib visualization
    plt.figure(figsize=(20, 20))
    nx.draw(graph, with_labels=True, font_size=8, node_size=50)
    plt.savefig('wiki_graph.png', dpi=300)
    print("Static image saved to wiki_graph.png")
