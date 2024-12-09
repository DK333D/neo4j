import streamlit as st
from neo4j import GraphDatabase
from pyvis.network import Network
import pandas as pd
import uuid  
from enum import Enum
import secrets
import time
import utils

# Load the password from secrets
APP_PASSWORD = st.secrets["App"]["PASSWORD"]

# Initialize session state
if "token" not in st.session_state:
    st.session_state["token"] = None

# Authentication flow
if st.session_state["token"] is None or not utils.is_token_valid(st.session_state["token"]):
    st.title("Login")
    password_input = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if password_input == APP_PASSWORD:
            # Generate a new token and store with timestamp
            token = f"{utils.generate_token()}:{int(time.time())}"
            st.session_state["token"] = token
            st.success("Login successful!")
        else:
            st.error("Incorrect password.")

if st.session_state["token"] is not None and utils.is_token_valid(st.session_state["token"]):


    st.sidebar.button("Logout", on_click=utils.logout)
    # Connect to the database
    uri = st.secrets["AuraDB"]["URI"]
    username = st.secrets["AuraDB"]["USERNAME"]
    password = st.secrets["AuraDB"]["PASSWORD"]

    # Neo4j connection
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
    except Exception as e:
        st.error(f"Error connecting to Neo4j: {e}")
        st.stop()



    # User Interface in Streamlit
    st.title("Military Aircraft, Drone, and Soldier Network")

    class Action(Enum):
        STATISTICS = "Statistics"
        AIRCRAFTS = "Aircrafts"
        SOLDIERS = "Soldiers"
        DRONES = "Drones"
        AIRCRAFT_AND_DRONES_RELATIONSHIPS = "Aircraft and Drones Relationships"
        SOLDIERS_AND_DRONES_RELATIONSHIPS = "Soldiers and Drones Relationships"
        DELETE_ENTITY = "Delete Entity"

    # Get the options from the Enum for the radio button
    options = [action.value for action in Action]

    # Create the radio button in the sidebar
    option = st.sidebar.radio("Choose an action:", options)

    if option == Action.STATISTICS.value:
        
        # Get statistics from the database
        aircraft_count, soldier_count, drone_count = utils.get_statistics(driver)

        # Display an image on the front page
        st.image("images/gremlins-deployment.jpg", caption="source: https://breakingdefense.com/2021/11/a-mothership-finally-recovers-darpas-gremlins-drone-but-its-not-all-good-news/", use_container_width=True)
        
        # Display statistics
        st.subheader("Current Statistics:")
        st.write(f"Total Aircraft: {aircraft_count}")
        st.write(f"Total Soldiers: {soldier_count}")
        st.write(f"Total Drones: {drone_count}")

    elif option == Action.AIRCRAFTS.value:
        st.subheader("Add a New Aircraft")

        # Add a new aircraft
        aircraft_name = st.text_input("Enter Aircraft Name")

        if st.button("Add an Aircraft"):
            if aircraft_name:
                result = utils.add_entity_with_uuid(driver, "Aircraft", aircraft_name)
                if result:
                    st.success(f"Aircraft '{aircraft_name}' added successfully.")
                else:
                    st.warning(f"Failed to add Aircraft '{aircraft_name}'.")
            else:
                st.error("Please provide a name for the Aircraft.")
        
        # Fetch all aircraft and display them in a table
        query_aircraft = """
        MATCH (a:Aircraft)
        RETURN a.name AS Name, a.uuid AS UUID
        """
        aircraft = utils.run_query(driver, query_aircraft)

        if aircraft:
            # Convert aircraft data to a DataFrame for easier handling
            aircraft_df = pd.DataFrame(aircraft)
            
            # Create a list of options showing both aircraft name and UUID
            aircraft_options = [
                f"{name} (UUID: {uuid})" for name, uuid in zip(aircraft_df['Name'], aircraft_df['UUID'])
            ] if not aircraft_df.empty else []
            
            # Select aircraft to delete based on name and UUID
            st.subheader("Delete an Aircraft")
            aircraft_to_delete = st.selectbox("Select Aircraft to Delete", aircraft_options)
            
            # Extract the aircraft name and UUID from the selected option
            if aircraft_to_delete:
                selected_aircraft_name = aircraft_to_delete.split(" (UUID: ")[0]
                selected_aircraft_uuid = aircraft_to_delete.split(" (UUID: ")[1].strip(")")

            if st.button("Delete Aircraft"):
                if aircraft_to_delete:
                    # Construct the query to delete by both UUID and name
                    delete_query = f"""
                    MATCH (a:Aircraft {{name: '{selected_aircraft_name}', uuid: '{selected_aircraft_uuid}'}})
                    DETACH DELETE a
                    """
                    utils.run_query(driver, delete_query)
                    st.success(f"Aircraft with name '{selected_aircraft_name}' and UUID '{selected_aircraft_uuid}' has been deleted.")
                else:
                    st.error("Please select an aircraft to delete.")
            
            # Refresh the data after deletion
            st.subheader("All Aircrafts in the Database")

            aircraft = utils.run_query(driver, query_aircraft)
            aircraft_df = pd.DataFrame(aircraft)
            st.write(aircraft_df)
            
            # Render the graph
            graph = utils.create_aircrafts_network(aircraft, "Aircrafts")
            graph.save_graph("aircrafts.html")
            st.components.v1.html(open("aircrafts.html", "r").read(), height=500)
        else:
            st.warning("No aircrafts found in the database.")
        
        # Display image
        st.image("images/aircraft.jpg", caption="source: https://www.fliteline.com/aircraft-guide/special-aircrafts/sprayer", use_container_width=True)


    elif option == Action.SOLDIERS.value:
        st.subheader("Add a New Soldier")

        # Add a new soldier
        soldier_name = st.text_input("Enter Soldier Name")
        
        if st.button("Add a soldier"):
            if soldier_name:
                result = utils.add_entity_with_uuid(driver, "Soldier", soldier_name)
                if result:
                    st.success(f"Soldier '{soldier_name}' added successfully.")
                else:
                    st.warning(f"Failed to add Soldier '{soldier_name}'.")
            else:
                st.error("Please provide a name for the Soldier.")
        
        # Fetch all soldiers and display them in a table
        query_soldier = """
        MATCH (s:Soldier)
        RETURN s.name AS Name, s.uuid AS UUID
        """
        soldier = utils.run_query(driver, query_soldier)
        if soldier:
            # Convert soldiers to DataFrame for easier handling
            soldier_df = pd.DataFrame(soldier)
            
            # Create a list of options showing both soldier name and UUID
            soldier_options = [
                f"{name} (UUID: {uuid})" for name, uuid in zip(soldier_df['Name'], soldier_df['UUID'])
            ] if not soldier_df.empty else []
            
            # Select soldier to delete based on name and UUID
            st.subheader("Delete a Soldier")
            soldier_to_delete = st.selectbox("Select Soldier to Delete", soldier_options)
            
            # Extract the soldier name and UUID from the selected option
            if soldier_to_delete:
                selected_soldier_name = soldier_to_delete.split(" (UUID: ")[0]
                selected_soldier_uuid = soldier_to_delete.split(" (UUID: ")[1].strip(")")

            if st.button("Delete Soldier"):
                if soldier_to_delete:
                    # Construct the query to delete by both UUID and name
                    delete_query = f"""
                    MATCH (s:Soldier {{name: '{selected_soldier_name}', uuid: '{selected_soldier_uuid}'}})
                    DETACH DELETE s
                    """
                    utils.run_query(driver, delete_query)
                    st.success(f"Soldier with name '{selected_soldier_name}' and UUID '{selected_soldier_uuid}' has been deleted.")
                else:
                    st.error("Please select a soldier to delete.")

            
        else:
            st.warning("No soldiers found in the database.")

        # Refresh the data after deletion
        st.subheader("All Soldiers in the Database")
        soldier = utils.run_query(driver, query_soldier)
        soldier_df = pd.DataFrame(soldier)
        st.write(soldier_df)
        # Render the graph
        graph = utils.create_soldiers_network(soldier, "Soldiers")
        graph.save_graph("soldiers.html")
        st.components.v1.html(open("soldiers.html", "r").read(), height=500)
        
        st.image("images/soldier.jpg", caption="source: https://www.defense.gov/Multimedia/Photos/igphoto/2002889537/", use_container_width=True)

    elif option == Action.DRONES.value:
        st.subheader("Add a New Drone")

        aircraft_names = utils.get_aircraft_names(driver)
        soldier_names = utils.get_soldier_names(driver)

        if not aircraft_names:
            st.error("No Aircraft found in the database. Add Aircraft first.")
        if not soldier_names:
            st.error("No Soldiers found in the database. Add Soldiers first.")
        
        # Adding a drone section
        aircraft_name = st.selectbox("Select Aircraft", aircraft_names)
        drone_name = st.text_input("Enter Drone Name")
        soldier_name = st.selectbox("Select Soldier", soldier_names)
        brand = st.text_input("Enter Drone Brand")

        if st.button("Add a drone"):
            if drone_name and soldier_name and brand:
                result = utils.add_drone_with_unique_name_and_brand(driver, aircraft_name, drone_name, soldier_name, brand)
                if result:
                    st.success(f"Drone '{drone_name}' of brand '{brand}' added and assigned to Soldier '{soldier_name}'.")
                else:
                    st.warning(f"Failed to add drone '{drone_name}'.")
            else:
                st.error("Please provide all fields.")

        # Fetch all drones and display them in a table
        query_drones = """
        MATCH (d:Drone)
        RETURN d.name AS Drone, d.uuid AS UUID, d.brand AS Brand
        """
        drones = utils.run_query(driver, query_drones)
        if drones:
            drones_df = pd.DataFrame(drones)
            
            # Create a list of options showing both drone name and UUID
            drone_options = [
                f"{drone} (UUID: {uuid})" for drone, uuid in zip(drones_df['Drone'], drones_df['UUID'])
            ] if not drones_df.empty else []
            
            # Select drone to delete based on UUID
            st.subheader("Delete a Drone")
            drone_to_delete = st.selectbox("Select Drone to Delete", drone_options)
            
            # Extract the drone name and UUID from the selected option
            if drone_to_delete:
                selected_drone_name = drone_to_delete.split(" (UUID: ")[0]
                selected_drone_uuid = drone_to_delete.split(" (UUID: ")[1].strip(")")

            if st.button("Delete Drone"):
                if drone_to_delete:
                    # Construct the query to delete by both UUID and name
                    delete_query = f"""
                    MATCH (d:Drone {{name: '{selected_drone_name}', uuid: '{selected_drone_uuid}'}})
                    DETACH DELETE d
                    """
                    utils.run_query(driver, delete_query)
                    st.success(f"Drone with name '{selected_drone_name}' and UUID '{selected_drone_uuid}' has been deleted.")
                else:
                    st.error("Please select a drone to delete.")
            # Render the graph
        else:
            st.warning("No drones found in the database.")
        
        # Refresh the data after deletion
        st.subheader("All Drones in the Database")
        drone = utils.run_query(driver, query_drones)
        drones_df = pd.DataFrame(drone)
        st.write(drones_df)
        graph = utils.create_drones_network(drones, "Drones")
        graph.save_graph("drones.html")
        st.components.v1.html(open("drones.html", "r").read(), height=500)
        
        st.image("images/gremlins-x-61.jpg", caption="source: https://en.wikipedia.org/wiki/Dynetics_X-61_Gremlins", use_container_width=True)


    elif option == Action.AIRCRAFT_AND_DRONES_RELATIONSHIPS.value:

        st.subheader("Relationships")

        # Dropdown for existing aircraft and drone names
        aircraft_names = utils.get_aircraft_names(driver)
        drone_names = utils.get_drone_names(driver)

        if not aircraft_names:
            st.error("No Aircraft found in the database. Add Aircraft first.")
        if not drone_names:
            st.error("No Drones found in the database. Add Drones first.")

        selected_aircraft = st.selectbox("Select Aircraft", aircraft_names, index=0 if aircraft_names else -1)
        selected_drone = st.selectbox("Select Drone", drone_names, index=0 if drone_names else -1)
        relationship_type = st.selectbox("Select Relationship Type", utils.allowed_relationship_types)

        if st.button("Add a relationship"):
            if selected_aircraft and selected_drone and relationship_type:
                result = utils.add_relationship(driver, selected_aircraft, selected_drone, relationship_type)
                if result:
                    st.success(f"Relationship {relationship_type} added between {selected_aircraft} and {selected_drone}.")
                else:
                    st.warning("Failed to add relationship. Check the entity names.")
            else:
                st.error("Please provide all fields.")

        # Relationship query
        query_aircraft_drones = """
        MATCH (a:Aircraft)-[r]->(d:Drone)
        RETURN a.name AS Aircraft, d.name AS Drone, type(r) AS Relationship
        """
        relationships = utils.run_query(driver, query_aircraft_drones)

        if relationships:
            st.subheader("Relationships between Aircraft and Drones")
            st.write(pd.DataFrame(relationships))

            graph = utils.create_aircraft_drone_network(relationships, "Aircraft-Drone Relationships")
            graph.save_graph("graph.html")
            st.components.v1.html(open("graph.html", "r").read(), height=500)
        else:
            st.warning("No relationships found.")

    elif option == Action.SOLDIERS_AND_DRONES_RELATIONSHIPS.value:
        st.subheader("Assign Soldier to Drone")

        drone_names = utils.get_drone_names(driver)

        if not drone_names:
            st.error("No Drones found in the database. Add Drones first.")

        soldier_names = utils.get_soldier_names(driver)
        if not soldier_names:
            st.error("No Soldiers found in the database. Add Soldiers first.")

        soldier_name = st.selectbox("Select Soldier", soldier_names)
        drone_name = st.selectbox("Select Drone", drone_names)

        if st.button("Assign Soldier to Drone"):
            if soldier_name and drone_name:
                result = utils.assign_soldier_to_drone(driver, soldier_name, drone_name)
                if result:
                    st.success(f"Soldier '{soldier_name}' has been assigned to Drone '{drone_name}'.")
                else:
                    st.warning(f"Failed to assign Soldier to Drone '{drone_name}'.")
            else:
                st.error("Please provide both Soldier and Drone names.")

        
        # Relationship query
        query_soldiers_drones = """
        MATCH (a:Soldier)-[r]->(d:Drone)
        RETURN a.name AS Soldier, d.name AS Drone, type(r) AS Relationship
        """
        relationships = utils.run_query(driver, query_soldiers_drones)

        if relationships:
            st.subheader("Relationships between Soldier and Drones")
            st.write(pd.DataFrame(relationships))

            graph = utils.create_soldier_drone_network(relationships, "Soldier-Drone Relationships")
            graph.save_graph("graph.html")
            st.components.v1.html(open("graph.html", "r").read(), height=500)
        else:
            st.warning("No relationships found.")

    elif option == Action.DELETE_ENTITY.value:
        st.subheader("Delete Entity (Drone, Soldier, or Aircraft)")

        entity_type = st.selectbox("Select Entity Type", ["Drone", "Soldier", "Aircraft"])
        entity_uuid = st.text_input(f"Enter {entity_type} UUID")

        if st.button("Delete Entity"):
            if entity_uuid:
                result = utils.delete_entity(driver, entity_type, entity_uuid)
                if result:
                    st.success(f"{entity_type} with UUID {entity_uuid} deleted successfully.")
                else:
                    st.warning(f"Failed to delete {entity_type} with UUID {entity_uuid}.")
            else:
                st.error(f"Please provide a UUID for the {entity_type}.")

    # Close the connection with Neo4j
    driver.close()