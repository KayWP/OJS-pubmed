#!/usr/bin/env python
# coding: utf-8

# In[34]:


from security import api_key

import requests
import json
import pandas as pd
import sys
import os


# In[5]:


import xml.etree.ElementTree as ET

def add_article_title(xml_string, ATitle):
    # Parse the XML string
    root = ET.fromstring(xml_string)

    # Iterate through each Article node
    for article_node in root.findall('.//Article'):
        # Find the VernacularTitle node
        vernacular_title_node = article_node.find('VernacularTitle')

        # Create a new ArticleTitle node
        article_title_node = ET.Element('ArticleTitle')
        article_title_node.text = ATitle

        # Get the list of child nodes of the Article node
        child_nodes = list(article_node)

        # Find the position of the VernacularTitle node
        vernacular_title_position = child_nodes.index(vernacular_title_node)

        # Insert the new ArticleTitle node after the VernacularTitle node
        article_node.insert(vernacular_title_position + 1, article_title_node)

    # Convert the modified XML back to a string
    modified_xml = ET.tostring(root).decode("utf-8")

    return modified_xml


# In[7]:


def get_vernacular_title(xml_string):
    # Parse the XML string
    root = ET.fromstring(xml_string)

    # Find the VernacularTitle node
    vernacular_title_node = root.find('.//VernacularTitle')

    # Check if the VernacularTitle node exists
    if vernacular_title_node is not None:
        # Return the text content of the VernacularTitle node
        return vernacular_title_node.text
    else:
        return None  # Return None if VernacularTitle is not found


# In[2]:


def read_xml_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            xml_string = file.read()
        return xml_string
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


# In[23]:


def retrieve_english_title(journaltitle, vernacular_title, api_key):
    response = requests.get("https://platform.openjournals.nl/"+journaltitle+"/api/v1/submissions/?apiToken="+api_key+"&status=3&searchPhrase="+vernacular_title)
    return response.json()['items'][0]['publications'][0]['fullTitle']['en_US']


# In[29]:


def rewrite_xml(xml_string, journaltitle, api_key):
    vernacular_title = get_vernacular_title(xml_string)
    english_title = retrieve_english_title(journaltitle, vernacular_title, api_key)
    return add_article_title(xml_string, english_title)
    


# In[37]:


def process_all_xml_files(input_folder, output_folder, journaltitle):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Process each XML file in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".xml"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            # Read the input XML file as a string
            with open(input_path, 'r', encoding='utf-8') as file:
                xml_string = file.read()

            # Rewrite the XML string
            modified_xml_string = rewrite_xml(xml_string, journaltitle, api_key)

            # Write the modified XML string to the output file
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(modified_xml_string)


# In[32]:


def main():
    journaltitle = input("What is the journal title? ")
    process_all_xml_files('input', 'output', journaltitle)


# In[38]:


if __name__ == "__main__":
    input_folder = 'input'
    output_folder = 'output'
    main()


# In[ ]:




