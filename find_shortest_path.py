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
    - Plot the route using folium module
"""

import sys
import osmnx as ox
import networkx as nx
from shapely.geometry import box, Point
import folium
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

def find_length_and_time(G, travel_length, travel_time):
    try:
        route_length = int(sum(ox.utils_graph.route_to_gdf(G, travel_length, "length")["length"]))
        route_time = int(sum(ox.utils_graph.route_to_gdf(G, travel_time, "travel_time")["travel_time"]))
    except Exception as e:
        print(f'Error: {e}')
    return route_length, route_time

def route_plotting(G, origin_loc, destination_loc, travel_length, travel_time):
    """Plot the shortest path between two addresses."""
    if travel_length or travel_time:
        # Plot the route on a Folium map with travel time and length
        m = ox.plot_route_folium(G, travel_length, route_map=folium.Map(), popup_attribute='name') #name is the street name
        folium.Marker(origin_loc, popup='Start').add_to(m)
        folium.Marker(destination_loc, popup='End').add_to(m)
        folium.Popup(f'Travel Time: {travel_time} minutes, Travel Length: {travel_length} meters').add_to(m)
    return m


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
    origin_loc = (orig_x, orig_y)
    destination_loc = (dest_x, dest_y)
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
    # find route length and route time
    route_length, route_time = find_length_and_time(G, travel_length, travel_time)
    print(f"Shortest travel length:{(route_length * 0.000621): .1f} miles and takes {(route_time/60 +0.5): .1f} minutes") 
    # plot route map
    route_map = route_plotting(G, origin_loc, destination_loc, travel_length, travel_time)
    # Save the map to an HTML file
    route_map.save('shortest_path_map.html')
    print('Done')
    return route_map


if __name__ == "__main__":
    route_map=main()


# plot the webmap
route_map
