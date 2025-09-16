import streamlit as st
import xml.etree.ElementTree as ET
import requests
import json
import pandas as pd
import os
import tempfile
import zipfile
from bs4 import BeautifulSoup
from io import BytesIO

st.set_page_config(
    page_title="OJS to PubMed XML Converter",
    page_icon="📄",
    layout="wide"
)

st.title("📄 OJS-PubMed Metadata-enricher")
st.markdown("Add additional MetaData to PubMed format XML generated in OJS 3.4")

# Sidebar for configuration
st.sidebar.header("⚙️ Configuration")

# API Configuration
with st.sidebar.expander("🔐 API Settings", expanded=True):
    api_key = st.text_input("API Key", type="password", help="Your OJS API key")
    journal_title = st.text_input("Journal Title", help="Full journal title")
    journal_abbreviation = st.text_input("Journal Abbreviation", help="Journal abbreviation for PubMed")

# File upload section
st.header("📁 Upload XML Files")
uploaded_files = st.file_uploader(
    "Choose XML files",
    type=['xml'],
    accept_multiple_files=True,
    help="Upload one or more XML files to convert"
)

# Core functions from the original script
def get_english_abstract(url_published):
    """Fetches and returns the English DC.Description.abstract metadata from an OJS article page."""
    try:
        response = requests.get(url_published)
        if response.status_code != 200:
            st.warning(f"Failed to fetch page. Status code: {response.status_code}")
            return ""

        soup = BeautifulSoup(response.content, "html.parser")
        dc_abstracts = soup.find_all("meta", {"name": "DC.Description"})

        for abstract in dc_abstracts:
            if abstract.get("xml:lang") == "en" and abstract.get("content"):
                return abstract.get("content")

        return ""
    except Exception as e:
        st.error(f"Error fetching abstract: {e}")
        return ""

def get_dc_subjects(url_published):
    """Fetches and returns all DC.Subject metadata from an OJS article page."""
    try:
        response = requests.get(url_published)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.content, "html.parser")
        dc_subjects = soup.find_all("meta", {"name": "DC.Subject"})
        
        return [subject.get("content") for subject in dc_subjects if subject.get("content")]
    except Exception as e:
        st.error(f"Error fetching subjects: {e}")
        return []

def get_vernacular_title(xml_string):
    """Extract vernacular title from XML."""
    try:
        root = ET.fromstring(xml_string)
        vernacular_title_node = root.find('.//VernacularTitle')
        return vernacular_title_node.text if vernacular_title_node is not None else None
    except Exception as e:
        st.error(f"Error extracting vernacular title: {e}")
        return None

def retrieve_json_info(journaltitle, vernacular_title, api_key):
    """Retrieve article information from OJS API."""
    try:
        url = f"https://platform.openjournals.nl/{journaltitle}/api/v1/submissions/"
        params = {
            'apiToken': api_key,
            'status': 3,
            'count': 100,
            'searchPhrase': vernacular_title
        }
        
        response = requests.get(url, params=params)
        response_data = response.json()

        for item in response_data['items']:
            for publication in item['publications']:
                title = publication.get('title', {})
                if vernacular_title == title.get('nl'):
                    fullTitle = publication.get('fullTitle', {})
                    return (
                        fullTitle.get('en'),
                        fullTitle.get('nl'),
                        item.get('urlPublished'),
                        item.get('id')
                    )
        
        return None, None, None, None
    except Exception as e:
        st.error(f"Error retrieving article info: {e}")
        return None, None, None, None

def add_article_title(xml_string, title):
    """Add article title to XML."""
    try:
        root = ET.fromstring(xml_string)
        for article_node in root.findall('.//Article'):
            vernacular_title_node = article_node.find('VernacularTitle')
            if vernacular_title_node is not None:
                article_title_node = ET.Element('ArticleTitle')
                article_title_node.text = title
                child_nodes = list(article_node)
                vernacular_title_position = child_nodes.index(vernacular_title_node)
                article_node.insert(vernacular_title_position + 1, article_title_node)
        return ET.tostring(root, encoding='unicode')
    except Exception as e:
        st.error(f"Error adding article title: {e}")
        return xml_string

def replace_vernacular_title(xml_string, title):
    """Replace vernacular title in XML."""
    try:
        root = ET.fromstring(xml_string)
        for article_node in root.findall('.//Article'):
            vernacular_title_node = article_node.find('VernacularTitle')
            if vernacular_title_node is not None:
                vernacular_title_node.text = title
        return ET.tostring(root, encoding='unicode')
    except Exception as e:
        st.error(f"Error replacing vernacular title: {e}")
        return xml_string

def replace_journal_title(xml_string, journal_abbreviation):
    """Replace journal title with abbreviation."""
    try:
        root = ET.fromstring(xml_string)
        journal_title = root.find('.//JournalTitle')
        if journal_title is not None:
            journal_title.text = journal_abbreviation
        return ET.tostring(root, encoding='unicode')
    except Exception as e:
        st.error(f"Error replacing journal title: {e}")
        return xml_string

