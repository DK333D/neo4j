import streamlit as st
from neo4j import Driver, GraphDatabase
from pyvis.network import Network
import pandas as pd
import uuid  
from enum import Enum
import secrets
import time

# Function to generate a secure token
def generate_token():
    return secrets.token_hex(32)

# Function to check token expiration (optional)
def is_token_valid(token):
    if token is None:
        return False
    token_parts = token.split(":")
    if len(token_parts) != 2:
        return False
    try:
        token_creation_time = int(token_parts[1])
        current_time = int(time.time())
        # Token valid for 1 hour (3600 seconds)
        return current_time - token_creation_time < 3600
    except ValueError:
        return False

# Logout function
def logout():
    st.session_state["token"] = None
    st.sidebar.info("You have been logged out!")

# Get data
def run_query(driver: Driver, query):
    try:
        with driver.session() as session:
            result = session.run(query)
            return result.data()
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return []

# Add Aircraft, Drone lub Soldier with UUID
def add_entity_with_uuid(driver: Driver, entity_type, name):
    entity_uuid = str(uuid.uuid4())
    query = f"CREATE (n:{entity_type} {{name: '{name}', uuid: '{entity_uuid}'}}) RETURN n.name AS Name, n.uuid AS UUID"
    try:
        with driver.session() as session:
            result = session.run(query)
            return result.data()
    except Exception as e:
        st.error(f"Error adding {entity_type}: {e}")
        return []

# Add drones with brand and unique name
def add_drone_with_unique_name_and_brand(driver: Driver, aircraft_name, drone_name, soldier_name, brand):
    existing_drone_query = f"""
    MATCH (d:Drone {{name: '{drone_name}'}})
    RETURN d.name AS Drone
    """
    existing_drone = run_query(driver, existing_drone_query)
    
    if existing_drone:
        st.error(f"Drone with name '{drone_name}' already exists.")
        return []

    drone_uuid = str(uuid.uuid4())
    query = f"""
    CREATE (d:Drone {{name: '{drone_name}', uuid: '{drone_uuid}', brand: '{brand}'}})
    WITH d
    MATCH (a:Aircraft {{name: '{aircraft_name}'}})
    MATCH (s:Soldier {{name: '{soldier_name}'}})
    CREATE (s)-[:RESPONSIBLE_FOR]->(d)
    CREATE (a)-[:HAS]->(d)
    RETURN d.name AS Drone, d.uuid AS UUID, d.brand AS Brand;

    """
    try:
        with driver.session() as session:
            result = session.run(query)
            return result.data()
    except Exception as e:
        st.error(f"Error adding drone: {e}")
        return []

