# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write(
    """Choose the fruits you want in your Smoothie!
    """
)

# Input field for the name on the order
name_on_order = st.text_input('Name on Smoothie')
st.write("The name on your Smoothie will be:", name_on_order)

# Snowflake connection and session initialization
cnx = st.connection("snowflake")
session = cnx.session()

# Convert the Snowpark DataFrame to a Pandas DataFrame so we can use the LOC function
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
pd_df = my_dataframe.to_pandas()

# Display data for debugging
# st.dataframe(pd_df)  
# st.stop()  

# Multiselect for fruit ingredients
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:', 
    pd_df['FRUIT_NAME'],  # Use the Pandas DataFrame column
    max_selections=5
)

# Check if the user selected any ingredients
if ingredients_list:
    ingredients_string = ''  # Initialize empty string for ingredients

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '  # Append chosen fruit to string

        # Get the corresponding SEARCH_ON value using Pandas loc
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        # Uncomment the line below to debug the search values
        # st.write('The search value for ', fruit_chosen, ' is ', search_on, '.')

        # Fetch and display nutrition information
        st.subheader(fruit_chosen + ' Nutrition Information')
        fruityvice_response = requests.get(f"https://fruityvice.com/api/fruit/{search_on}")
        if fruityvice_response.status_code == 200:
            fv_df = st.dataframe(data=fruityvice_response.json(), use_container_width=True)
        else:
            st.write(f"Could not fetch data for {fruit_chosen}.")

    # Add the order to the database
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders (ingredients, name_on_order)
        VALUES ('{ingredients_string.strip()}', '{name_on_order}')
    """
    # Uncomment the line below to debug the insert statement
    # st.write(my_insert_stmt)

    # Button to submit the order
    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