def replace_language_tag(xml_string):
    """Replace 'dut' language tag with 'NL'."""
    try:
        root = ET.fromstring(xml_string)
        for language in root.findall('.//Language'):
            if language.text == 'dut':
                language.text = 'NL'
        return ET.tostring(root, encoding='unicode')
    except Exception as e:
        st.error(f"Error replacing language tag: {e}")
        return xml_string

def add_article_id_list(xml_string):
    """Add article ID list with DOI."""
    try:
        root = ET.fromstring(xml_string)
        author_list = root.find(".//AuthorList")
        doi_node = root.find(".//ELocationID[@EIdType='doi']")
        doi_value = doi_node.text if doi_node is not None else None
        
        if doi_value and author_list is not None:
            article_id_list = ET.Element("ArticleIdList")
            article_id = ET.Element("ArticleId", IdType="doi")
            article_id.text = doi_value
            article_id_list.append(article_id)
            
            # Find parent and insert after AuthorList
            for parent in root.iter():
                if author_list in list(parent):
                    index = list(parent).index(author_list)
                    parent.insert(index + 1, article_id_list)
                    break
        
        return ET.tostring(root, encoding='unicode')
    except Exception as e:
        st.error(f"Error adding article ID list: {e}")
        return xml_string

def add_publication_type(xml_string):
    """Add publication type."""
    try:
        root = ET.fromstring(xml_string)
        article_id_list = root.find(".//ArticleIdList")
        
        if article_id_list is not None:
            publication_type = ET.Element("PublicationType")
            publication_type.text = "Journal Article"
            
            for parent in root.iter():
                if article_id_list in list(parent):
                    index = list(parent).index(article_id_list)
                    parent.insert(index, publication_type)
                    break
        
        return ET.tostring(root, encoding='unicode')
    except Exception as e:
        st.error(f"Error adding publication type: {e}")
        return xml_string

def insert_keywords_after_abstract(xml_content, keywords):
    """Insert keywords as ObjectList after Abstract."""
    try:
        root = ET.fromstring(xml_content)
        abstract_node = root.find('.//Abstract')
        
        if abstract_node is None or not keywords:
            return xml_content

        object_list = ET.Element('ObjectList')
        for keyword in keywords:
            object_element = ET.Element('Object', Type='keyword')
            param_element = ET.Element('Param', Name='value')
            param_element.text = keyword
            object_element.append(param_element)
            object_list.append(object_element)

        for parent in root.iter():
            if abstract_node in list(parent):
                abstract_index = list(parent).index(abstract_node)
                parent.insert(abstract_index + 1, object_list)
                break

        return ET.tostring(root, encoding='unicode')
    except Exception as e:
        st.error(f"Error inserting keywords: {e}")
        return xml_content

def refurbish_abstracts(modified_xml, abstract_en):
    """Replace abstracts and add OtherAbstract for Dutch."""
    try:
        root = ET.fromstring(modified_xml)
        dutch_abstract_node = root.find(".//Abstract")
        
        if dutch_abstract_node is None:
            return modified_xml

        dutch_abstract = dutch_abstract_node.text
        dutch_abstract_node.text = abstract_en

        article_node = root.find(".//Article")
        if article_node is not None:
            other_abstract_node = ET.Element("OtherAbstract", attrib={"Language": "NL"})
            other_abstract_node.text = dutch_abstract
            article_node.append(other_abstract_node)

        return ET.tostring(root, encoding='unicode')
    except Exception as e:
        st.error(f"Error refurbishing abstracts: {e}")
        return modified_xml

def reorganize_article_xml(xml_content):
    """Reorganize XML elements in correct order."""
    element_order = [
        'Journal', 'Replaces', 'ArticleTitle', 'VernacularTitle', 'FirstPage', 
        'LastPage', 'ELocationID', 'Language', 'AuthorList', 'GroupList', 
        'PublicationType', 'ArticleIdList', 'History', 'Abstract', 
        'OtherAbstract', 'CopyrightInformation', 'CoiStatement', 'ObjectList', 
        'ReferenceList', 'ArchiveCopySource'
    ]

    try:
        root = ET.fromstring(xml_content)
        for article in root.findall('Article'):
            ordered_elements = []
            for elem_name in element_order:
                element = article.find(elem_name)
                if element is not None:
                    ordered_elements.append(element)
            
            article.clear()
            for elem in ordered_elements:
                article.append(elem)

        return ET.tostring(root, encoding='unicode')
    except Exception as e:
        st.error(f"Error reorganizing XML: {e}")
        return xml_content

