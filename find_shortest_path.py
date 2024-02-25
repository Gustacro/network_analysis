#!/usr/bin/python
# utf-8
"""
Title : Shortest path from A to B
Objective: Find the shortest possible time and path from A to B locations
Date: 021182024

Steps:
    - Get start and end location addresses from user input
    - Geocode the addresses via "geopy" python module, it's also possible via Nominatum, or HERE API
    - Plot it on a map to get an idea using "folium" module
    - Find shortest route between locations using OpenRouteService.org api
    - Plot the route on folium module
"""

import sys
import osmnx as ox
import networkx as nx
from shapely.geometry import box, Point
ox.config(use_cache=True, log_console=True)

def geocode(address):
    """Geocode an address using OSMnx."""
    try:
        x, y = ox.geocode(address)
    except Exception as e:
        print(f'Error: {str(e)}')
        return None, None
    return x, y

def boundary_constructor(orig_x, orig_y, dest_x, dest_y):
    """Create a bounding box around two points."""
    boundary_box = Point(orig_y, orig_x).buffer(0.001).union(Point(dest_y, dest_x).buffer(0.001)).bounds
    minx, miny, maxx, maxy = boundary_box
    bbox = box(*[minx, miny, maxx, maxy])
    return bbox

def getting_osm(bbox, network_type, truncate_edges):
    """Retrieve OSM data (roads, edges, nodes) for a given bounding box and network type."""
    G = ox.graph_from_polygon(bbox, retain_all=False, network_type=network_type, truncate_by_edge=truncate_edges)
    # hwy_speed = {'primary': 64} # If fixed speed is needed or missed it, add hwy_ speed as *param in add_edge_speeds() function
    G = ox.add_edge_speeds(G) # <- add here hwy_speed
    G = ox.add_edge_travel_times(G)
    roads = ox.graph_to_gdfs(G, nodes=False, edges=True)
    return G, roads

def find_closest_node(G, lat, lng, distance):
    """Find the closest node in a graph to a given latitude and longitude."""
    node_id, dist_to_loc = ox.distance.nearest_nodes(G, X=lat, Y=lng, return_dist=distance)
    return node_id, dist_to_loc

def shortest_path(G, orig_node_id, dest_node_id, weight):
    """Find the shortest path between two nodes in a graph."""
    try:
        route = ox.shortest_path(G, orig_node_id, dest_node_id, weight=weight)
    except nx.NetworkXNoPath as e:
        print(f"No path found between {orig_node_id} and {dest_node_id}")
        print(e)
    return route

def route_plotting(G, travel_length, travel_time):
    """Plot the shortest path lenght and shortest path time."""
    if travel_length and travel_time:
        fig, ax = ox.plot_graph_routes(
            G,
            routes=[travel_length, travel_time],
            route_colors=["r", "y"],
            route_linewidth=6,
            node_size=0
        )
    elif travel_length:
        ox.plot_route_folium(G, travel_length, popup_attribute='length')
    elif travel_time:
        ox.plot_route_folium(G, travel_time, popup_attribute='travel_time')


def main():
    # User address input
    origin_address = str(input('Enter the origin address: '))
    destination_address = str(input('Enter the destination adddress: '))
    # Geocode addresses
    orig_x, orig_y = geocode(origin_address)
    dest_x, dest_y = geocode(destination_address)
    # Check if geocoding was successful
    if not all([orig_x, orig_y, dest_x, dest_y]):
        print("Unable to geocode one or both addresses. Exiting...")
        sys.exit()
    # Create bounding box
    bbox = boundary_constructor(orig_x, orig_y, dest_x, dest_y) 
    # Retrieve OSM data
    G, roads = getting_osm(bbox, network_type='drive', truncate_edges='True')
    # Find closest node
    orig_node_id, dist_to_orig = find_closest_node(G, orig_y, orig_x, True)
    dest_node_id, dist_to_dest = find_closest_node(G, dest_y, dest_x, True)
    # find shortest path
    travel_length = shortest_path(G, orig_node_id, dest_node_id, weight='length')
    travel_time = shortest_path(G, orig_node_id, dest_node_id, weight='travel_time')
    print(f"Shortest travel length:{travel_length: .2f} meters and takes {round(travel_time)} minutes") # NOT SURE IF CORRECT (travel_time/1.6 only for walk network type) 
    # plot routes
    route_plotting(G, travel_length, travel_time)


if __name__ == "__main__":
    main()