# Add relationship
def add_relationship(driver: Driver, aircraft, drone, relationship_type):
    query = f"""
    MATCH (a:Aircraft {{name: '{aircraft}'}}), (d:Drone {{name: '{drone}'}})
    CREATE (a)-[:{relationship_type}]->(d)
    RETURN a.name AS Aircraft, d.name AS Drone, '{relationship_type}' AS Relationship
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            return result.data()
    except Exception as e:
        st.error(f"Error adding relationship: {e}")
        return []

# Create Aircrafts and Drones Network
def create_aircraft_drone_network(data, title):
    net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")
    net.barnes_hut()

    for row in data:
        net.add_node(row["Aircraft"], label=row["Aircraft"], color="blue")
        net.add_node(row["Drone"], label=row["Drone"], color="green")
        net.add_edge(row["Aircraft"], row["Drone"], title=row.get("Relationship", "CONNECTED_TO"))

    net.repulsion(node_distance=120, central_gravity=0.33, spring_length=110, spring_strength=0.10, damping=0.95)
    return net

# Create Soldiers and Drones Network
def create_soldier_drone_network(data, title):
    net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")
    net.barnes_hut()

    for row in data:
        net.add_node(row["Soldier"], label=row["Aircraft"], color="blue")
        net.add_node(row["Drone"], label=row["Drone"], color="green")
        net.add_edge(row["Soldier"], row["Drone"], title=row.get("Relationship", "CONNECTED_TO"))

    net.repulsion(node_distance=120, central_gravity=0.33, spring_length=110, spring_strength=0.10, damping=0.95)
    return net

def create_drones_network(data, title):
    net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")
    net.barnes_hut()

    for row in data:
        net.add_node(str(row["Brand"])+"-"+str(row["Drone"]), label=row["Drone"], color="green")

    net.repulsion(node_distance=120, central_gravity=0.33, spring_length=110, spring_strength=0.10, damping=0.95)
    return net

def create_soldiers_network(data, title):
    net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")
    net.barnes_hut()

    for row in data:
        net.add_node(str(row["Name"]), label=str(row["Name"]), color="green")

    net.repulsion(node_distance=120, central_gravity=0.33, spring_length=110, spring_strength=0.10, damping=0.95)
    return net


def create_aircrafts_network(data, title):
    net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")
    net.barnes_hut()

    for row in data:
        net.add_node(str(row["Name"]), label=str(row["Name"]), color="green")

    net.repulsion(node_distance=120, central_gravity=0.33, spring_length=110, spring_strength=0.10, damping=0.95)
    return net


# Generate soldiers and drones networks
def create_soldier_drone_network(data, title):
    net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")
    net.barnes_hut()

    # Adding nodes and edges for soldiers and drones
    for row in data:
        soldier = row["Soldier"]
        drone = row["Drone"]
        # Add soldier node
        net.add_node(soldier, label=soldier, color="blue")
        # Add drone node
        net.add_node(drone, label=drone, color="green")
        # Create an edge from soldier to drone
        net.add_edge(soldier, drone, title="Responsible for", color="orange")

    net.repulsion(node_distance=150, central_gravity=0.33, spring_length=100, spring_strength=0.10, damping=0.95)

    return net

# Relation types
allowed_relationship_types = ["CONNECTED_TO", "SUPPORTS", "MONITORS"]

# Lists of Aircraft, Drones, Soldiers
def get_aircraft_names(driver):
    query = "MATCH (a:Aircraft) RETURN a.name AS Aircraft"
    data = run_query(driver, query)
    return [item["Aircraft"] for item in data]

def get_drone_names(driver):
    query = "MATCH (d:Drone) RETURN d.name AS Drone"
    data = run_query(driver, query)
    return [item["Drone"] for item in data]

def get_soldier_names(driver):
    query = "MATCH (s:Soldier) RETURN s.name AS Soldier"
    data = run_query(driver, query)
    return [item["Soldier"] for item in data]

# Deletion function
def delete_entity(driver: Driver, entity_type, uuid):
    query = f"""
    MATCH (n:{entity_type} {{uuid: '{uuid}'}})
    DETACH DELETE n
    RETURN n
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            return result.data()
    except Exception as e:
        st.error(f"Error deleting {entity_type}: {e}")
        return []

# Assign soldier to drone function 
def assign_soldier_to_drone(driver: Driver, soldier_name, drone_name):
    query = f"""
    MATCH (s:Soldier {{name: '{soldier_name}'}}), (d:Drone {{name: '{drone_name}'}})
    CREATE (s)-[:RESPONSIBLE_FOR]->(d)
    RETURN s.name AS Soldier, d.name AS Drone
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            return result.data()
    except Exception as e:
        st.error(f"Error assigning soldier to drone: {e}")
        return []

# Display soldiers and drones relationships
def view_soldiers_and_drones(driver):
    query = """
    MATCH (s:Soldier)-[:RESPONSIBLE_FOR]->(d:Drone)
    RETURN s.name AS Soldier, d.name AS Drone, d.uuid AS DroneUUID
    """
    data = run_query(driver, query)
    return data

# Function to fetch the counts from Neo4j
def get_statistics(driver: Driver):
    with driver.session() as session:
        # Cypher query to count the aircraft, soldiers, and drones nodes
        aircraft_query = "MATCH (a:Aircraft) RETURN COUNT(a) AS count"
        soldier_query = "MATCH (s:Soldier) RETURN COUNT(s) AS count"
        drone_query = "MATCH (d:Drone) RETURN COUNT(d) AS count"

        # Execute queries and get counts
        aircraft_count = session.run(aircraft_query).single()["count"]
        soldier_count = session.run(soldier_query).single()["count"]
        drone_count = session.run(drone_query).single()["count"]

        return aircraft_count, soldier_count, drone_count