def rewrite_xml(xml_string, journal_abbreviation, api_key):
    """Main function to rewrite XML."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("Extracting vernacular title...")
        progress_bar.progress(10)
        vernacular_title = get_vernacular_title(xml_string)
        
        if not vernacular_title:
            st.error("Could not extract vernacular title from XML")
            return None
        
        status_text.text("Retrieving article information from API...")
        progress_bar.progress(20)
        english_title, dutch_title, url_published, pub_id = retrieve_json_info(
            journal_abbreviation, vernacular_title, api_key
        )
        
        if not english_title or not url_published:
            st.error(f"Could not find English title for: {vernacular_title}")
            return None
        
        status_text.text("Fetching English abstract...")
        progress_bar.progress(30)
        abstract_en = get_english_abstract(url_published)
        
        status_text.text("Processing XML transformations...")
        progress_bar.progress(40)
        modified_xml = add_article_title(xml_string, english_title)
        progress_bar.progress(45)
        modified_xml = replace_vernacular_title(modified_xml, dutch_title)
        progress_bar.progress(50)
        modified_xml = replace_journal_title(modified_xml, journal_abbreviation)
        progress_bar.progress(55)
        modified_xml = replace_language_tag(modified_xml)
        progress_bar.progress(60)
        modified_xml = add_article_id_list(modified_xml)
        progress_bar.progress(65)
        modified_xml = add_publication_type(modified_xml)
        
        status_text.text("Fetching keywords...")
        progress_bar.progress(70)
        keywords = get_dc_subjects(url_published)
        modified_xml = insert_keywords_after_abstract(modified_xml, keywords)
        progress_bar.progress(80)
        modified_xml = refurbish_abstracts(modified_xml, abstract_en)
        progress_bar.progress(90)
        modified_xml = reorganize_article_xml(modified_xml)
        
        status_text.text("Finalizing...")
        progress_bar.progress(100)
        
        status_text.text("✅ Processing complete!")
        return modified_xml
        
    except Exception as e:
        st.error(f"Error processing XML: {e}")
        return None

def prettify_xml(xml_string):
    """Prettify XML for readability."""
    try:
        soup = BeautifulSoup(xml_string, 'xml')
        return soup.prettify()
    except Exception as e:
        st.error(f"Error prettifying XML: {e}")
        return xml_string

# Main processing section
if uploaded_files and api_key and journal_abbreviation:
    st.header("🔄 Processing Files")
    
    if st.button("🚀 Start Conversion", type="primary"):
        # Create root element for combined XML
        root = ET.Element('ArticleSet')
        processed_files = []
        
        for uploaded_file in uploaded_files:
            st.subheader(f"Processing: {uploaded_file.name}")
            
            # Read XML content
            xml_content = uploaded_file.getvalue().decode('utf-8')
            
            # Process the XML
            modified_xml = rewrite_xml(xml_content, journal_abbreviation, api_key)
            
            if modified_xml:
                try:
                    # Parse and add to combined XML
                    article_set = ET.fromstring(modified_xml)
                    for article in article_set.findall('Article'):
                        root.append(article)
                    processed_files.append(uploaded_file.name)
                    st.success(f"✅ Successfully processed {uploaded_file.name}")
                except ET.ParseError as e:
                    st.error(f"❌ Error parsing {uploaded_file.name}: {e}")
            else:
                st.error(f"❌ Failed to process {uploaded_file.name}")
        
        if processed_files:
            # Create final XML with DOCTYPE
            combined_xml = ET.tostring(root, encoding='unicode')
            combined_xml_with_doctype = (
                '<!DOCTYPE ArticleSet PUBLIC "-//NLM//DTD PubMed 2.8//EN" '
                '"https://dtd.nlm.nih.gov/ncbi/pubmed/in/PubMed.dtd">\n'
                + combined_xml
            )
            
            # Prettify
            final_xml = prettify_xml(combined_xml_with_doctype)
            
            # Display results
            st.header("📊 Results")
            st.success(f"Successfully processed {len(processed_files)} files")
            
            # Download button
            st.download_button(
                label="📥 Download ArticleSet.xml",
                data=final_xml,
                file_name="articleset.xml",
                mime="application/xml"
            )
            
            # Show preview
            with st.expander("👀 Preview Generated XML"):
                st.code(final_xml[:2000] + "..." if len(final_xml) > 2000 else final_xml, language="xml")

elif uploaded_files:
    st.warning("⚠️ Please provide API Key and Journal Abbreviation in the sidebar to proceed.")
elif not uploaded_files:
    st.info("ℹ️ Please upload XML files to get started.")

# Help section
with st.sidebar.expander("❓ Help & Instructions"):
    st.markdown("""
    **How to use:**
    1. Enter your OJS API credentials (generated under 'profile' -> 'API key' in OJS)
    2. Upload the individual articles as XML, generated by the Pubmed Export Plugin in OJS 3.4
    3. Click 'Start Conversion'
    4. Download the converted ArticleSet.xml
    
    **Requirements:**
    - Valid OJS API key
    - Journal abbreviation
    - XML files from OJS
    
    **Output:**
    - PubMed-formatted XML with DOCTYPE
    - Combined ArticleSet with all articles
    """)

# Footer
st.markdown("---")
st.markdown("*OJS-PubMed XML Enricher - Built by [OpenJournals.nl](www.openjournals.nl) by [KayWP](https://github.com/KayWP)")