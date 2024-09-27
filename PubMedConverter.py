#!/usr/bin/env python
# coding: utf-8

# In[1]:


from dotenv import dotenv_values

import xml.etree.ElementTree as ET

import requests
import json
import pandas as pd
import sys
import os

security = dotenv_values(".env")
api_key = security.get('api_key')
journal_title = security.get('journal_title')
journal_abbreviation = security.get('journal_abbreviation')
pubmed_user = security.get('pubmed_user')
pubmed_pass = security.get('pubmed_pass')


# In[ ]:





# In[2]:


def add_article_title(xml_string, ATitle):
    # Parse the XML string
    root = ET.fromstring(xml_string)

    # Iterate through each Article node
    for article_node in root.findall('.//Article'):
        # Find the VernacularTitle node
        vernacular_title_node = article_node.find('VernacularTitle')

        if vernacular_title_node is not None:
            # Create a new ArticleTitle node
            article_title_node = ET.Element('ArticleTitle')
            article_title_node.text = ATitle

            # Get the list of child nodes of the Article node
            child_nodes = list(article_node)

            # Find the position of the VernacularTitle node
            vernacular_title_position = child_nodes.index(vernacular_title_node)

            # Insert the new ArticleTitle node after the VernacularTitle node
            article_node.insert(vernacular_title_position + 1, article_title_node)

    # Convert the modified XML tree back to a string
    return ET.tostring(root, encoding='unicode')


# In[19]:


def add_article_id_list(xml_string):
    # Parse the input XML string
    root = ET.fromstring(xml_string)
    
    # Find the AuthorList node
    author_list = root.find(".//AuthorList")
    
    # Find the DOI under ELocationID
    doi_node = root.find(".//ELocationID[@EIdType='doi']")
    doi_value = doi_node.text if doi_node is not None else None
    
    # Create the ArticleIdList element
    article_id_list = ET.Element("ArticleIdList")
    
    if doi_value:
        # Create the ArticleId element
        article_id = ET.Element("ArticleId", IdType="doi")
        article_id.text = doi_value
        
        # Append the ArticleId element to the ArticleIdList
        article_id_list.append(article_id)
    
    # We need to manually find the parent of the AuthorList node
    # This is necessary because ElementTree doesn't support getparent()
    def find_parent(root, child):
        # Traverse through all elements
        for parent in root.iter():
            # Look for child within this parent
            if child in list(parent):
                return parent
        return None
    
    parent = find_parent(root, author_list)
    
    # Insert the ArticleIdList node after the AuthorList node
    if parent is not None and author_list is not None:
        # Get the index of the AuthorList and insert the ArticleIdList after it
        index = list(parent).index(author_list)
        parent.insert(index + 1, article_id_list)
    
    # Convert the modified XML tree back into a string
    return ET.tostring(root, encoding='unicode')


# In[18]:


def add_publication_type(xml_string):
    # Parse the input XML string
    root = ET.fromstring(xml_string)
    
    # Find the AuthorList node
    author_list = root.find(".//AuthorList")
    
    # Find the ArticleIdList node
    article_id_list = root.find(".//ArticleIdList")
    
    # Create a new PublicationType element
    publication_type = ET.Element("PublicationType")
    publication_type.text = "Journal Article"
    
    # We need to manually find the parent of the ArticleIdList node
    def find_parent(root, child):
        # Traverse through all elements
        for parent in root.iter():
            # Look for child within this parent
            if child in list(parent):
                return parent
        return None
    
    parent = find_parent(root, article_id_list)
    
    # Insert the PublicationType node after the AuthorList and before ArticleIdList
    if parent is not None and author_list is not None and article_id_list is not None:
        # Get the index of the ArticleIdList and insert the PublicationType before it
        index = list(parent).index(article_id_list)
        parent.insert(index, publication_type)
    
    # Convert the modified XML tree back into a string
    return ET.tostring(root, encoding='unicode')


# In[3]:


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


# In[17]:


def replace_language_tag(xml_string):
    # Parse the XML string
    root = ET.fromstring(xml_string)

    # Find all 'Language' elements and replace 'dut' with 'NL'
    for language in root.findall('.//Language'):
        if language.text == 'dut':
            language.text = 'NL'

    # Convert the XML tree back to a string
    return ET.tostring(root, encoding='unicode')


# In[ ]:


def replace_journal_title(xml_string, journal_abbreviation):
    # Parse the XML string
    root = ET.fromstring(xml_string)

    # Find the JournalTitle element and set its text to journal_abbreviation
    journal_title = root.find('.//JournalTitle')
    if journal_title is not None:
        journal_title.text = journal_abbreviation

    # Convert the XML tree back to a string
    return ET.tostring(root, encoding='unicode')


# In[4]:


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


# In[5]:


def retrieve_english_title(journaltitle, vernacular_title, api_key):
    response = requests.get("https://platform.openjournals.nl/"+journaltitle+"/api/v1/submissions/?apiToken="+api_key+"&status=3&count=100&searchPhrase="+vernacular_title)
    
    response_data = response.json()

    # Assuming 'response_data' is your JSON data
    for item in response_data['items']:  # Iterate over each item in 'items'
        for publication in item['publications']:  # Iterate over each publication in 'publications'
            title = publication.get('title')  # Get 'fullTitle'
            if vernacular_title == title['nl']:  # Test if 'fullTitle' exists
                output = title['en']

        
    return output


# In[6]:


def rewrite_xml(xml_string, journaltitle, api_key):
    # Get the vernacular title from the XML
    vernacular_title = get_vernacular_title(xml_string)
    
    # Retrieve the English title based on the vernacular title and journal title
    english_title = retrieve_english_title(journaltitle, vernacular_title, api_key)
    print(english_title)
    
    # Add the English article title to the XML
    modified_xml = add_article_title(xml_string, english_title)
    
    #replace the journal title with whatever Pubmed requires
    modified_xml = replace_journal_title(modified_xml, journal_abbreviation)
    
    # Replace the language tag in the modified XML
    modified_xml = replace_language_tag(modified_xml)
    
    #add article id
    modified_xml = add_article_id_list(modified_xml)
    
    #add 'publication type'
    modified_xml = add_publication_type(modified_xml)
    
    # Convert the modified XML back to a string
    output = ET.tostring(ET.fromstring(modified_xml), encoding="unicode")
    
    return output


# In[7]:


def process_all_xml_files(input_folder, output_folder, journaltitle, api_key):
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
    journaltitle = journal_title
    process_all_xml_files('input', 'output', journaltitle, api_key)


# In[38]:


if __name__ == "__main__":
    input_folder = 'input'
    output_folder = 'output'
    main()


# In[ ]:




